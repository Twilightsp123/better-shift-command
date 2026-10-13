#!/usr/bin/env python3
"""Exact WH3 9.0.3 original EXE: constructor -> type -> third handler callbacks."""
import argparse,json,re,shutil,struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE
PINS={int(a,16):b for a,b in (ln.split() for ln in """
0326581C 4053
03265833 4533c0
03265852 488d05cf8b8700
03265864 488901
03265867 488d05b28c8700
0326586E 48894130
032658AC 4c898388000000
032658D7 448883b2000000
0326F16C 488d42d0
0326F179 e9c6f8ffff
0326EA44 488bc4
0326EAB2 488b4328
0326EAD1 4c8b8840040000
0326EADB 4d8b8960010000
0326EAE2 ff5208
032701C4 4053
032701CA 488d42d0
032701DA 80bbb200000000
032701F2 e851c40000
0327020D 488b8b88000000
03270219 80792500
0327021F 83792004
03270229 e8b2c3eaff
0327C64C 488b8188000000
0327C65B 83782004
0327C661 80782400
0326F0A0 4c8b4b60
0326F100 4c8b4b68
030D3011 e806281900
030D312D e8ea261900
030D3379 e89e241900
030DCCE7 e8308b1800
03275385 e89204ffff
03275549 e8ce02ffff
032756AB e86c01ffff
03275815 e80200ffff
03275943 e8d4fefeff
03275A86 e891fdfeff
03275BD6 e841fcfeff
03275CDF e838fbfeff
03275E08 e80ffafeff
03275F38 e8dff8feff
03276279 e89ef5feff
032830AD e86a27feff
""".strip().splitlines())}
LEAVES={0x008F96B0:(0x008F96B0,0x008F96B8),0x0326F16C:(0x0326F16C,0x0326F17E)}
CONSTRUCTOR_CALL_SITES=[int(x,16) for x in """030D3011 030D312D 030D3379 030DCCE7 03275385 03275549 032756AB 03275815 03275943 03275A86 03275BD6 03275CDF 03275E08 03275F38 03276279 032830AD""".split()]
CALLS={x:0x0326581C for x in CONSTRUCTOR_CALL_SITES}
CALLS.update({0x032701F2:0x0327C648,0x03270229:0x0311C5E0})
JUMPS={0x0326F179:0x0326EA44}
LEAS={0x03265852:0x03ADE428,0x03265867:0x03ADE520,0x008F96B0:0x03D19BD8}
POINTERS={0x03ADE4F8:0x008F96B0,0x03D19BD8:0x039407A8,0x039407A8:0x032701C4,0x039407B0:0x0326F16C,0x03940EE0:0x0326F0DC,0x03941408:0x0326F07C}

def audit(exe):
 pe=StrictPE(Path(exe))
 try:
  if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
  pins=dict(PINS);pins[0x008F96B0]='488d0521054203'
  cache={}
  for site,hexbytes in pins.items():
   data=bytes.fromhex(hexbytes)
   if pe.read(site,len(data),True)!=data:raise ValueError('ORIGINAL_OPCODE_DRIFT:'+hex(site))
   owner=pe.function(site) or next((v for v in LEAVES.values() if v[0]<=site<v[1]),None)
   if owner is None:raise ValueError('UNVERIFIED_FUNCTION_OWNER:'+hex(site))
   if owner not in cache:
    asm=pe.disasm(owner[0],owner[1]-owner[0])
    cache[owner]={int(m.group(1),16) for ln in asm.splitlines() if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',ln))}
   if site not in cache[owner]:raise ValueError('MID_INSTRUCTION:'+hex(site))
  for table,opcode in ((CALLS,0xe8),(JUMPS,0xe9)):
   for site,target in table.items():
    data=pe.read(site,5,True)
    if data[0]!=opcode or site+5+struct.unpack_from('<i',data,1)[0]!=target:raise ValueError('BRANCH_DRIFT:'+hex(site))
  for site,target in LEAS.items():
   data=pe.read(site,7,True)
   if data[:3]!=b'\x48\x8d\x05' or site+7+struct.unpack_from('<i',data,3)[0]!=target:raise ValueError('RIP_LEA_DRIFT:'+hex(site))
  for site,target in POINTERS.items():
   if struct.unpack('<Q',pe.read(site,8))[0]!=pe.base+target:raise ValueError('TYPE_POINTER_DRIFT:'+hex(site))
  return dict(schema='bsc.n1.third_handler_type_lineage.v1',sha256=pe.sha,grade='EXACT_EXE_STATIC',
   opcode_instruction_starts=len(pins),typed_pointer_slots=len(POINTERS),E8_edges=len(CALLS),E9_edges=len(JUMPS),RIP_LEA_edges=len(LEAS),
   constructor_callers=len(CONSTRUCTOR_CALL_SITES),type_chain='ctor 0x0326581C -> main vtable 0x03ADE428 +0xD0 -> 0x008F96B0 -> registry address 0x03D19BD8 -> 0x039407A8 -> task callback 0x032701C4',
   geometry_callback='0x039407B0 -> 0x0326F16C -> 0x0326EA44',
   initially_null_plus88=True,nonnull_plus88_source_proven=False,
   geometry_context_plus160_is_move_task_plus160_proven=False,
   move_slot_plus_a0_to_third_parent_plus88_proven=False,
   third_handler_same_as_factory_A_or_B=False,native_patch_authorized=False)
 finally:pe.close()

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.exe.resolve()==a.out.resolve():p.error('NEVER_OVERWRITE_EXE')
 result=audit(a.exe);a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('PASS',result['opcode_instruction_starts'],'opcode instruction starts,',result['constructor_callers'],'constructor E8 sites; NO PATCH')
