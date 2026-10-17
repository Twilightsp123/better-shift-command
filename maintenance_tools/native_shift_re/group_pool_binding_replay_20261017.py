# LEGACY R30 MODEL: return-with-binding unconditionally raises. This is NOT
# a universal native WH3 invariant: verified 0x0301B8E4 retires groups before
# its direct UnitRoot+0x32F8 rebind. Prefer group_rebuild_transaction_replay_20261017.py
# when modeling this bounded non-atomic rebuild. Do not use legacy rejection
# as evidence of a game bug. Public R30 regression intentionally tests this
# restrictive, now documented legacy behavior.
#!/usr/bin/env python3
"""Offline event ledger; NEVER a game Hook, and event completeness is unproved."""
import argparse,json,re
from collections import defaultdict
from pathlib import Path
ID=re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,40}$')
TYPES={'checkout','return','bind','clear','snapshot'}
def atom(x,k):
 v=x.get(k)
 if not isinstance(v,str) or not ID.fullmatch(v) or v.lower().startswith('0x'):
  raise ValueError('INVALID_OR_POINTER_ID:'+k)
 return v
def analyze(lines):
 live={};serial=defaultdict(int);roots={};revision=defaultdict(int)
 records=[];last=0
 for line in lines:
  if not line.strip():continue
  if len(records)>=5000:raise ValueError('EVENT_BUDGET_EXCEEDED')
  obj=json.loads(line)
  if not isinstance(obj,dict) or obj.get('schema')!='bsc.n1.pool_binding_event.v1':
   raise ValueError('INVALID_SCHEMA')
  op=obj.get('event')
  if op not in TYPES:raise ValueError('INVALID_EVENT')
  seq=obj.get('seq')
  if type(seq)!=int or seq<=last:raise ValueError('NON_MONOTONIC_SEQUENCE')
  last=seq;root=atom(obj,'root_id');pool=atom(obj,'pool_id')
  alias=atom(obj,'object_alias') if op not in ('clear','snapshot') else None
  key=(pool,alias) if alias else None
  changed=False;unknown=False
  if op=='checkout':
   if key in live:raise ValueError('DOUBLE_CHECKOUT_WITHOUT_RETURN')
   serial[key]+=1;live[key]=serial[key]
  elif op=='return':
   if key not in live:raise ValueError('RETURN_WITHOUT_CHECKOUT')
   if any(v is not None and v[:2]==key for v in roots.values()):
    raise ValueError('RETURN_WHILE_ROOT_BOUND')
   live.pop(key)
  elif op=='bind':
   incarnation=live.get(key)
   new=(pool,alias,incarnation)
   if roots.get(root)!=new:revision[root]+=1;changed=True
   roots[root]=new
   unknown=incarnation is None
  elif op=='clear':
   if roots.get(root) is not None:revision[root]+=1;changed=True
   roots[root]=None
  elif op=='snapshot':
   v=roots.get(root);unknown=v is None or v[2] is None
  v=roots.get(root)
  records.append(dict(seq=seq,event=op,root_id=root,binding_revision=revision[root],
   binding_changed=changed,pool_checkout_incarnation=v[2] if v else None,
   lifetime_uncertain=unknown or (v is not None and v[2] is None)))
 return dict(schema='bsc.n1.offline_group_pool_binding_replay.v1',
  events=records,event_count=len(records),full_event_coverage_proven=False,
  source_is_real_gameplay_verified=False,
  root_binding_revision_is_group_lifetime_generation=False,
  raw_object_alias_is_lifetime_generation=False,
  root_cause_proven=False,patch_authorized=False)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--jsonl',type=Path,required=True);p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.jsonl.resolve()==a.out.resolve():p.error('INPUT_OVERWRITE_FORBIDDEN')
 with a.jsonl.open(encoding='utf8') as f:r=analyze(f)
 s=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(s,encoding='utf8')
 print(s)
if __name__=='__main__':main()
