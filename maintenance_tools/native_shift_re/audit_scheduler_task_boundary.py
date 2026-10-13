#!/usr/bin/env python3
"""WH3 9.0.3 exact original EXE: dispatcher stack and separate task callback.

Read-only static proof: not an RMB/Shift instance trace and never a game patch.
Requires SHA-pinned x64 PE/unwind and real objdump instruction boundaries.
"""
import argparse,json,re,shutil,struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

PINS = {
0x0326FF88:'488b5310', 0x0326FF8C:'8b8298080000', 0x0326FF97:'48399cc2180800',
0x0326FFC3:'8b8a98080000',0x0326FFCE:'48399cca180800',
0x03270064:'488b5310',0x03270068:'8b8a98080000',0x03270073:'48399cca180800',
0x0327C6B4:'488b5110',0x0327C6B8:'80baa808000000',0x0327C6C1:'8b8298080000',
0x0327C6C9:'3982ac080000',0x0327C6D1:'c682a908000001',
0x0327C6D8:'488b4910',0x0327C6DC:'8b91ac080000',0x0327C6E4:'e853f8e5ff',
0x030DBF50:'80b9a808000000',0x030DBF5E:'c681a808000000',
0x030DBF65:'399198080000',0x030DBF6D:'488da918080000',
0x030DBF74:'8bbd80000000',0x030DBF7F:'488b4cfd00',0x030DBF93:'8b44fd08',
0x030DBF97:'29839c080000',0x030DBFA1:'0183a0080000',0x030DBFA7:'ff8b98080000',
0x032701F2:'e851c40000',0x0327020D:'488b8b88000000',0x03270219:'80792500',
0x0327021F:'83792004',0x03270229:'e8b2c3eaff',
0x0327C648:'4883ec28',0x0327C64C:'488b8188000000',
0x0327C65B:'83782004',0x0327C661:'80782400',
0x0311C5E4:'83792004',0x0311C5F0:'80792400',
0x0311C5F6:'80792500',0x0311C603:'4881c168010000',
0x0311C60A:'e865000000',
0x030EE88D:'44894120',0x030EE891:'6644894124',0x030EE90F:'4d898268010000',
0x030C4813:'488d4b30',0x030C4817:'e820770100',0x030C481C:'8b83c8080000',
}
EDGES = {
0x0327C6E4:0x030DBF3C,0x032701F2:0x0327C648,
0x03270229:0x0311C5E0,0x0311C60A:0x0311C674,
0x030C4817:0x030DBF3C,
}
TYPED_CALLBACKS = {
0x039407A8:0x032701C4, # separate descriptor; NOT factory A or B
0x03940ED8:0x0326FFF4, # A's sibling dispatcher callback
0x03940EE0:0x0326F0DC, # A's constructor callback
0x03941400:0x0326FF60, # B's sibling dispatcher callback
0x03941408:0x0326F07C, # B's constructor callback
}
EXPECTED_SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'

def verify(pe):
 if pe.sha!=EXPECTED_SHA:raise ValueError('WRONG_EXE_SHA')
 if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
 verified={}
 for site,hexcode in PINS.items():
  if pe.read(site,len(hexcode)//2,True).hex()!=hexcode:
   raise ValueError('OPCODE_CHANGED:'+hex(site))
  owner=pe.function(site)
  if not owner:raise ValueError('NO_UNWIND_OWNER:'+hex(site))
  if owner not in verified:
   asm=pe.disasm(owner[0],owner[1]-owner[0])
   verified[owner]={int(m.group(1),16) for line in asm.splitlines()
     if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',line))}
  if site not in verified[owner]:raise ValueError('MID_INSTRUCTION:'+hex(site))
 for site,target in EDGES.items():
  code=pe.read(site,5,True)
  if code[0]!=0xE8 or site+5+struct.unpack_from('<i',code,1)[0]!=target:
   raise ValueError('E8_CHANGED:'+hex(site))
 for site,target in TYPED_CALLBACKS.items():
  if struct.unpack('<Q',pe.read(site,8))[0]!=pe.base+target:
   raise ValueError('DESCRIPTOR_CALLBACK_CHANGED:'+hex(site))
 return {
 'schema':'bsc.n1.scheduler_stack_and_separate_task_callback.v1',
 'exe_sha256':pe.sha,'evidence_level':'EXACT_ORIGINAL_EXE_STATIC',
 'opcode_instruction_starts':len(PINS),'E8_edges':len(EDGES),
 'typed_callbacks':len(TYPED_CALLBACKS),'unwind_function_owners':len(verified),
 'dispatcher_embedded_layout':{
  'owner_destructor':'0x030C47A4',
  'owner_plus_30_dispatcher':'0x030C4813',
  'owner_plus_8C8_equals_dispatcher_plus_898':True,
  'stack_slot_start':'dispatcher+0x818',
  'stride_bytes':16,'count':'dispatcher+0x898','slot_weight':'slot+0x08',
  'weight_on_remove':'dispatcher+0x89C -= weight; +0x8A0 += weight',
  'count_on_remove':'dispatcher+0x898 -= 1',
  'removal_gate':'dispatcher+0x8A8','active_index':'dispatcher+0x8AC'},
 'factory_dispatcher_callbacks':{
  'A':'0x0326FFF4','B':'0x0326FF60',
  'both_examine_last_stack_slot':True,
  'old_factory_callbacks_have_distinct_identity':True},
 'separate_task_descriptor':{
  'callback_slot':'0x039407A8','callback':'0x032701C4',
  'not_A_or_B_callback':True,'read_parent_plus_88':'0x0327020D',
  'status_checker':'0x0327C648','task_read_plus_168':'0x0311C603',
  'task_status_fields_mirror_move_task_constructor':True,
  'actual_same_pointer_as_MOVE_slot_plus_A0_proven':False},
 'MOVE_slot_to_A_B_factory_parent_proven':False,'native_patch_authorized':False,
 }

def audit(exe):
 pe=StrictPE(Path(exe))
 try:return verify(pe)
 finally:pe.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--exe',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True)
 args=ap.parse_args()
 if args.exe.resolve()==args.out.resolve():ap.error('NEVER_OVERWRITE_GAME_EXE')
 result=audit(args.exe)
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print('PASS',result['opcode_instruction_starts'],'opcode starts',
       result['E8_edges'],'direct calls',result['typed_callbacks'],
       'distinct typed callbacks; NO PATCH')
if __name__=='__main__':main()
