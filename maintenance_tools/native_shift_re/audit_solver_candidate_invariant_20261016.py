#!/usr/bin/env python3
"""Exact original WH3 solver result1/result2 vs shared candidate-count contract.

Read-only fixed binary. No Shift runtime hit or gameplay patch is implied.
"""
import argparse,json,pathlib,struct
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA
from audit_converter_return_contract_20261016 import branch
PINS=pathlib.Path(__file__).with_name('solver_candidate_invariant_pins_20261016.txt')
JUMPS={0x03126636:0x031266cd,0x031266ba:0x031267f0,
 0x031267c4:0x031267ca,0x031267c8:0x0312681a,
 0x030fddb6:0x030fdece,0x030fddc2:0x030fdea3}
E8={0x031267cd:0x03102aa8,0x030fddac:0x03125a1c}

def guards():
 data={}
 for line in PINS.read_text('utf8').splitlines():
  parts=line.split('#',1)[0].split()
  if not parts:continue
  if len(parts)!=2:raise ValueError('INVALID_PIN_ROW')
  rva=int(parts[0],16)
  if rva in data:raise ValueError('DUPLICATE_PIN')
  data[rva]=bytes.fromhex(parts[1])
 if len(data)!=35:raise ValueError('PIN_INVENTORY_DRIFT')
 return data

def solver_classification(result,concurrent_writer=False):
 if result==2:return 'unknown_race' if concurrent_writer else 'nonzero_count_required'
 if result==1:return 'earlier_nonzero_count_but_virtual_can_mutate'
 return 'alternate_or_failure_path'

def audit(path):
 pe=OriginalEXE(path)
 try:
  if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
  g=guards(); owners={}
  for site,raw in g.items():
   if pe.section(site)!='.00cfg' or pe.read(site,len(raw))!=raw:
    raise ValueError('OPCODE_CHANGED:'+hex(site))
   owner=pe.owner(site)
   if owner is None:raise ValueError('NO_UNWIND_OWNER:'+hex(site))
   span=owner[:2]
   if span not in owners:owners[span]=pe.starts_in(*span)
   if site not in owners[span]:raise ValueError('MID_INSTRUCTION:'+hex(site))
  for site,dest in JUMPS.items():
   if branch(site,g[site])!=dest:raise ValueError('JCC_DRIFT:'+hex(site))
  for site,dest in E8.items():
   raw=pe.read(site,5)
   if raw[0]!=0xe8 or site+5+struct.unpack_from('<i',raw,1)[0]!=dest:
    raise ValueError('E8_DRIFT:'+hex(site))
  # Caller [RSP+0x28] equals callee [entryRSP+0x30];
  # seven pushes and RBP=entryRSP-0x4D8 give callee [RBP+0x508].
  if (-0x4d8+0x508)!=0x30 or (-8+0x30)!=0x28:
   raise ValueError('WIN64_STACK_ALIAS_DRIFT')
  # Explicit 0x04360378 container address, +4 count field,
  # and return 2 guarded by [R14+4] nonzero branch.
  if pe.read(0x030fdd88,7)!=bytes.fromhex('488d05e9252601') or \
     pe.read(0x031267bf,5)!=bytes.fromhex('41837e0400') or \
     pe.read(0x0312681a,5)!=bytes.fromhex('b802000000') or \
     pe.read(0x031267f9,4)!=bytes.fromhex('41ff5018'):
   raise ValueError('CANDIDATE_RETURN_SOURCE_CHANGED')
  # 0x031267C4 JZ goes to container reset rather than result2.
  # result1 requires the earlier array-member loop but invokes a
  # virtual method, whose side effects on shared state are not proved.
  return {'schema':'bsc.n1.solver_candidate_return_contract.v1',
   'sha256':pe.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
   'decoded_guarded_sites':len(g),'E8_edges':len(E8),'JCC_edges':len(JUMPS),
   'container':'caller 0x04360378 passed via Win64 sixth argument, solver R14; +4 count',
   'result2_requires_nonzero_count_at_check':True,
   'same_thread_no_call_between_result2_and_converter_count_test':True,
   'result1_entered_nonempty_candidate_iteration':True,
   'result1_virtual_may_change_count':True,
   'result1_following_count_zero_proven_impossible':False,
   'concurrent_mutation_ruled_out':False,
   'actual_player_shift_null_observed':False,'gameplay_patch_authorized':False}
 finally:pe.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--exe',type=pathlib.Path,required=True)
 ap.add_argument('--out',type=pathlib.Path)
 a=ap.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():ap.error('EXE_OVERWRITE_FORBIDDEN')
 r=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print('STATIC_PASS',r['decoded_guarded_sites'],'opcodes',r['E8_edges'],'E8',r['JCC_edges'],'branches; NO PATCH')
if __name__=='__main__':main()
