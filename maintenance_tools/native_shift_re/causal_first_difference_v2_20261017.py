#!/usr/bin/env python3
"""Conservative offline member comparison: not a native Hook or causal diagnosis.

Same tick != atomic group sample; index adjacent != spatial neighbors.
"""
import argparse,json,math,re
from pathlib import Path
from collections import defaultdict
SCHEMA='bsc.n1.member_observation.v2'
ORDER=('group_epoch','packet_route_epoch','frame_epoch','world_goal_direction','tick_branch','motion_direction')
TOKEN=re.compile(r'^[a-z][a-z0-9_-]{0,35}$')
PHASES={'tick_entry','world_goal_resolved','post_member_tick','post_group_update'}
MAX_RECORDS=2000
MAX_SKEW_NS=200000

def atom(v):
 if type(v)!=str or not TOKEN.fullmatch(v) or re.search(r'0x[0-9a-f]{8,}',v):
  raise ValueError('RAW_OR_UNVERIFIED_ID')
 return v
def vec(v):
 if v is None:return None
 if type(v)!=list or len(v)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1e8 for x in v):
  raise ValueError('INVALID_VECTOR')
 return tuple(float(x) for x in v)
def vint(v,maxval,key):
 if type(v)!=int or v<0 or v>maxval:raise ValueError('BAD_INTEGER_'+key)
 return v
def tick_branch(f,s,bnull):
 if f&8:return 'virtual_498'
 if f&4:return 'inline_action' if s in (4,16) else 'other_state'
 return 'neighbor' if bnull else 'virtual_490'
def validate(x):
 if type(x)!=dict or x.get('schema')!=SCHEMA:raise ValueError('INVALID_SCHEMA')
 r={}
 for k in ('trace_id','unit_epoch','move_epoch','snapshot_id'):r[k]=atom(x.get(k))
 for k in ('group_epoch','packet_route_epoch','frame_epoch'):r[k]=atom(x[k]) if x.get(k) is not None else None
 r['phase']=x.get('phase')
 if r['phase'] not in PHASES:raise ValueError('INVALID_OBSERVATION_PHASE')
 for k,limit in [('tick',10**9),('sample_seq',10**8),('sample_time_ns',10**18),
                 ('member_index',9999),('flags108',255),('state324',65535)]:
  r[k]=vint(x.get(k),limit,k)
 if type(x.get('b20_null'))!=bool:raise ValueError('UNKNOWN_B20_STATUS')
 r['b20_null']=x['b20_null']
 for k in ('position_xyz','world_goal_xyz','velocity_xyz'):r[k]=vec(x.get(k))
 r['tick_branch']=tick_branch(r['flags108'],r['state324'],r['b20_null'])
 return r
def cosine(a,b):
 if a is None or b is None:return None
 aa=math.sqrt(sum(v*v for v in a));bb=math.sqrt(sum(v*v for v in b))
 if min(aa,bb)<1e-6:return None
 return max(-1.,min(1.,sum(v*w for v,w in zip(a,b))/(aa*bb)))
def stage_diffs(a,b):
 diffs=[];unknown=[]
 for k in ORDER[:3]:
  if a[k] is None or b[k] is None:unknown.append(k)
  elif a[k]!=b[k]:diffs.append({'stage':k,'values':[a[k],b[k]]})
 if any(a[k] is None or b[k] is None for k in ('position_xyz','world_goal_xyz')):
  unknown.append('world_goal_direction')
 else:
  aa=tuple(x-y for x,y in zip(a['world_goal_xyz'],a['position_xyz']))
  bb=tuple(x-y for x,y in zip(b['world_goal_xyz'],b['position_xyz']))
  c=cosine(aa,bb)
  if c is None:unknown.append('world_goal_direction')
  elif c<-.5:diffs.append({'stage':'world_goal_direction','cosine':round(c,5)})
 if a['tick_branch']!=b['tick_branch']:
  diffs.append({'stage':'tick_branch','values':[a['tick_branch'],b['tick_branch']]})
 c=cosine(a['velocity_xyz'],b['velocity_xyz'])
 if c is None:unknown.append('motion_direction')
 elif c<-.5:diffs.append({'stage':'motion_direction','cosine':round(c,5)})
 diffs.sort(key=lambda item:ORDER.index(item['stage']))
 first=ORDER.index(diffs[0]['stage']) if diffs else None
 earlier=[k for k in unknown if first is not None and ORDER.index(k)<first]
 return {'candidate_stage_differences':diffs,
  'earliest_ordered_recorded_stage':diffs[0]['stage'] if diffs else None,
  'earliest_stage_is_unambiguous':bool(diffs) and not earlier,
  'unobserved_stages':unknown,'earlier_unobserved_stages':earlier,
  'stage_order_is_causal_or_temporal_proof':False,'root_cause_proven':False}
def pair(a,b):
 r={'member_indices':[a['member_index'],b['member_index']],
  'index_adjacency_is_spatial_adjacency_proof':False,
  'actual_atomic_snapshot_proven':False,'root_cause_proven':False}
 if a['phase']!=b['phase']:
  r['status']='NOT_COMPARABLE_PHASE_MISMATCH';return r
 if a['sample_seq']==b['sample_seq']:
  r['status']='NOT_COMPARABLE_DUPLICATE_SAMPLE_SEQUENCE';return r
 skew=abs(a['sample_time_ns']-b['sample_time_ns'])
 r['time_skew_ns']=skew
 if skew>MAX_SKEW_NS:
  r['status']='NOT_COMPARABLE_SEQUENTIAL_SKEW';return r
 r['status']='NEAR_IN_TIME_CANDIDATES_ONLY_NOT_ATOMIC'
 r.update(stage_diffs(a,b))
 return r
def analyze(lines):
 cohorts=defaultdict(dict);count=0
 for raw in lines:
  if not raw.strip():continue
  count+=1
  if count>MAX_RECORDS:raise ValueError('BOUNDED_TRACE_EXCEEDED')
  x=validate(json.loads(raw))
  key=tuple(x[k] for k in ('trace_id','unit_epoch','move_epoch','snapshot_id','tick'))
  if x['member_index'] in cohorts[key]:raise ValueError('DUPLICATE_MEMBER_SAMPLE')
  cohorts[key][x['member_index']]=x
 pairs=[]
 for key,records in sorted(cohorts.items()):
  for i,a in sorted(records.items()):
   if i+1 in records:
    r=pair(a,records[i+1])
    r.update({'trace_id':key[0],'snapshot_id':key[3],'tick':key[4]})
    pairs.append(r)
 return dict(schema='bsc.n1.first_difference_v2.v1',input_records=count,
  index_adjacent_candidate_pairs=len(pairs),pairs=pairs,
  status='CANDIDATE_ONLY_UNVERIFIED_EXTERNAL_PROVENANCE' if pairs else 'NO_MATCHED_INDEX_ADJACENT_PAIR',
  cannot_verify_collector_lineage=True,cannot_verify_engine_atomicity=True,
  cannot_prove_spatial_neighbourhood=True,root_cause_proven=False,patch_authorized=False)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--jsonl',type=Path,required=True);p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.jsonl.resolve()==a.out.resolve():p.error('INPUT_OVERWRITE_FORBIDDEN')
 with a.jsonl.open(encoding='utf8') as f:r=analyze(f)
 s=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(s,'utf8')
 print(s)
if __name__=='__main__':main()
