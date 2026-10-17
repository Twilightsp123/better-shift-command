#!/usr/bin/env python3
"""Offline Group rebuild transaction: object checkout vs Root binding identity.

External events and completeness are UNVERIFIED. This is NOT a Windows Hook.
"""
import argparse,json,re
from collections import defaultdict
from pathlib import Path
ID=re.compile(r'^[a-z][a-z0-9_-]{0,31}$')
SCHEMA='bsc.n1.group_binding_transaction_event.v2'
OPS={'checkout','return','bind','clear','rebuild_begin','rebuild_end','snapshot'}
MAX_EVENTS=4000
def token(row,key,optional=False):
 v=row.get(key)
 if v is None and optional:return None
 if type(v)!=str or not ID.fullmatch(v) or v.startswith('0x'):
  raise ValueError('UNTRUSTED_OR_MISSING_'+key)
 return v
def replay(lines):
 serial=defaultdict(int);live={};roots={};revisions=defaultdict(int)
 active={};out=[];last=-1
 for line in lines:
  if not line.strip():continue
  if len(out)>=MAX_EVENTS:raise ValueError('BUDGET_EXCEEDED')
  row=json.loads(line)
  if not isinstance(row,dict) or row.get('schema')!=SCHEMA:raise ValueError('SCHEMA_DRIFT')
  op=row.get('event')
  if op not in OPS:raise ValueError('UNKNOWN_OPERATION')
  seq=row.get('seq')
  if type(seq)!=int or not last<seq<=100000000:raise ValueError('NONMONOTONIC_EVENT_SEQUENCE')
  last=seq;root=token(row,'root_id');pool=token(row,'pool_id')
  alias=token(row,'object_alias',optional=True)
  if op in ('checkout','return','bind') and alias is None:raise ValueError('OBJECT_ALIAS_REQUIRED')
  k=(pool,alias) if alias else None
  affected=[];unknown=False
  if op=='rebuild_begin':
   if root in active:raise ValueError('REENTRANT_SCOPE_NOT_MODELLED')
   active[root]=seq
  elif op=='rebuild_end':
   if root not in active:raise ValueError('REBUILD_END_WITHOUT_BEGIN')
   b=roots.get(root)
   if b and b[3]:raise ValueError('REBUILD_EXIT_WITH_STALE_BINDING')
   active.pop(root)
  elif op=='checkout':
   if k in live:raise ValueError('DOUBLE_CHECKOUT')
   serial[k]+=1;live[k]=serial[k]
  elif op=='return':
   if k not in live:raise ValueError('RETURN_NOT_OBSERVED_CHECKOUT')
   for who,b in list(roots.items()):
    if b and b[:2]==k and b[2]==live[k]:
     if who not in active:
      raise ValueError('AMBIGUOUS_RETURN_BOUND_OUTSIDE_TYPED_REBUILD')
     roots[who]=(*b[:3],True);affected.append(who)
   live.pop(k)
  elif op=='bind':
   incarnation=live.get(k);unknown=incarnation is None
   new=(*k,incarnation,False);old=roots.get(root)
   if old is None or old[:3]!=new[:3] or old[3]:revisions[root]+=1
   roots[root]=new
  elif op=='clear':
   if roots.get(root) is not None:revisions[root]+=1
   roots[root]=None
  b=roots.get(root)
  stale=bool(b and b[3])
  unknown=unknown or bool(b and b[2] is None)
  stable=(op=='snapshot' and root not in active and not stale and not unknown and bool(b))
  out.append(dict(seq=seq,event=op,root_id=root,root_binding_revision=revisions[root],
   object_checkout_incarnation=b[2] if b else None,
   root_pointer_stale_during_transaction=stale,
   transition_scope_active=root in active,
   affected_roots_on_return=affected,lifecycle_unknown=unknown,
   stable_snapshot_candidate=stable,atomic_engine_snapshot_proven=False))
 if active:raise ValueError('UNCLOSED_REBUILD_SCOPE')
 return dict(schema='bsc.n1.group_binding_transaction_replay.v2',events=out,count=len(out),
  input_events_come_from_real_game_proven=False,
  full_native_event_coverage_proven=False,
  cross_thread_ordering_proven=False,
  stable_snapshot_candidate_is_atomic_engine_snapshot=False,
  root_cause_proven=False,native_patch_authorized=False)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--jsonl',type=Path,required=True);p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.out.resolve()==a.jsonl.resolve():p.error('INPUT_OVERWRITE_FORBIDDEN')
 with a.jsonl.open(encoding='utf8') as f:r=replay(f)
 text=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(text,'utf8')
 print(text)
if __name__=='__main__':main()
