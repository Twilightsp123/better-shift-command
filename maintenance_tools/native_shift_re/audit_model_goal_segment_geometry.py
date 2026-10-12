#!/usr/bin/env python3
"""Anonymized actual per-member native goal geometry from BSC one-shot JSONL.

Straight current-position -> new motor goal segments are ONLY lookahead chords.
Crossing them does not prove real CA curved paths cross, collision or Shift cause.
"""
import argparse,collections,itertools,json,math,struct
from pathlib import Path

def decoded_xyz(blob):
    data=bytes.fromhex(blob)
    if len(data)!=24:raise ValueError('GOAL24_INVALID')
    return struct.unpack('<6f',data)[:3]

def segment_intersection(p,q,r,s):
    x,y=q[0]-p[0],q[1]-p[1];u,v=s[0]-r[0],s[1]-r[1]
    denominator=x*v-y*u
    if abs(denominator)<1e-8:return None
    a,b=r[0]-p[0],r[1]-p[1]
    t=(a*v-b*u)/denominator
    h=(a*y-b*x)/denominator
    if not 1e-6<t<1-1e-6 or not 1e-6<h<1-1e-6:return None
    return (t,h)

def audit(rows):
    bytick=collections.defaultdict(list);positions=collections.defaultdict(dict)
    for event in rows:
        if event.get('ev')=='MOTOR_GOAL_REVERSAL':
            try:
                x,z=event['x'],event['z']
                goal=decoded_xyz(event['newGoal24'])
                if all(math.isfinite(v) for v in (x,z,goal[0],goal[2])):
                    bytick[(event.get('group'),event['groupTick'])].append(
                        (event['member'],(x,z),(goal[0],goal[2])))
            except (ValueError,KeyError,TypeError):continue
        elif event.get('ev')=='GROUP_TICK_POSITION':
            k=(event.get('group'),event.get('turnStartTick'),event.get('groupTick'))
            x,z=event.get('x'),event.get('z')
            if (isinstance(x,(int,float)) and isinstance(z,(int,float)) and
                math.isfinite(x) and math.isfinite(z)):
                positions[k][event.get('member')]=(x,z)
    turns=[]
    for (group,tick),members in sorted(bytick.items(),key=lambda kv:kv[0][1]):
        crossings=[]
        for (id_a,pos_a,goal_a),(id_b,pos_b,goal_b) in itertools.combinations(members,2):
            fractions=segment_intersection(pos_a,goal_a,pos_b,goal_b)
            if id_a!=id_b and fractions:
                crossings.append({'member_pair_anonymized':True,
                    'fraction_along_first_lookahead':round(fractions[0],5),
                    'fraction_along_second_lookahead':round(fractions[1],5)})
        turns.append({'tick':tick,'simultaneous_goal_reversals':len(members),
            'lookahead_straight_segment_crossings':len(crossings),
            'crossing_fraction_samples':crossings,
            'real_movement_trajectory_crossing_proven':False})
    centers=[]
    for (group,start,tick),members in positions.items():
        valid=[point for m,point in members.items() if m is not None]
        if len(valid)<2:continue
        distance=min(math.dist(a,b) for a,b in itertools.combinations(valid,2))
        centers.append({'turn_start_tick':start,'tick':tick,
            'sampled_members':len(valid),
            'min_horizontal_center_distance':round(distance,6),
            'collision_proven':False})
    return {'schema':'bsc.n1.anonymous_goal_geometry_lookahead.v1',
        'simultaneous_reversal_ticks':turns,
        'closest_sampled_member_center':min(
            centers,key=lambda v:v['min_horizontal_center_distance']) if centers else None,
        'physical_collision_cause_proven':False,
        'rmb_vs_shift_order_instance_captured':False,
        'warning':'Lookahead chord intersections do NOT establish real CA curved trajectory crossing.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    rows=(json.loads(s) for s in a.input.read_text(encoding='utf-8-sig').splitlines() if s.strip())
    result=audit(rows)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('ANONYMOUS_GEOMETRY',len(result['simultaneous_reversal_ticks']),'turns; collisions NOT proven')
if __name__=='__main__':main()
