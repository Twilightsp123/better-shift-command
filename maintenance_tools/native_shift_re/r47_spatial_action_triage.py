#!/usr/bin/env python3
"""BSC R47: offline-only spatial/action contrast of sequential native member reads.

It does NOT access game memory, run third-party DLL, claim atomicity, or prove a
cause.  No numeric source-field address or action pointer is serialized.
"""
from __future__ import annotations
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

SCHEMA = 'bsc.n1.passive_member_snapshot.v1'
REPORT_SCHEMA = 'bsc.n1.spatial_action_triage.v1'
MAX_RECORDS = 64
MAX_ROWS = 64


def finite_vector(v, dims, field):
    if not isinstance(v, (list, tuple)) or len(v) != dims:
        raise ValueError('INVALID_' + field)
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in v):
        raise ValueError('NONFINITE_' + field)
    return tuple(float(x) for x in v)


def validate_record(o):
    if not isinstance(o, dict) or o.get('schema') != SCHEMA:
        raise ValueError('INVALID_SCHEMA')
    if o.get('sample_type') != 'sequential-not-atomic':
        raise ValueError('MISSING_NONATOMIC_MARK')
    if o.get('inventory_stable') is not True:
        raise ValueError('UNSTABLE_MEMBER_INVENTORY')
    if o.get('build') != '6acec6f4':
        raise ValueError('BUILD_MISMATCH')
    if not isinstance(o.get('unit_token'), str) or not 0 < len(o['unit_token']) <= 80:
        raise ValueError('MISSING_UNIT_TOKEN')
    if type(o.get('time_ms')) not in (int, float) or not math.isfinite(o['time_ms']):
        raise ValueError('INVALID_TIME')
    if not isinstance(o.get('rows'), list) or len(o['rows']) > MAX_ROWS:
        raise ValueError('INVALID_ROW_COUNT')
    if type(o.get('sample_id')) is not int or o['sample_id'] < 0:
        raise ValueError('INVALID_SAMPLE_ID')
    if not isinstance(o.get('member_count'), int) or not 0 < o['member_count'] <= 500:
        raise ValueError('INVALID_MEMBER_COUNT')
    seen = set()
    for row in o['rows']:
        if not isinstance(row, dict):
            raise ValueError('INVALID_ROW')
        ident = row.get('member_id')
        if not isinstance(ident, str) or not ident or len(ident) > 80:
            raise ValueError('INVALID_MEMBER_ID')
        if ident in seen:
            raise ValueError('DUPLICATE_MEMBER_ID')
        seen.add(ident)
        if type(row.get('member_index')) is not int or not 1 <= row['member_index'] <= o['member_count']:
            raise ValueError('INVALID_MEMBER_INDEX')
        finite_vector(row.get('position_xyz'), 3, 'POSITION')
        if row.get('stored_goal_xz') is not None:
            finite_vector(row['stored_goal_xz'], 2, 'GOAL')
        if type(row.get('goal_has_reference')) is not bool:
            raise ValueError('MISSING_GOAL_REFERENCE_STATE')
        if not isinstance(row.get('action'), str) or len(row['action']) > 80:
            raise ValueError('INVALID_ACTION')
        if 'pending_delta_xyz' in row and row['pending_delta_xyz'] is not None:
            finite_vector(row['pending_delta_xyz'], 3, 'DELTA')
        # Absolutely no runtime pointer addresses in output: these are user
        # controlled IDs, not pointers. A plain 0x... pointer is prohibited.
        if ident.lower().startswith('0x') or o['unit_token'].lower().startswith('0x'):
            raise ValueError('RAW_POINTER_IDENTIFIER_FORBIDDEN')
    return o


def xz(row):
    p = row['position_xyz']
    return (p[0], p[2])


def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def distance_during_linear_interval(a0, a1, b0, b1):
    """A geometric approximation, NOT continuous or simultaneous game evidence."""
    rx, rz = a0[0]-b0[0], a0[1]-b0[1]
    vx, vz = (a1[0]-a0[0])-(b1[0]-b0[0]), (a1[1]-a0[1])-(b1[1]-b0[1])
    den = vx*vx+vz*vz
    frac = max(0.0, min(1.0, -(rx*vx+rz*vz)/den)) if den > 1e-12 else 0.0
    return round(math.hypot(rx+frac*vx, rz+frac*vz),6), round(frac,6)



def best_rigid_fit(first, second):
    """Closed-form 2D rigid alignment; shape diagnostic, not a physical model.

    Inputs are corresponding X/Z positions from two sequential, non-atomic
    samples. A rigid unit translation or yaw rotation has near-zero residual.
    """
    if len(first) != len(second) or len(first) < 3:
        return None
    n=len(first)
    for p in first+second:
        finite_vector(p,2,'RIGID_FIT')
    c0=(sum(x for x,z in first)/n,sum(z for x,z in first)/n)
    c1=(sum(x for x,z in second)/n,sum(z for x,z in second)/n)
    dot=cross=0.0
    for p,q in zip(first,second):
        x,z=p[0]-c0[0],p[1]-c0[1]
        xx,zz=q[0]-c1[0],q[1]-c1[1]
        dot+=x*xx+z*zz
        cross+=x*zz-z*xx
    angle=math.atan2(cross,dot)
    c,s=math.cos(angle),math.sin(angle)
    rms=math.sqrt(sum((c*(p[0]-c0[0])-s*(p[1]-c0[1])+c1[0]-q[0])**2 +
                      (s*(p[0]-c0[0])+c*(p[1]-c0[1])+c1[1]-q[1])**2
                      for p,q in zip(first,second))/n)
    return {'member_count':n,'best_rigid_yaw_degrees':round(math.degrees(angle),4),
            'centroid_shift_m_estimate':round(dist(c0,c1),5),
            'rms_nonrigid_residual_m':round(rms,6),
            'caution':'Sequential samples; shape residual not a deformation cause or gameplay bug proof'}


def analyze(records, *, candidate_radius=3.5, compress_ratio=0.5,
            endpoint_radius=0.8):
    if not records or len(records) > MAX_RECORDS:
        raise ValueError('INVALID_SAMPLE_COUNT')
    for r in records:
        validate_record(r)
    groups = defaultdict(list)
    for r in records:
        groups[(r['unit_token'],r['build'])].append(r)
    findings=[];fits=[];pairs_considered=0;intervals=0;skipped=[]
    for (unit,build), seq in groups.items():
        seq.sort(key=lambda x:x['time_ms'])
        for l,r in zip(seq,seq[1:]):
            if l['time_ms'] >= r['time_ms'] or l['sample_id'] >= r['sample_id']:
                skipped.append('NONMONOTONIC_SAMPLES');continue
            if l['member_count'] != r['member_count']:
                skipped.append('MEMBER_COUNT_CHANGED');continue
            a={x['member_id']:x for x in l['rows']}
            b={x['member_id']:x for x in r['rows']}
            keys=[k for k in a if k in b and a[k]['member_index']==b[k]['member_index']]
            intervals+=1
            dt=(r['time_ms']-l['time_ms'])/1000.0
            if len(keys)>=3:
                rigid=best_rigid_fit([xz(a[k]) for k in keys], [xz(b[k]) for k in keys])
                if rigid is not None:
                    rigid.update({'unit_token':unit,'start_sample':l['sample_id'],
                                  'end_sample':r['sample_id']})
                    fits.append(rigid)
            for i,k in enumerate(keys):
                for h in keys[i+1:]:
                    aa,ab=a[k],a[h];ba,bb=b[k],b[h]
                    p0,q0=xz(aa),xz(ab)
                    d0=dist(p0,q0)
                    if d0 < 1e-6 or d0 > candidate_radius:continue
                    pairs_considered+=1
                    p1,q1=xz(ba),xz(bb)
                    d1=dist(p1,q1)
                    closure=1-d1/d0
                    local_min,tstar=distance_during_linear_interval(p0,p1,q0,q1)
                    # Skip routine pairs; positive closure alone is not evidence
                    # of a collision and does not imply a game engine error.
                    if closure < compress_ratio and d1 > endpoint_radius:continue
                    goal_analysis='not_comparable'
                    goal_end_distance=None
                    if all(x['goal_has_reference'] is False and x.get('stored_goal_xz') is not None
                           for x in (aa,ab)):
                        gp=finite_vector(aa['stored_goal_xz'],2,'GOAL')
                        gq=finite_vector(ab['stored_goal_xz'],2,'GOAL')
                        goal_end_distance=round(dist(gp,gq),5)
                        goal_analysis='stored_goal_not_verified_as_active_motor_target'
                    actions_same_at_begin=aa['action']==ab['action']
                    actions_same_at_end=ba['action']==bb['action']
                    event = {
                        'unit_token':unit,'start_sample':l['sample_id'],
                        'end_sample':r['sample_id'],'dt_seconds':round(dt,4),
                        'members':[k,h],
                        'baseline_distance':round(d0,5),
                        'end_distance':round(d1,5),
                        'distance_compression_fraction':round(closure,5),
                        'min_interpolated_distance_estimate':local_min,
                        'interpolated_fraction':tstar,
                        'actions_at_start':[aa['action'],ab['action']],
                        'actions_at_end':[ba['action'],bb['action']],
                        'same_action_at_start':actions_same_at_begin,
                        'same_action_at_end':actions_same_at_end,
                        'stored_goal_pair_distance':goal_end_distance,
                        'stored_goal_status':goal_analysis,
                        'interpretation':'spatial_proximity_only; not a collision, first_error, or root_cause proof'
                    }
                    findings.append(event)
    findings.sort(key=lambda x:(x['end_distance'], -x['distance_compression_fraction']))
    return {'schema':REPORT_SCHEMA,'records_checked':len(records),
            'adjacent_intervals_compared':intervals,'candidate_pairs_compared':pairs_considered,
            'proximity_events':findings[:100], 'rigid_motion_contrasts':fits[:100],
            'truncated':len(findings)>100 or len(fits)>100,
            'skipped_intervals':sorted(set(skipped)),
            'limitations':[
                'Snapshots are sequential and not atomic even after inventory double-check',
                'Interpolated minimum is geometric only, assumes synchronized same-time movement',
                'Member array index is not spatial adjacency; pairs selected by observed 2D distance',
                'A matching pointer across reads does not prove no object-pool ABA reuse',
                'Stored goals may not be current active motor targets even without frame reference',
                'Proximity and action disagreement do not establish the first error or gameplay causation',
                'Rigid-fit residual is a nonrigid-shape indicator, not a diagnosis of abnormality',
            ],'first_error_proven':False,'root_cause_proven':False,
            'gameplay_patch_authorized':False}


def run(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--candidate-radius',type=float,default=3.5)
    ap.add_argument('--compress-ratio',type=float,default=0.5)
    ap.add_argument('--endpoint-radius',type=float,default=0.8)
    args=ap.parse_args(argv)
    if args.input.resolve()==args.output.resolve():ap.error('refusing to overwrite input')
    if args.input.stat().st_size>200000:ap.error('input too large')
    rows=[json.loads(s) for s in args.input.read_text('utf-8').splitlines() if s.strip()]
    report=analyze(rows,candidate_radius=args.candidate_radius,
                   compress_ratio=args.compress_ratio,endpoint_radius=args.endpoint_radius)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(f"OFFLINE_ONLY {report['adjacent_intervals_compared']} intervals, {len(report['proximity_events'])} proximity candidates; NO PATCH")

if __name__=='__main__':run()
