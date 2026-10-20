#!/usr/bin/env python3
"""Fail-closed wrapper for R49 sequential passive samples feeding R47 geometry.

NO gameplay observation or native patch. Expected file is JSONL from the R49
research-only sampler. The emitter is not assumed to be an atomic engine capture.
"""
from __future__ import annotations
import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
import r47_spatial_action_triage as r47

SCHEMA = 'bsc.n1.r49_spatial_evidence_preflight.v1'
MAX_SAMPLES = 64
MAX_CAPTURE_US = 5000.0
MAX_WITHIN_SAMPLE_SKEW_US = 2500.0
MAX_GAP_MS = 250.0
MEMBER_ID = re.compile(r'^m[1-9][0-9]*_[1-9][0-9]*$')


def measured(v):
    return type(v) in (int, float) and math.isfinite(v) and v >= 0


def validate_r49_sample(rec):
    r47.validate_record(rec)
    if rec.get('intra_sample_full_roster_stable') is not True:
        raise ValueError('R49_FULL_ROSTER_GUARD_REQUIRED')
    if rec.get('cross_snapshot_lifetime_proven') is not False:
        raise ValueError('R49_UNPROVEN_LIFETIME_MARK_REQUIRED')
    if rec.get('sample_type') != 'sequential-not-atomic':
        raise ValueError('R49_SEQUENTIAL_ONLY')
    if rec.get('native_patch_authorized') is not False:
        raise ValueError('R49_PATCH_NOT_AUTHORIZED')
    epoch = rec.get('roster_epoch')
    if type(epoch) is not int or not 1 <= epoch <= 10000:
        raise ValueError('INVALID_ROSTER_EPOCH')
    duration = rec.get('read_duration_us')
    if not measured(duration) or duration > MAX_CAPTURE_US:
        raise ValueError('BAD_SAMPLING_DURATION')
    if rec.get('roster_bytes_checked') != rec.get('member_count') * 8:
        raise ValueError('FULL_ROSTER_SIZE_MISMATCH')
    times=[]
    for row in rec['rows']:
        if not MEMBER_ID.fullmatch(row['member_id']):
            raise ValueError('R49_IDENTITIES_MUST_BE_EPOCH_SCOPED')
        if not row['member_id'].startswith('m' + str(epoch) + '_'):
            raise ValueError('R49_ID_EPOCH_MISMATCH')
        t=row.get('read_offset_us')
        if not measured(t) or t>duration:
            raise ValueError('MISSING_OR_INVALID_ROW_TIME')
        times.append(t)
        if row.get('member_type') not in ('ordinary_exact_vtable','unknown_position_only'):
            raise ValueError('INVALID_TYPED_MEMBER_STATUS')
        if row['member_type']=='unknown_position_only':
            if row.get('action') != 'not_typed' or row.get('stored_goal_xz') is not None:
                raise ValueError('UNTYPED_MEMBER_MUST_BE_POSITION_ONLY')
    if times != sorted(times):
        raise ValueError('NONMONOTONIC_WITHIN_SNAPSHOT_ROW_TIMES')
    if not times:
        raise ValueError('EMPTY_MEMBER_SNAPSHOT')
    return max(times)-min(times)


def preflight(samples):
    if not 1 <= len(samples) <= MAX_SAMPLES:
        raise ValueError('INVALID_R49_INPUT_COUNT')
    spans=[validate_r49_sample(s) for s in samples]
    groups=defaultdict(list)
    for rec, span in zip(samples,spans):
        groups[(rec['unit_token'],rec['build'])].append((rec, span))
    sanitized=[]
    accepted=skipped_gap=skipped_span=skipped_epoch=skipped_order=0
    for key, seq in groups.items():
        seq.sort(key=lambda row: (row[0]['time_ms'],row[0]['sample_id']))
        # Accept explicit two-sample intervals only; never let R47 accidentally
        # join disconnected epochs, long gaps, or too-skewed within-row readings.
        for (a,ta),(b,tb) in zip(seq,seq[1:]):
            if a['sample_id']>=b['sample_id'] or a['time_ms']>=b['time_ms']:
                skipped_order+=1;continue
            if a['roster_epoch'] != b['roster_epoch']:
                skipped_epoch+=1;continue
            if b['time_ms']-a['time_ms']>MAX_GAP_MS:
                skipped_gap+=1;continue
            if ta>MAX_WITHIN_SAMPLE_SKEW_US or tb>MAX_WITHIN_SAMPLE_SKEW_US:
                skipped_span+=1;continue
            sanitized.extend([a,b]);accepted+=1
    pairs=[]
    rigid=[]
    # R47 groups by unit/token; don't let it create unapproved adjacency by
    # feeding all allowed intervals into one continuous sequence.
    for i in range(0,len(sanitized),2):
        report=r47.analyze(sanitized[i:i+2])
        for p in report['proximity_events']:
            p['non_atomic_pair_skew_caveat']=True
        pairs.extend(report['proximity_events'])
        rigid.extend(report['rigid_motion_contrasts'])
    return {
        'schema': SCHEMA,
        'input_samples':len(samples), 'compared_intervals':accepted,
        'excluded_due_to_roster_epoch_change':skipped_epoch,
        'excluded_due_to_gap':skipped_gap,
        'excluded_due_to_within_sample_skew':skipped_span,
        'excluded_due_to_monotonicity':skipped_order,
        'candidate_proximity_events':pairs[:100],
        'best_rigid_motion_fits':rigid[:100],
        'truncated':len(pairs)>100 or len(rigid)>100,
        'evidence_grade':'SEQUENTIAL_NEAR_TIME_PASSIVE_SPATIAL_ONLY',
        'not_full_unit_atomic_snapshot':True,
        'same_pointer_same_lifetime_proven':False,
        'physical_overlap_or_abnormality_proven':False,
        'first_error_proven':False,'root_cause_proven':False,'gameplay_patch_authorized':False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.input.resolve()==args.output.resolve():parser.error('refusing to overwrite original samples')
    if args.input.stat().st_size > 500000:parser.error('input size exceeds evidence budget')
    records=[json.loads(x) for x in args.input.read_text('utf8').splitlines() if x.strip()]
    result=preflight(records)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print('OFFLINE_R49_PREFLIGHT_PASS', result['compared_intervals'], 'intervals,',
          len(result['candidate_proximity_events']),'proximity candidates; NO PATCH')

if __name__=='__main__':main()
