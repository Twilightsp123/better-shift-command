#!/usr/bin/env python3
"""Analyze original user motor goals and member positions around a native turn.

The results prove motion/goal behavior in the logged group but NEVER attribute
that observed turn to RMB or Shift without a real native order identity.
"""
import argparse
from collections import defaultdict, Counter
import json
import math
from pathlib import Path
import statistics
import struct


def xyz_from_hex(value):
    if not isinstance(value,str):return None
    try:
        b=bytes.fromhex(value)
        if len(b)<12:return None
        xyz=struct.unpack_from('<fff',b,0)
        return xyz if all(math.isfinite(x) for x in xyz) else None
    except ValueError:return None


def vec(start, dest):
    return dest[0]-start[0],dest[2]-start[1]


def dot(a,b):return a[0]*b[0]+a[1]*b[1]


def norm(a):return math.hypot(*a)


def unit(a):
    n=norm(a)
    return (a[0]/n,a[1]/n) if n else (0.,0.)


def get_turns(rows):
    """Return signed old/new lookahead turn events from original PRE records."""
    changes=[]
    for r in rows:
        if r.get('ev')!='GOAL_COMMIT_PRE':continue
        old,new=xyz_from_hex(r.get('before24')),xyz_from_hex(r.get('proposed24'))
        x,z=r.get('x'),r.get('z')
        if not old or not new or not isinstance(x,(float,int)) or not isinstance(z,(float,int)):
            continue
        origin=(x,z);a=vec(origin,old);b=vec(origin,new)
        if norm(a)<2 or norm(b)<2:continue
        cosine=dot(a,b)/norm(a)/norm(b)
        if cosine>=-0.7:continue
        changes.append({'atMs':r['atMs'],'clock':r.get('clock'),
             'member':r['member'],'group':r.get('owner440'),
             'old_target_xz':(old[0],old[2]),'new_target_xz':(new[0],new[2]),
             'member_xz':origin,'heading_cosine':cosine,
             'old_lookahead_distance':norm(a),'new_lookahead_distance':norm(b)})
    return changes


def analyze(rows):
    events=[x for x in rows if x.get('type')=='event']
    receiv=[x for x in events if x.get('ev')=='B_DEFERRED_RECEIVE']
    count=Counter(x['member'] for x in receiv)
    cadence={}
    for member,n in count.items():
        a=sorted((x for x in receiv if x['member']==member),key=lambda x:x['clock'])
        delta=[y['clock']-x['clock'] for x,y in zip(a,a[1:])]
        ahead=[]
        for e in a:
            pos=xyz_from_hex(e.get('packet58'))
            if pos:ahead.append(math.hypot(pos[0]-e['x'],pos[2]-e['z']))
        cadence[member]={
         'receiver_count':n,
         'tick_deltas':delta,
         'all_deltas_11':bool(delta) and all(v==11 for v in delta),
         'lookahead_min':min(ahead) if ahead else None,
         'lookahead_max':max(ahead) if ahead else None,
         'lookahead_median':statistics.median(ahead) if ahead else None,
        }
    turns=get_turns(events)
    byactor=defaultdict(list)
    for e in events:
        if e.get('ev')!='GOAL_COMMIT_POST':continue
        if e.get('member') is None:continue
        if not isinstance(e.get('x'),(int,float)) or not isinstance(e.get('z'),(int,float)):
            continue
        byactor[e['member']].append(e)
    direction_stats=[]
    for t in turns:
        timeline=[e for e in byactor[t['member']] if e['atMs']>=t['atMs']]
        if not timeline:continue
        # Evaluate signed progress along the pre-reversal goal direction.
        old=vec(t['member_xz'],(t['old_target_xz'][0],0,t['old_target_xz'][1]))
        old_dir=(old[0]/norm(old),old[1]/norm(old))
        progress=[(e['clock'],dot((e['x']-t['member_xz'][0],
                                  e['z']-t['member_xz'][1]),old_dir)) for e in timeline]
        last=progress[0]
        peak=max(progress,key=lambda x:x[1])
        changes=[(progress[i-1][0],progress[i][0],progress[i][1]-progress[i-1][1])
                 for i in range(1,len(progress))]
        first_negative=next((x for x in changes if x[2]<-0.02),None)
        direction_stats.append({'member':t['member'],'clock':t['clock'],
          'old_direction_positive_progress_peak_tick':peak[0],
          'old_direction_positive_progress_peak_units':peak[1],
          'first_negative_progress_interval':first_negative,
          'following_goal_post_events':len(progress),
          'caveat':'Goal-writes are not a guaranteed per-frame physical velocity trace.'})
    groups=defaultdict(list)
    for t in turns:
        groups[(t['group'],t['clock'])].append(t)
    simultaneous=[{'group':k[0],'clock':k[1],
                  'members':len(v),'max_time_spread_ms':max(x['atMs'] for x in v)-min(x['atMs'] for x in v)}
                  for k,v in groups.items() if len({x['member'] for x in v})>1]
    return {'schema':'bsc.n1.private_existing_reverse_goal_audit.v1',
      'receiver_count':len(receiv),
      'receiver_member_cadence':cadence,
      'native_lookahead_reversals':turns,
      'same_group_tick_multiple_members_reversed':simultaneous,
      'physical_progress_after_goal_reversal':direction_stats,
      'original_packet_sender_confirmed':False,
      'native_queued_Shift_instance_confirmed':False,
      'crowding_causality_proven':False,
      'reason':'Real goal changes and continuing displacement can coexist under CA normal gradual turning, even without stale goals. No order identity, no full 60-member physics.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    rows=[json.loads(s) for s in args.input.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    result=analyze(rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('REVERSALS_FOUND',len(result['native_lookahead_reversals']))
    print('COHORT_SAME_TICK',result['same_group_tick_multiple_members_reversed'])

if __name__=='__main__':main()
