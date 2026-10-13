#!/usr/bin/env python3
"""WH3 9.0.3: MOVE queue layout -> typed gate -> conditional per-member packet.

Original EXE SHA/PE/objdump static only. Not proof a Shift instance used
this optional +0x388 path. Never patches or writes the original executable.
"""
import argparse, json, re, shutil, struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

MOVE_VTABLE=0x0390B4F0
MOVE_B0_B8_FALSE=0x008D3330
PINS={int(a,16):b for a,b in (line.split() for line in '''
030323EE 488bd9
030326A7 83bb882f000028
030326B4 488d8b78020000
030326BE e84dddf1ff
030326CE 488d4b18
030326E4 e8d369fdff
02F50422 488bd9
02F5044C 4c8d4310
02F50477 488d0cc0
02F5047B 48c1e105
02F5047F 4903c8
02F50482 4c8909
02F504C2 41ff80082d0000
02F504C9 418b88002d0000
02F504EF 410388042d0000
02F50506 488d1cc9
02F5050A 48c1e305
02F5050E 4903d8
030090C9 488bf9
030090D1 488d1518249000
030090D8 488917
030090E7 4883a7a0000000
03039C89 488b5128
03039C8D 83ba882f000000
03039C96 8b828c2f0000
03039C9C 488dbaa0020000
03039CA3 488d0cc0
03039CA7 48c1e105
03039CAB 4803f9
03039CB4 ff90b8000000
03039CBC 7421
03039CDF f30f1005a92603
03039CE7 f30f1103
03039CF3 f30f114b04
03039D00 f30f114308
03039BF6 ff90b0000000
03039C52 ff90b8000000
03039D46 ff90b8000000
03045F94 488b4128
03045FA4 e86b3dffff
03045FAF e8103cffff
03045FBA e8613cffff
03045FCA e8ad3cffff
03045FDA 488b5548
03045FE1 488b4d28
03045FEE 4881c1c0320000
03046015 4889442420
0304601A e805a7fcff
0301073F 488da8d8feffff
03010746 4881ece8010000
03010840 4c8bad50010000
03010A69 f3410f104500
03010A73 f3410f104d04
03010A7D f3410f105508
03010ACD e8daf1f4ff
03010AE4 e8bb3d0900
03010AEE 48c1e820
03010AF2 84c0
03010AFC 488d5500
03010B06 804d6c20
03010B0A f30f114558
03010B0F ff9088030000
03010BCF e8d8f0f4ff
03010BEE e8b13c0900
03010C43 ff9080030000
03010D5A e8c9f0f4ff
03010D71 e82e3b0900
03010D7B 48c1e820
03010D7F 84c0
03010D9B 488d5500
03010DA5 804d6c20
03010DA9 f30f114558
03010DAE ff9088030000
03011036 e871ecf4ff
0301104D e852380900
03011057 48c1e820
0301105B 84c0
03011065 488d5500
0301106F 804d6c20
03011073 f30f114558
03011078 ff9088030000
0301118B e81cebf4ff
030111AF e8f0360900
03011203 ff9080030000
030A48DB f30f1185580100
030A48E6 c6855c01000000
030A49B9 f30f5905f38487
030A4A3A f30f1185580100
030A4A4D c6855c01000001
030A4A54 488b8558010000
'''.strip().splitlines())}
LEAF_SITES={
 0x02F5FD1B:'48895128',
 0x02F5FD1F:'c74158000080bf',
 0x02F5FE97:'4c894128',
 0x02F5FE9F:'c74158000080bf',
}
LEAF_BOUNDS={0x02F5FCAC:(0x02F5FCAC,0x02F5FD52),
             0x02F5FE28:(0x02F5FE28,0x02F5FED4)}
CALL_EDGES={
 0x030326BE:0x02F50410,
 0x030326E4:0x030090BC,
 0x03045FA4:0x03039D14,0x03045FAF:0x03039BC4,
 0x03045FBA:0x03039C20,0x03045FCA:0x03039C7C,
 0x0304601A:0x03010724,
 0x03010ACD:0x02F5FCAC,0x03010BCF:0x02F5FCAC,
 0x03010D5A:0x02F5FE28,0x03011036:0x02F5FCAC,
 0x0301118B:0x02F5FCAC,
 0x03010AE4:0x030A48A4,0x03010BEE:0x030A48A4,
 0x03010D71:0x030A48A4,0x0301104D:0x030A48A4,
 0x030111AF:0x030A48A4,
}
DISPATCHES_388=(0x03010B0F,0x03010DAE,0x03011078)
DISPATCHES_380=(0x03010C43,0x03011203)
RESULT_GATES={0x03010B0F:(0x03010AEE,0x03010AF2,0x03010B06,0x03010B0A),
 0x03010DAE:(0x03010D7B,0x03010D7F,0x03010DA5,0x03010DA9),
 0x03011078:(0x03011057,0x0301105B,0x0301106F,0x03011073)}
EXPECTED_SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'

def original_instruction_starts(pe):
 if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
 cache={}
 for site,code in {**PINS,**LEAF_SITES}.items():
  expected=bytes.fromhex(code)
  if pe.read(site,len(expected),True)!=expected:
   raise ValueError('OPCODE_CHANGED:'+hex(site))
  owner=pe.function(site)
  if owner is None:owner=next((span for span in LEAF_BOUNDS.values() if span[0]<=site<span[1]),None)
  if owner is None:raise ValueError('NO_UNWIND_OR_EXPLICIT_LEAF:'+hex(site))
  if owner not in cache:
   asm=pe.disasm(owner[0],owner[1]-owner[0])
   cache[owner]={int(m.group(1),16) for line in asm.splitlines()
    if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',line))}
  if site not in cache[owner]:raise ValueError('MID_INSTRUCTION:'+hex(site))
 return len(PINS)+len(LEAF_SITES),len(cache)

def static_contract(pe):
 n,owners=original_instruction_starts(pe)
 for site,target in CALL_EDGES.items():
  code=pe.read(site,5,True)
  if code[0]!=0xE8 or site+5+struct.unpack_from('<i',code,1)[0]!=target:
   raise ValueError('DIRECT_CALL_DRIFT:'+hex(site))
 for site in DISPATCHES_388+DISPATCHES_380:
  expected=0x388 if site in DISPATCHES_388 else 0x380
  if struct.unpack_from('<I',pe.read(site,6,True),2)[0]!=expected:
   raise ValueError('INDIRECT_SLOT_DRIFT:'+hex(site))
  if pe.read(site,2,True)!=b'\xff\x90':raise ValueError('INDIRECT_OPCODE_DRIFT:'+hex(site))
 for off in (0xB0,0xB8):
  actual=struct.unpack('<Q',pe.read(MOVE_VTABLE+off,8))[0]
  if actual!=pe.base+MOVE_B0_B8_FALSE:
   raise ValueError('MOVE_VTABLE_NONFALSE:'+hex(off))
 if pe.read(MOVE_B0_B8_FALSE,3,True)!=b'\x32\xc0\xc3':
  raise ValueError('MOVE_B0_B8_LEAF_CHANGED')
 if struct.unpack('<Q',pe.read(MOVE_VTABLE,8))[0]!=pe.base+0x0300C660:
  raise ValueError('MOVE_VTABLE_BASE_CHANGED')
 if struct.unpack('<Q',pe.read(MOVE_VTABLE+0x8,8))[0]!=pe.base+0x03025D70:
  raise ValueError('MOVE_VTABLE_OBJECT_TYPE_CHANGED')
 const=struct.unpack('<f',pe.read(0x0391CEB4,4))[0]
 if pe.read(0x0391CEB4,4)!=bytes.fromhex('35fa8e3c'):
  raise ValueError('ANGLE_CONVERSION_DRIFT')
 if pe.read(0x0406C390,12)!=b'\x00'*12:
  raise ValueError('FALLBACK_ZERO_VECTOR_CHANGED')
 for site,stages in RESULT_GATES.items():
  if any(x not in PINS for x in stages):raise ValueError('MISSING_VALIDITY_GATE:'+hex(site))
 if (0x278+0x2d10,0x278+0x2d14,0x278+0x10+0x18)!=(0x2f88,0x2f8c,0x2a0):
  raise ValueError('RING_OFFSET_FORMULA_CHANGED')
 return dict(schema='bsc.n1.move_slot_optional_member_packet_gate.v1',
   exe_sha256=pe.sha,proof_grade='EXACT_ORIGINAL_EXE_STATIC',
   opcodes_and_objdump_instruction_starts=n,unwind_or_explicit_leaf_owners=owners,
   direct_E8_edges=len(CALL_EDGES),typed_MOVE_vtable_slots=4,
   indirect_v380_dispatches=len(DISPATCHES_380),indirect_v388_dispatches=len(DISPATCHES_388),
   queue_layout={'queue_embedded_at_root':'0x278','slot_wrapper_first_at_root':'0x288',
    'native_slot_first_at_root':'0x2A0','slot_stride_bytes':0x120,
    'count_at_root':'0x2F88','active_index_at_root':'0x2F8C'},
   getter_queue_root='[callback_owner+0x28]',
   getter_MOVE_plusB8_gate='0x008D3330 returns false',
   MOVE_plusB0_gate='0x008D3330 returns false',
   getter_fallback_vector='float32(0,0,0)',
   packed_result_float_plus_flag=True,
   caller_temp_packet_argument='RBP+0x00 in function 0x03010724',
   caller_world_reference='5th argument from 0x03045F80 stack [rsp+0x20] to callee [rbp+0x150]',
   helper_calls_in_caller=len([site for site,dest in CALL_EDGES.items() if dest==0x030A48A4]),
   packet_constructors={'0x02F5FCAC':4,'0x02F5FE28':1},
   optional_float_default=-1.0,
   native_angle_unit_scale=const,
   both_packet_constructors_set_minus_one_default=True,
   implicit_MOVE_slot_is_special_plusB8_type=False,
   special_member_virtual388_always_executed_for_SHIFT=False,
   original_SHIFT_instance_execution_proven=False,
   queue_instance_identity_across_functions_proven=False,
   member_crowding_cause_proven=False,
   native_patch_authorized=False)

def audit(exe):
 pe=StrictPE(Path(exe))
 try:
  if pe.sha!=EXPECTED_SHA:raise ValueError('SHA_MISMATCH')
  return static_contract(pe)
 finally:pe.close()

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.exe.resolve()==a.out.resolve():p.error('NEVER_OVERWRITE_EXE')
 result=audit(a.exe)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print('PASS',result['opcodes_and_objdump_instruction_starts'],'opcodes;',result['direct_E8_edges'],'E8; MOVE gate is false; NO PATCH')
