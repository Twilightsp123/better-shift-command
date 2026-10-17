#!/usr/bin/env python3
"""SHA-locked, read-only feasibility of WH3 member observation sites.

Does NOT attach to any process. No claim of safe production hooks or root cause.
"""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA,IMAGEBASE

PINS={
 0x0306B9F0:'48895c2410',0x0306BA08:'488b4158',0x0306BA0C:'488bf9',
 0x0306BA0F:'458af0',0x0306BA12:'488bda',
 0x0311954C:'48895c2408',0x03119556:'80b92802000001',
 0x0311CED4:'4883ec28',0x0311CEDB:'488b4910',
 0x0311CEE8:'e853b7e1ff',0x0311CF02:'488bc2',
 0x03081EB4:'488bc4',0x03082262:'8a8708010000',
 0x03082268:'a808',0x030822F9:'e88628fdff',
 0x03054BA9:'488bf9',0x0305501D:'488d8fe0010000',
 0x03055024:'488d542460',0x03055029:'e8a67e0c00',
 0x0305502E:'450f57ff',0x03055036:'f30f5c9f88000000'}
CALLS={0x0311CEE8:0x02F38640,0x030822F9:0x03054B84,
       0x03055029:0x0311CED4}
SITES={
 'packet_entry':{'rva':'0x0306B9F0','member':'RCX','packet':'RDX','mode':'R8B'},
 'goal_entry':{'rva':'0x0311954C','member':'RCX','record':'RDX','flags':'R9D'},
 'member_tick_entry':{'rva':'0x03081EB4','member':'RCX'},
 'world_goal_after_call':{'rva':'0x0305502E','member':'RDI','world_xyz':'RAX points to caller output buffer, prior to position subtract'}}
BLOCKERS=[
 'No verified MOVE/group/member generation lifecycle IDs; pointer equality is not an epoch',
 'Per-member Tick is sequential; no engine-wide atomic snapshot barrier demonstrated',
 'No tested thread-safe bounded Win64 hook deployment, only disassembly feasibility',
 'No proven typed post-steering velocity/output writer',
 'Generic 0x0311CED4 RCX is the goal record, NOT member identity']

def audit(exe):
 pe=OriginalEXE(exe)
 try:
  if pe.sha!=SHA or pe.base!=IMAGEBASE:raise ValueError('WRONG_ORIGINAL_BUILD')
  cache={}
  for at,code in PINS.items():
   raw=bytes.fromhex(code)
   if pe.section(at)!='.00cfg' or pe.read(at,len(raw))!=raw:raise ValueError('OPCODE_DRIFT:'+hex(at))
   owner=pe.owner(at)
   if owner is None:raise ValueError('NO_UNWIND_OWNER:'+hex(at))
   span=owner[:2]
   if span not in cache:cache[span]=pe.starts_in(*span)
   if at not in cache[span]:raise ValueError('MID_INSTRUCTION:'+hex(at))
  for site,target in CALLS.items():
   raw=pe.read(site,5)
   if raw[0]!=0xe8 or site+5+struct.unpack_from('<i',raw,1)[0]!=target:raise ValueError('E8_DRIFT:'+hex(site))
  if pe.owner(0x03055029)[:2]!=pe.owner(0x0305502E)[:2] or pe.owner(0x0305501D)[:2]!=pe.owner(0x03054BA9)[:2]:
   raise ValueError('CALLSITE_OR_MEMBER_OWNER_CHANGED')
  if PINS[0x0311CF02]!='488bc2' or PINS[0x0305502E]!='450f57ff':
   raise ValueError('POSTCALL_RESULT_CHANGED')
  return dict(schema='bsc.n1.static_observation_site_contract.v1',
   sha256=pe.sha,proof='EXACT_ORIGINAL_EXE_STATIC',
   guarded_opcodes=len(PINS),verified_direct_calls=len(CALLS),
   function_owners_checked=len(cache),site_contracts=SITES,
   member_source='0x03054BA9 MOV RDI,RCX; 0x0305501D LEA RCX,[RDI+0x1E0]',
   world_goal_result='0x0311CF02 MOV RAX,RDX; at 0x0305502E output is before 0x03055036 member-position subtraction',
   receiver_has_member_identity=False,safe_runtime_hook_proven=False,
   collection_ready=False,blocking_conditions=BLOCKERS,gameplay_patch_authorized=False)
 finally:pe.close()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True);p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():p.error('EXE_OVERWRITE_FORBIDDEN')
 report=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n','utf8')
 print('STATIC_PASS',report['guarded_opcodes'],'opcode starts',report['verified_direct_calls'],'E8; NOT COLLECTION READY')
if __name__=='__main__':main()
