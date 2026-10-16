#!/usr/bin/env python3
"""Offline, read-only and conservative BSC member-pair first-difference analysis.

Requires ALREADY-COLLECTED, instance-correlated, sanitized JSONL. This script
does not access the game, and its output NEVER proves gameplay causality.
"""
import argparse,json,math,re
from collections import defaultdict
from pathlib import Path
SCHEMA='bsc.n1.member_snapshot.v1'
TOKEN=re.compile(r'^[A-Za-z][A-Za-z0-9_:-]{0,47}$')
ORDER=('group_epoch','packet_route_epoch','frame_epoch','world_target_direction',
       'tick_dispatch','motion_direction')
MAX_LINES=10000

def xyz(a):
 if not isinstance(a,list) or len(a)!=3 or any(
   type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1e8 for x in a):
  raise ValueError('INVALID_XYZ')
 return tuple(float(x) for x in a)

def epoch(a):
 if not isinstance(a,str) or not TOKEN.fullmatch(a) or re.search(r'0[xX][0-9a-fA-F]{8,}',a):
  raise ValueError('INVALID_EPOCH_OR_RAW_ADDRESS')
 return a

def tick_branch(flags,state,b20_null):
 if flags&8:return 'other_virtual_0x498'
 if flags&4:return 'inline_action' if state in (4,16) else 'other_state'
 return 'neighbor' if b20_null else 'other_virtual_0x490'

def validate(rec):
 if not isinstance(rec,dict) or rec.get('schema')!=SCHEMA:raise ValueError('SCHEMA_MISMATCH')
 out={}
 for key in ('trace_id','unit_epoch','move_epoch','group_epoch','packet_route_epoch','frame_epoch'):
  out[key]=epoch(rec[key]) if rec.get(key) is not None else None
 for key in ('tick','member_index','flags108','state324'):
  v=rec.get(key)
  ceiling={'tick':1000000,'member_index':999,'flags108':255,'state324':65535}[key]
  if type(v)!=int or v<0 or v>ceiling:raise ValueError('BAD_INTEGER_FIELD:'+key)
  out[key]=v
 if type(rec.get('b20_null'))!=bool:raise ValueError('MISSING_MEMBER_B20_GATE')
 out['b20_null']=rec['b20_null']
 for key in ('member_position','world_target','output_velocity'):
  out[key]=xyz(rec[key]) if rec.get(key) is not None else None
 out['tick_branch']=tick_branch(out['flags108'],out['state324'],out['b20_null'])
 return out

def dircos(a,b):
 if a is None or b is None:return None
 x=math.sqrt(sum(v*v for v in a));y=math.sqrt(sum(v*v for v in b))
 if x<1e-4 or y<1e-4:return None
 return sum(v*w for v,w in zip(a,b))/(x*y)

def direction(goal,pos):
 return tuple(x-y for x,y in zip(goal,pos)) if goal is not None and pos is not None else None

def compare(a,b):
 found=[];missing=[]
 for key in ('group_epoch','packet_route_epoch','frame_epoch'):
  if a[key] is None or b[key] is None:missing.append(key)
  elif a[key]!=b[key]:found.append({'stage':key,'values':[a[key],b[key]]})
 c=dircos(direction(a['world_target'],a['member_position']),
          direction(b['world_target'],b['member_position']))
 if c is None:missing.append('world_target_direction')
 elif c<-.5:found.append({'stage':'world_target_direction','cosine':round(c,5)})
 if a['tick_branch']!=b['tick_branch']:
  found.append({'stage':'tick_dispatch','values':[a['tick_branch'],b['tick_branch']]})
 c=dircos(a['output_velocity'],b['output_velocity'])
 if c is None:missing.append('motion_direction')
 elif c<-.5:found.append({'stage':'motion_direction','cosine':round(c,5)})
 found.sort(key=lambda x:ORDER.index(x['stage']))
 return {'members':[a['member_index'],b['member_index']],
  'observed_differences':found,
  'earliest_recorded_difference':found[0]['stage'] if found else None,
  'not_observed_stages':missing,
  'root_cause_proven':False,
  'note':'Per-member formation and motion differences may be valid; this is not a bug diagnosis.'}

def analyze(lines):
 cohorts=defaultdict(dict);count=0
 for raw in lines:
  if not raw.strip():continue
  count+=1
  if count>MAX_LINES:raise ValueError('TRACE_BUDGET_EXCEEDED')
  obj=validate(json.loads(raw))
  key=tuple(obj[k] for k in ('trace_id','unit_epoch','move_epoch','tick'))
  if any(x is None for x in key):raise ValueError('MISSING_INSTANCE_EPOCH')
  index=obj['member_index']
  if index in cohorts[key]:raise ValueError('DUPLICATE_MEMBER_TICK')
  cohorts[key][index]=obj
 pairs=[]
 for key,entries in sorted(cohorts.items()):
  for index in sorted(entries):
   if index+1 in entries:
    result=compare(entries[index],entries[index+1])
    result.update({'trace_id':key[0],'unit_epoch':key[1],
      'move_epoch':key[2],'tick':key[3]})
    pairs.append(result)
 return {'schema':'bsc.n1.offline_first_difference.v1',
  'source_event_schema':SCHEMA,'input_records':count,
  'cohorts':len(cohorts),'paired_adjacent_members':len(pairs),
  'pairs':pairs,'status':'CANDIDATE_DIFFERENCES_ONLY' if pairs else
    'INSUFFICIENT_ADJACENT_SAME_TICK_EVIDENCE',
  'actual_SHIFT_instance_correlated_by_script':False,
  'root_cause_proven':False,'patch_authorized':False}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--jsonl',type=Path,required=True);p.add_argument('--out',type=Path)
 args=p.parse_args()
 if args.out and args.jsonl.resolve()==args.out.resolve():p.error('INPUT_OVERWRITE_FORBIDDEN')
 with args.jsonl.open(encoding='utf8') as f:result=analyze(f)
 content=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
 if args.out:
  args.out.parent.mkdir(parents=True,exist_ok=True)
  args.out.write_text(content,encoding='utf8')
 print(content)
if __name__=='__main__':main()
