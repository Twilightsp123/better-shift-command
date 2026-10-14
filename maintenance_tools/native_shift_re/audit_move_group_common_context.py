#!/usr/bin/env python3
"""SHA-pinned WH3 9.0.3 native MOVE -> UnitRoot -> group -> member fanout.

Two DIFFERENT source preparations enter the same typed group fanout function.
No causal claim of Shift model crowding and no original game modification.
The context's +0x160 and a queued MOVE task's +0x160 are NOT treated as aliases.
"""
import argparse
import json
import re
import shutil
import struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
PINS={int(a,16):bytes.fromhex(b) for a,b in (ln.split() for ln in r'''
02F2C734 4053
02F2C73D 488d0564899d00
02F2C74D 48895108
02F2C777 488d059af6b800
02F2C77E 488901
02F563F4 488b4b08
02F563F8 488d542450
02F563FD 488b89f8320000
02F56404 e8373a3200
0300889E 488b4238
030088A8 498bd8
030088BF 0f28f3
030088C2 488b8040040000
030088C9 488b8860010000
030088D0 e8db901100
030088D5 48894718
03012897 488b4138
030128A4 4c8b8040040000
03012982 e80d5fffff
03012987 48898770020000
030129A7 488b4738
030129B0 48894108
030129B7 48897910
030129E5 48898f70020000
0301B844 8950d8
0301B84A 4c8940e0
0301B8AB 488d542420
0301B8B7 e880730a00
0301B8E4 48895c2408
0301B90F 4c8bc6
0301B917 ba03000000
0301B91F e810ffffff
0301B96D 48899ef8320000
03025DBB 488b4310
03025DBF 488b4808
0302609B 488b4b10
030260A8 488b5108
030260AF e88066f0ff
0302DB6D 4c8b8040040000
0302DB81 488b81483d0000
0302DB88 8b9048020000
0302DB8E e851ddfeff
0302DBC4 e8b34cfeff
0302DBC9 488b8570020000
0302DBD3 488b5018
0302DBD7 488b5270
0302DBDB e8b0780a00
030C2C50 488bfa
030C2C56 488b5208
030C2C5A 4883c230
030C2C61 e8da000000
030C2C68 488d0d81c98400
030C2C6F 48890b
030C2C7D 488983100a0000
030C2D40 488b4208
030C2D44 48894108
030C2D48 488b4208
030C2D4E 48894110
030C2D52 488d05c7c88400
030C2D59 488901
030C2DC5 c3
030D54A2 4c8b99300b0000
030D54BC 448b4f24
030D54CA 41ff5248
030D54D5 488b4728
030D54D9 4c8d0476
030D54DD 49c1e004
030D54E6 4c03442440
030D54F0 488b1cf0
030D54F7 450fb74822
030D54FC e867a3e8ff
030D550F ff9068030000
030D5522 ff5020
030D5561 8b4924
030D5566 0f84a9000000
030D5575 488b83300b0000
030D55AD 488b4310
030D55C7 488b8840040000
030D55DD 488b8960010000
030D55E4 4883c118
030D55F5 e8a2840200
030D5603 e888feffff
030EE88D 44894120
030EE891 6644894124
030EE90F 4d898268010000
030EE92B 4d898260010000
03279E4A 488b4110
03279E54 488b8840040000
03279E5B 488b8950010000
03279E62 e89d8fb4ff
03279E69 744f
03279E78 498b81100a0000
03279E7F 488b8870020000
03279E86 440fb74144
03279E99 498b81100a0000
03279EA0 488b8870020000
03279EA7 f30f105940
03279EB3 e894b6e5ff
'''.strip().splitlines())}
LEAF_SPAN=(0x030C2D40,0x030C2DC6)
DIRECT_CALLS={
 0x0301B91F:0x0301B834,
 0x0301B8B7:0x030C2C3C,
 0x030C2C61:0x030C2D40,
 0x0302DB8E:0x0301B8E4,
 0x0302DBC4:0x0301287C,
 0x0302DBDB:0x030D5490,
 0x03012982:0x03008894,
 0x030088D0:0x031219B0,
 0x030260AF:0x02F2C734,
 0x02F56404:0x03279E40,
 0x03279E62:0x02DC2E04,
 0x03279EB3:0x030D554C,
 0x030D55F5:0x030FDA9C,
 0x030D5603:0x030D5490,
 0x030D54FC:0x02F5F868,
}
VTABLE_METHODS={
 0x0390B4F0+0x08:0x03025D70,
 0x03ABBE18+0x10:0x02F561E8,
}
INSTALLED_VTABLES={
 0x030C2D52:0x0390F620,
 0x030C2C68:0x0390F5F0,
 0x02F2C777:0x03ABBE18,
}

def symbolic_sources(root='ROOT'):
 """Field-provenance expression graph, NOT an observed runtime pointer alias."""
 ctx=f'MEM[{root}+0x38]'
 deeper=f'MEM[{ctx}+0x440]'
 geom=f'MEM[{deeper}+0x160]'
 group={'owner':root,'plus_10_context':ctx}
 route_config={'root':root,'source_context':ctx,'source_geometry':geom,
               'route_payload_creator':'0x031219B0','result_field':'root+0x270'}
 deferred={'group':group,'source_context':ctx,'source_geometry':geom,
           'input_to_converter':geom+'+0x18','converter':'0x030FDA9C'}
 return {'group':group,'route_config':route_config,'deferred_fanout':deferred,
         'queue_big_task_plus160_alias_proven':False}

def audit(exe):
 pe=StrictPE(Path(exe))
 try:
  if pe.sha!=SHA:raise ValueError('WRONG_ORIGINAL_EXE_SHA')
  if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
  cache={}
  for site,raw in PINS.items():
   if pe.read(site,len(raw),True)!=raw:
    raise ValueError('EXACT_OPCODE_DRIFT:'+hex(site))
   owner=pe.function(site)
   if owner is None and LEAF_SPAN[0]<=site<LEAF_SPAN[1]:owner=LEAF_SPAN
   if owner is None:raise ValueError('UNVERIFIED_UNWIND_OWNER:'+hex(site))
   if owner not in cache:
    asm=pe.disasm(owner[0],owner[1]-owner[0])
    cache[owner]={int(m.group(1),16) for ln in asm.splitlines()
      if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',ln))}
   if site not in cache[owner]:raise ValueError('MID_INSTRUCTION:'+hex(site))
  # Explicit no-unwind constructor terminates with ret, then padding INT3.
  if pe.read(0x030C2DC5,3,True)!=b'\xc3\xcc\xcc':
   raise ValueError('NO_UNWIND_LEAF_END_DRIFT')
  for site,target in DIRECT_CALLS.items():
   raw=pe.read(site,5,True)
   if raw[0]!=0xe8 or site+5+struct.unpack_from('<i',raw,1)[0]!=target:
    raise ValueError('DIRECT_E8_DRIFT:'+hex(site))
  for slot,target in VTABLE_METHODS.items():
   if struct.unpack('<Q',pe.read(slot,8))[0]!=pe.base+target:
    raise ValueError('TYPED_VTABLE_METHOD_DRIFT:'+hex(slot))
  for site,target in INSTALLED_VTABLES.items():
   raw=pe.read(site,7,True)
   # compiler may use either LEA RAX or LEA RDX
   if raw[:3] not in (b'\x48\x8d\x05',b'\x48\x8d\x15',b'\x48\x8d\x0d') or site+7+struct.unpack_from('<i',raw,3)[0]!=target:
    raise ValueError('RIP_INSTALLED_VTABLE_DRIFT:'+hex(site))
  if pe.read(0x03279E69,2,True)!=b'\x74\x4f':
   raise ValueError('TASK_CALLBACK_MODE_GATE_CHANGED')
  if 0x03279E69+2+struct.unpack('<b',pe.read(0x03279E6A,1,True))[0]!=0x03279EBA:
   raise ValueError('TASK_CALLBACK_SKIP_TARGET_CHANGED')
  if PINS[0x030C2D44]!=bytes.fromhex('48894108') or PINS[0x030C2D4E]!=bytes.fromhex('48894110'):
   raise ValueError('GROUP_CONTEXT_FIELD_WRITERS_CHANGED')
  return {
   'schema':'bsc.n1.original_MOVE_group_shared_context_and_two_fanouts.v1',
   'original_sha256':pe.sha,'verification_grade':'EXACT_ORIGINAL_EXE_STATIC',
   'opcode_and_objdump_instruction_starts':len(PINS),
   'unwind_or_explicit_leaf_function_bodies':len(cache),
   'direct_E8_calls':len(DIRECT_CALLS),
   'typed_vtable_method_pointers':len(VTABLE_METHODS),
   'RIP_installed_vtables':len(INSTALLED_VTABLES),
   'root_group_identity_source':{
     '0x0301B8E4':'passes UnitRoot as R8 to 0x0301B834',
     '0x0301B834':'stores R8 in constructor parameter block +0x08',
     '0x030C2C3C':'passes UnitRoot+0x30 to leaf 0x030C2D40',
     '0x030C2D40':'stores MEM[UnitRoot+0x38] into group+0x08 and group+0x10',
     '0x030C2C3C':'stores UnitRoot into group+0xA10',
     '0x0301B8E4':'stores created group into UnitRoot+0x32F8',
   },
   'symbolic_sources':symbolic_sources(),
   'immediate_move_route_and_fanout':'0x0302DB44 -> 0x0301287C writes root+0x270 -> 0x030D5490',
   'conditional_task_to_group':'0x03025D70 -> 0x02F2C734(task+8=root) -> 0x02F561E8 -> root+0x32F8 -> 0x03279E40',
   'conditional_task_mode_gate':'0x03279E62 helper 0x02DC2E04; zero skips 0x030D554C',
   'task_group_uses_root_route_descriptor':'group+0xA10 -> root+0x270 -> route+0x40/+0x44 on fallback',
   'deferred_member_fanout':'group+0x10 -> +0x440 -> +0x160+0x18 -> 0x030FDA9C -> 0x030D5490',
   'immediate_and_deferred_fanout_have_different_geometry_inputs':True,
   'task_callback_always_fanout':False,
   'two_fanouts_in_same_player_SHIFT_instance_observed':False,
   'group_context_plus160_equals_queued_big_task_plus160_proven':False,
   'same_soldier_goal_generation_mismatch_proven':False,
   'native_gameplay_patch_authorized':False,
  }
 finally:pe.close()

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--exe',type=Path,required=True)
 parser.add_argument('--out',type=Path,required=True)
 args=parser.parse_args()
 if args.exe.resolve()==args.out.resolve():parser.error('NEVER_OVERWRITE_EXE')
 report=audit(args.exe)
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('PASS exact original EXE',report['opcode_and_objdump_instruction_starts'],'instructions;',report['direct_E8_calls'],'direct calls; NO PATCH')
