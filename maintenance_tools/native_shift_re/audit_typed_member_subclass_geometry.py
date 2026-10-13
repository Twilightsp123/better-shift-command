#!/usr/bin/env python3
"""Exact WH3 9.0.3 read-only audit: typed member geometry and false +0x88 setter.

The actor constructor installs 0x0390FAB0. A different 0x90-byte adapter
receives the SIMD store across +0x88 in 0x0326F4C4; do not alias them.
No game code is changed, no raw executable/runtime pointers are committed.
"""
import argparse,json,re,shutil,struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

EXPECTED_SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
SLOTS={
0x0390FAB0:{0x260:0x008D3330,0x348:0x0306B510,0x368:0x03117CE0,0x388:0x03117D44,0x580:0x0306A990,0x5B8:0x0306A8C0},
0x038FD658:{0x260:0x008D3330,0x348:0x0306B510,0x368:0x0306B9F0,0x388:0x0306C0DC,0x580:0x0306A990,0x5B8:0x0306A8C0},
0x03910500:{0x260:0x008D3330,0x348:0x0306B510,0x368:0x0306B9F0,0x388:0x0306C0DC,0x580:0x0306A990,0x5B8:0x0306A8C0}}
PINS={int(a,16):b for a,b in (line.split() for line in """
030ee4d0 e8abfeffff
030ee4d5 488d05d4158200
030ee4df 488903
03117cfb ff9060020000
03117d3f e9ac3cf5ff
03117d5a ff9060020000
03117d62 0f859d000000
03117deb e84c1a1300
03117e00 e887000000
03117ea1 488bb9680b0000
03117eab 8b81640b0000
03117eba f6456840
03117ef7 ff90b8050000
03117f3c f6456802
03117f40 0f8401010000
03117f76 ff90c8020000
03118038 e9b4feffff
03118040 41ff90b8050000
0311804e 0f8566feffff
0326f4dd b990000000
0326f4e5 e8d256e5ff
0326f4ea 488bd8
0326f533 e8505fffff
0326f53d 488d05f45a6a00
0326f548 488903
0326f54b f30f7f8380000000
03265179 488d05888c8700
03265180 488903
0326519b 48898388000000
""".strip().splitlines())}
CALLS={0x030EE4D0:0x030EE380,0x03117DEB:0x0324983C,0x03117E00:0x03117E8C,0x0326F4E5:0x030C4BBC,0x0326F533:0x03265488}
JUMPS={0x03117D3F:0x0306B9F0,0x03118038:0x03117EF1}
LEAS={0x030EE4D5:0x0390FAB0,0x0326F53D:0x03915038,0x03265179:0x03ADDE08}

def opcode_boundaries(pe):
 if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
 cache={}
 for at,h in PINS.items():
  if pe.read(at,len(h)//2,True).hex()!=h:raise ValueError('OPCODE_DRIFT:'+hex(at))
  owner=pe.function(at)
  if not owner:raise ValueError('UNWIND_OWNER_MISSING:'+hex(at))
  if owner not in cache:
   asm=pe.disasm(owner[0],owner[1]-owner[0])
   cache[owner]={int(m.group(1),16) for row in asm.splitlines()
    if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',row))}
  if at not in cache[owner]:raise ValueError('MID_INSTRUCTION:'+hex(at))
 return len(PINS),len(cache)

def checked_rel32(pe,at,target,opcode):
 raw=pe.read(at,5,True)
 if raw[0]!=opcode or at+5+struct.unpack_from('<i',raw,1)[0]!=target:
  raise ValueError('BAD_BRANCH:'+hex(at))

def checked_lea(pe,at,target):
 raw=pe.read(at,7,True)
 if raw[:3]!=b'\x48\x8d\x05' or at+7+struct.unpack_from('<i',raw,3)[0]!=target:
  raise ValueError('BAD_LEA:'+hex(at))

def audit(exe):
 pe=StrictPE(Path(exe))
 try:
  if pe.sha!=EXPECTED_SHA:raise ValueError('WRONG_EXE')
  count,owners=opcode_boundaries(pe)
  for site,target in CALLS.items():checked_rel32(pe,site,target,0xE8)
  for site,target in JUMPS.items():checked_rel32(pe,site,target,0xE9)
  for site,target in LEAS.items():checked_lea(pe,site,target)
  for base,entries in SLOTS.items():
   for off,target in entries.items():
    if struct.unpack('<Q',pe.read(base+off,8))[0]!=pe.base+target:
     raise ValueError('MEMBER_VTABLE_DRIFT:'+hex(base+off))
  if pe.read(0x008D3330,3,True)!=b'\x32\xc0\xc3':
   raise ValueError('MEMBER_PLUS260_NOT_FALSE_LEAF')
  if struct.unpack('<Q',pe.read(0x03940850,8))[0]!=pe.base+0x0326F4C4:
   raise ValueError('REGISTERED_ADAPTER_WRITER_MOVED')
  return dict(schema='bsc.n1.typed_member_geometry_and_false_plus88_writer.v1',
   sha256=pe.sha,grade='EXACT_EXE_STATIC',
   opcode_instruction_starts=count,unwind_function_owners=owners,
   direct_calls=len(CALLS),direct_jumps=len(JUMPS),
   RIP_LEAS=len(LEAS),typed_member_vtable_slots=sum(len(x) for x in SLOTS.values()),
   member_constructor='0x030EE464 installs vtable 0x0390FAB0',
   member_specific_receiver='0x0390FAB0+0x368 -> 0x03117CE0 -> 0x0306B9F0 (tailjump)',
   member_specific_geometry='0x0390FAB0+0x388 -> 0x03117D44',
   member_plus_260_returns_false_for_pinned_vtable=True,
   geometry_packing='0x03117D44 -> 0x0324983C -> 0x03117E8C',
   fanout_array='owner+0xB68 with owner+0xB64 count',
   per_member_conditions='input+0x68 flags and member current action state select +0x5B8 or other branches',
   third_handler_plus88_false_writer='0x0326F4C4 allocates distinct 0x90-byte object with vtable 0x03915038; SIMD store to its +0x80..+0x8F',
   other_plus88_false_writer='0x03265164 installs vtable 0x03ADDE08; +0x88 write is different class',
   MOVE_queued_subtask_to_this_input_instance_proven=False,
   crowding_cause_proven=False,native_patch_authorized=False)
 finally:pe.close()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.exe.resolve()==a.out.resolve():p.error('NEVER_OVERWRITE_EXE')
 report=audit(a.exe)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print('PASS',report['opcode_instruction_starts'],'opcodes',report['typed_member_vtable_slots'],'member slots; NO PATCH')

if __name__=='__main__':main()
