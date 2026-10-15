#!/usr/bin/env python3
"""Original B node0/node1 route readiness difference; fixed original EXE only."""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA
PINS={
 0x02f4f5c3:'488d542450',0x02f4f5c8:'c684249c00000001',
 0x02f4f5de:'e8cd231d00',0x03271be9:'e862aee7ff',
 0x03271c04:'e8a7fdeaff',0x030eca56:'4533d2',
 0x030ecaab:'4488514c',0x03121a25:'6683630800',
 0x03121a45:'4883637000',0x03121a82:'e87d13caff',
 0x03121a87:'3c01',0x03121a89:'7406',
 0x03121a8b:'807e4c01',0x03121a8f:'7515',
 0x03121a99:'e8febffdff',0x03121a9e:'48894370',
 0x03121aa2:'c6430801',
}
E8={0x02f4f5de:0x031219b0,0x03271be9:0x030eca50,
    0x03271c04:0x031219b0,0x03121a82:0x02dc2e04,
    0x03121a99:0x030fda9c}
LEAF=(0x030eca50,0x030ecab0)
def convert_attempt(mode,record_flag):
 return mode==1 or record_flag==1

def audit(exe):
 pe=OriginalEXE(exe)
 try:
  if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
  starts={}
  for at,raw in PINS.items():
   code=bytes.fromhex(raw)
   if pe.section(at)!='.00cfg' or pe.read(at,len(code))!=code:
    raise ValueError('OPCODE_DRIFT:'+hex(at))
   owner=pe.owner(at)
   bounds=owner[:2] if owner else LEAF if LEAF[0]<=at<LEAF[1] else None
   if bounds is None:raise ValueError('OWNER_DRIFT:'+hex(at))
   if bounds not in starts:starts[bounds]=pe.starts_in(*bounds)
   if at not in starts[bounds]:raise ValueError('MID_INSTRUCTION:'+hex(at))
  for at,target in E8.items():
   b=pe.read(at,5)
   if b[0]!=0xe8 or at+5+struct.unpack_from('<i',b,1)[0]!=target:
    raise ValueError('E8_DRIFT:'+hex(at))
  # source+0x4C (at record beginning RSP+0x50) is RSP+0x9C
  if (0x50+0x4c)!=0x9c:raise ValueError('STACK_RECORD_ALIAS_DRIFT')
  return {'schema':'bsc.n1.node0_vs_fallback_node1_mode_gate.v1',
   'sha256':pe.sha,'pin_instruction_starts':len(PINS),'E8_guards':len(E8),
   'initial_shorttask_record_plus4c':1,'fallback_B_record_plus4c':0,
   'node_conversion_attempt_gate':'mode helper == 1 OR input record+0x4c == 1',
   'initial_node_attempts_conversion_even_mode_ne1':True,
   'fallback_node_requires_mode1_for_immediate_conversion':True,
   'node_plus8_set_after_converter_without_testing_result_pointer':True,
   'converter_nonnull_result_proven':False,
   'same_group_generation_proven':False,'gameplay_patch_authorized':False}
 finally:pe.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--out',type=Path)
 a=ap.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():ap.error('EXE_OVERWRITE_FORBIDDEN')
 r=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('PASS',r['pin_instruction_starts'],'opcode starts',r['E8_guards'],'E8; NO PATCH')
if __name__=='__main__':main()
