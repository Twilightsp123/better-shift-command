#!/usr/bin/env python3
"""BSC R38: exact-SHA, read-only native packet heading and member motion gates.

Scopes: B2 sender's member packet construction and transformation, typed member
constructor field+0x984 source, receiver inline/virtual dispatch, member Tick.
This is NOT a Shift defect causality proof or an authorized gameplay patch.
"""
import argparse, hashlib, json, re, struct
from pathlib import Path
from audit_r35_group_transaction_20261017 import PE, disasm, branch_dest, SHA, IMAGE_BASE, SIZED
HERE=Path(__file__).resolve().parent
PINS=HERE/'r38_packet_heading_motion_pins_20261018.txt'
MEMBER_TABLE=0x03912950
TASK_TABLE_A=0x03919B28
TASK_TABLE_B=0x039199F8
EXPECTED_COUNTS={'B_sender':26,'packet_kind_preparer':12,'packet_ctor_leaf':37,
 'packet_heading_adapter':16,'member_heading_adjust':29,'member_receiver':36,
 'member_constructor':22,'member_Tick':18,'inline_action_Tick':22,
 'constructor_action_kind_A':11,'constructor_action_kind_B':11,
 'member_world_target':9,'position_simple':6,'position_complex':4}
# Concrete direct E8 edges; E8 relative displacements must be verified, never
# replaced by a naive global RVA relocation offset.
E8={
 0x0326AAD9:0x0326F210,0x0326AB19:0x02F775AC,
 0x0326F253:0x030DE670,0x0326F293:0x02F648E4,0x0326F2D6:0x02F648E4,
 0x02F775CE:0x030844C8,0x03084511:0x004EDA50,
 0x03070A7B:0x02DC7E30,0x03070A94:0x02DB5AC4,
 0x03070AB3:0x02F647D0,0x03070ACD:0x03084618,
 0x03070B54:0x0312214C,0x03070B6F:0x0312214C,
 0x03070BF8:0x0324E2C8,0x03070C2D:0x0324D994,
 0x03052CA0:0x030F31D8,0x03053231:0x004EDA50,
 0x03087322:0x03085F9C,0x03087349:0x03059BC8,
 0x0324D99B:0x03053630,0x0324E2CF:0x03053630,
 0x03084638:0x030846E0,0x030846C3:0x0310D064,
}
BRANCH={
 0x02F775BD:0x02F775D9,0x030844E2:0x0308451E,
 0x03070A85:0x03070ABD,0x03070A8B:0x03070ABD,
 0x03070B52:0x03070B6F,0x030872CF:0x03087339,
 0x030872DA:0x0308731B,0x030872DF:0x0308731B,
 0x03087343:0x030873F0,
}
VIRTUAL={
 (MEMBER_TABLE,0x368):0x03070A48,
 (MEMBER_TABLE,0x100):0x030785AC,
 (MEMBER_TABLE,0xE8):0x03078268,
 (TASK_TABLE_A,0x8):0x0325D9FC,
 (TASK_TABLE_A,0x10):0x03261688,
 (TASK_TABLE_B,0x8):0x0325E824,
 (TASK_TABLE_B,0x10):0x03263AF8,
}
# Short complete-code landmarks, verified against objdump and full instruction.
ASM={
 0x02F64926:'and    al,0x1',
 0x02F64931:'and    cl,0x1',
 0x02F6493A:'shl    cl,0x4',
 0x02F64948:'or     cl,0x6',
 0x02F6494B:'and    al,0xfd',
 0x02F64951:'or     al,0x1',
 0x02F64957:'mov    BYTE PTR [r10+0x51],al',
 0x02F64966:'mov    BYTE PTR [r10+0x50],cl',
 0x0326F298:'or     BYTE PTR [rsi+0x50],0x8',
 0x0326AB1E:'mov    al,BYTE PTR [rbp+0x27]',
 0x0326AB21:'mov    cl,BYTE PTR [r15+0x10]',
 0x0326AB28:'xor    cl,al',
 0x0326AB2A:'and    cl,0x40',
 0x0326AB2F:'mov    BYTE PTR [rbp+0x27],al',
 0x02F775B2:'or     BYTE PTR [rcx+0x51],0x2',
 0x02F775B9:'test   BYTE PTR [rcx+0x50],0x2',
 0x02F775D6:'mov    WORD PTR [rbx],cx',
 0x030844D2:'mov    rax,QWORD PTR [rcx+0x2e8]',
 0x030844E4:'movss  xmm1,DWORD PTR [rcx+0x984]',
 0x030844EC:'mov    eax,DWORD PTR [rax+0x36cc]',
 0x03084500:'and    ecx,0x4000',
 0x03084516:'add    ax,WORD PTR [rdi]',
 0x0308451E:'movzx  eax,WORD PTR [r8]',
 0x03053258:'movss  xmm0,DWORD PTR [rax+0x90c]',
 0x030532BE:'movss  DWORD PTR [rbx+0x984],xmm0',
 0x03070A87:'test   BYTE PTR [rdx+0x50],0x20',
 0x03070ABD:'test   BYTE PTR [rdx+0x51],0x2',
 0x03070B2F:'mov    eax,DWORD PTR [rdi+0x104]',
 0x03070B66:'call   QWORD PTR [r11+0x100]',
 0x03070B9C:'call   QWORD PTR [r11+0xe8]',
 0x03070BC1:'mov    ecx,0xd600',
 0x03070BC6:'bt     ecx,eax',
 0x03070BF8:'call   0x324e2c8',
 0x03070C2D:'call   0x324d994',
 0x030872CD:'test   al,0x4',
 0x030872D1:'mov    eax,DWORD PTR [rdi+0x324]',
 0x0308731B:'lea    rcx,[rdi+0x328]',
 0x0308733C:'cmp    QWORD PTR [rdi+0xb20],r14',
 0x03087349:'call   0x3059bc8',
 0x03085FA2:'cmp    BYTE PTR [rcx+0x154],0x1',
 0x03085FAB:'lea    rbx,[rcx+0x8]',
 0x03085FC1:'call   QWORD PTR [rax+0x8]',
 0x03085FD4:'call   QWORD PTR [rax+0x10]',
}

def manifest():
 groups={};name=None
 for line in PINS.read_text('utf-8').splitlines():
  hdr=re.match(r'^# (\w+) bounds=([0-9a-fA-F]+):([0-9a-fA-F]+)',line)
  if hdr:
   name=hdr[1]; lo=int(hdr[2],16);hi=int(hdr[3],16)
   if name in groups or lo>=hi:raise ValueError('INVALID_PIN_GROUP')
   groups[name]=((lo,hi),{});continue
  cols=line.split('#',1)[0].split()
  if not cols:continue
  if len(cols)!=2 or name is None:raise ValueError('BAD_PIN_ROW')
  at=int(cols[0],16)
  if at in groups[name][1]:raise ValueError('DUPLICATE_PIN')
  groups[name][1][at]=bytes.fromhex(cols[1])
 if set(groups)!=set(EXPECTED_COUNTS):raise ValueError('GROUP_DRIFT')
 for name,n in EXPECTED_COUNTS.items():
  if len(groups[name][1])!=n:raise ValueError(f'PIN_COUNT_DRIFT:{name}:{len(groups[name][1])}!={n}')
 return groups

def packet_flag50(b0, b4, special=False, sender_b6=False):
 """Small *local* expression model of the audited B2 packet writers only."""
 flags=0x06 | (1 if b0 else 0) | (0x10 if b4 else 0)
 if special:flags|=0x08
 if sender_b6:flags|=0x40
 return flags

def receiver_kind(kind):
 return 'kind_B_vtable_39199f8' if 0<=kind<=15 and bool(0xd600 & (1<<kind)) else 'kind_A_vtable_3919b28'

def receiver_phase(mode_nonzero,member_state_104):
 if not mode_nonzero:return 'inline_task_4a8'
 return 'member_virtual_100' if member_state_104 in (1,2) else 'member_virtual_e8'

def tick_phase(flags108,state324,ref_b20_is_null=True):
 if flags108 & 0x8:return 'member_other_virtual_498'
 if flags108 & 0x4:
  return 'inline_action_328' if state324 in (4,16) else 'another_member_state'
 return 'steering_3059bc8' if ref_b20_is_null else 'member_other_virtual_490'

def audit(exe):
 pe=PE(exe)
 try:
  if pe.base!=IMAGE_BASE or len(pe.d)!=SIZED:raise ValueError('WRONG_EXE_PE_LAYOUT')
  with Path(exe).open('rb') as fh: actual_sha=hashlib.file_digest(fh,'sha256').hexdigest()
  if actual_sha!=SHA:raise ValueError('EXE_SHA256_MISMATCH')
  groups=manifest();all_pins={};decodes={};owners=set()
  for name,(bounds,pins) in groups.items():
   lo,hi=bounds
   if not pe.is_executable(lo):raise ValueError('PIN_OUTSIDE_CODE:'+name)
   if name=='packet_ctor_leaf':
    if pe.owner(lo) is not None:raise ValueError('LEAF_PDATA_DRIFT')
    if pe.read(hi-1,1)!=b'\xc3':raise ValueError('LEAF_RET_DRIFT')
   else:
    if pe.owner(lo)!=bounds:raise ValueError('UNWIND_FUNCTION_DRIFT:'+name)
    owners.add(bounds)
   asm=disasm(pe,lo,hi);decodes[name]=asm
   for at,raw in pins.items():
    if not lo<=at<hi or at not in asm:raise ValueError('MID_INSTRUCTION:'+hex(at))
    if pe.read(at,len(raw))!=raw:raise ValueError('BYTE_DRIFT:'+hex(at))
    if at in all_pins:raise ValueError('DUPLICATE_PIN_SITE')
    all_pins[at]=raw
  for at,to in E8.items():
   b=all_pins.get(at)
   if b is None or len(b)!=5 or b[0]!=0xe8 or at+5+struct.unpack_from('<i',b,1)[0]!=to:
    raise ValueError('E8_TARGET_DRIFT:'+hex(at))
  for at,to in BRANCH.items():
   if at not in all_pins or branch_dest(at,all_pins[at])!=to:
    raise ValueError('BRANCH_TARGET_DRIFT:'+hex(at))
  index={at:txt for d in decodes.values() for at,txt in d.items()}
  for at,txt in ASM.items():
   if index.get(at)!=txt:raise ValueError('SEMANTIC_INSTRUCTION_DRIFT:'+hex(at)+':'+str(index.get(at)))
  for (vtable,slot),func in VIRTUAL.items():
   ptr=struct.unpack('<Q',pe.read(vtable+slot,8))[0]
   if ptr!=IMAGE_BASE+func:raise ValueError('VTABLE_SLOT_DRIFT:'+hex(vtable)+':'+hex(slot))
  # Strong member type: constructor installs the vtable containing receiver and
  # both direct-geometry virtuals, not merely a same-offset coincidence.
  constructor=decodes['member_constructor']
  if '0x3912950' not in constructor[0x03052D20].lower() or constructor[0x03052D34]!='mov    QWORD PTR [rbx],rax':
   raise ValueError('MEMBER_CTOR_TYPE_DRIFT')
  for ctor,name,vtbl in ((0x0324D994,'constructor_action_kind_A',TASK_TABLE_A),(0x0324E2C8,'constructor_action_kind_B',TASK_TABLE_B)):
   lines='\n'.join(decodes[name].values()).lower()
   if hex(vtbl) not in lines:raise ValueError('ACTION_VTABLE_CONSTRUCTOR_DRIFT:'+name)
  # Full constructor core must preserve the packet+0x50 bit5==0 invariant.
  # The R38 sender only overwrites bit6; wrapper's optional OR is bit3.
  if any(packet_flag50(x,y,z,w)&0x20 for x in (False,True) for y in (False,True)
         for z in (False,True) for w in (False,True)):
   raise ValueError('PACKET_BIT20_MODEL_INVARIANT_BROKEN')
  # The member field+0x984 uses a typed member constructor store and a true
  # member+0x2e8-gated *read* in heading modifier; not a route generation id.
  if struct.unpack('<f',pe.read(0x0392211C,4))[0]!=0.5:
   raise ValueError('HEADING_HALF_CONSTANT_CHANGED')
  if not all(k in decodes['inline_action_Tick'] for k in (0x03085FC1,0x03085FD4)):
   raise ValueError('INLINE_ACTION_VTABLE_DISPATCH_CHANGED')
  return {
   'schema':'bsc.n1.r38_native_packet_heading_member_action_gates.v1',
   'exe_sha256':actual_sha,'exe_bytes':len(pe.d),'pe_imagebase':hex(pe.base),
   'verified_opcode_starts':len(all_pins),'verified_e8':len(E8),
   'verified_control_transfers':len(BRANCH),'verified_vtable_slots':len(VIRTUAL),
   'verified_unwind_functions':len(owners),'verified_leaf_functions':1,
   'B2_packet_flag50_bit20_always_clear_in_verified_sender':True,
   'B2_packet_flag50_bit2_always_set':True,
   'B2_packet_flag51_bit2_set_per_member':True,
   'B2_member_heading_adjust':'0x0326AB19 -> 0x02F775AC -> 0x030844C8; when member+0x2E8 and related +0x36CC == 0, base heading + AngleConvert(0x4000 * (member+0x984 - 0.5))',
   'typed_member_constructor':'0x03052BA8 vtable=0x03912950, writes member+0x984 at 0x030532BE from Group+0x90C or per-unit RNG; not proven a dynamic Shift route counter',
   'receiver_mode_gate':'with B2 packet+0x50 bit20=0, mode helper zero uses member+0x4A8 inline task; nonzero enters per-member virtual by member+0x104',
   'receiver_packet_kind_task_table':'packet+0x34 bits 9,10,12,14,15 use 0x039199F8 class; other kinds use 0x03919B28',
   'member_tick_gate':'member+0x108 bit4 with state+0x324 in (4,16) -> member+0x328 action Tick; bit4 clear and member+0xB20 null -> 0x03059BC8 steering',
   'same_move_member_heading_causality_proven':False,
   'member_field_984_dynamic_rewritten_during_shift_proven':False,
   'true_final_physical_velocity_writer_identified':False,
   'shift_crowding_root_cause_proven':False,
   'native_gameplay_patch_authorized':False,
  }
 finally:pe.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--exe',type=Path,required=True)
 ap.add_argument('--out',type=Path)
 args=ap.parse_args()
 if args.out and args.out.resolve()==args.exe.resolve():ap.error('CANNOT_OVERWRITE_GAME_EXE')
 result=audit(args.exe)
 if args.out:
  args.out.parent.mkdir(parents=True,exist_ok=True)
  args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
 print('R38_STATIC_PASS',result['verified_opcode_starts'],'pinned opcodes',result['verified_e8'],'calls',result['verified_control_transfers'],'branches',result['verified_vtable_slots'],'vtable; NO PATCH')

if __name__=='__main__':main()
