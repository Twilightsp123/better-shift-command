#!/usr/bin/env python3
"""R45: SHA-guarded, read-only proof of B2 packet vs buffered state16 task identity.

No game process access, no patch, no runtime Shift identity assertions.
This proof checks direct paths and typed vtables; indirect/re-entrant calls remain open.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
from audit_r35_group_transaction_20261017 import PE,disasm,branch_dest
from audit_r43_member_pending_goal_delta_20261018 import direct_callers

HERE=Path(__file__).resolve().parent
MANIFEST=HERE/'r45_b2_state16_provenance_pins_20261019.txt'
SHA='9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496'
SIZE=232531920
BASE=0x140000000
LEAF_SPAN=(0x02F648E4,0x02F6496B)
EXPECTED_GROUPS=13
EXPECTED_PINS=107
TABLES={
 (0x03912950,0x368):0x03070A48,
 (0x03912950,0x550):0x0306F594,
 (0x039199F8,0x08):0x0325E824,
 (0x039199F8,0x10):0x03263AF8,
 (0x03919B28,0x08):0x0325D9FC,
 (0x03919B28,0x10):0x03261688,
 (0x03AE22D0,0x08):0x0325E4B4,
 (0x03AE22D0,0x10):0x032621E0,
}
E8={
 0x0326AAD9:0x0326F210,0x0326AB19:0x02F775AC,
 0x0326F293:0x02F648E4,0x0326F2D6:0x02F648E4,
 0x03070A7B:0x02DC7E30,0x03070A94:0x02DB5AC4,
 0x03070AB3:0x02F647D0,0x03070ACD:0x03084618,
 0x03070BD2:0x02DB5A20,0x03070BF8:0x0324E2C8,
 0x03070C06:0x02DB5A20,0x03070C2D:0x0324D994,
 0x0324E2CF:0x03053630,0x0324D99B:0x03053630,
 0x0306F71F:0x02DB5A20,0x0306F733:0x0324DBAC,
 0x0324DBB6:0x03053630,0x0325E544:0x03065DB8,
 0x03261A77:0x03081D40,0x03261CAB:0x03081D40,
 0x03263D9F:0x03081D40,0x03081ED6:0x03164710,
}
JUMPS={
 0x03070A85:0x03070ABD,
 0x03070A8B:0x03070ABD,
 0x03070AB8:0x03070C32,
 0x03070B6D:0x03070BB9,
 0x03070BC9:0x03070BFF,
 0x03070BFD:0x03070C32,
}
# Positive, type-relevant, limited-scope instruction sites.
TEXT={
 ('b2_sender',0x0326ABAF):'call   QWORD PTR [rax+0x368]',
 ('packet_ctor_fixed_bit',0x02F64948):'or     cl,0x6',
 ('packet_ctor_fixed_bit',0x02F64966):'mov    BYTE PTR [r10+0x50],cl',
 ('member_receiver',0x03070A85):'jne    0x3070abd',
 ('member_receiver',0x03070A87):'test   BYTE PTR [rdx+0x50],0x20',
 ('member_receiver',0x03070A8B):'jne    0x3070abd',
 ('member_receiver',0x03070A99):'lea    rcx,[rdi+0x4a8]',
 ('member_receiver',0x03070AB8):'jmp    0x3070c32',
 ('member_receiver',0x03070B66):'call   QWORD PTR [r11+0x100]',
 ('member_receiver',0x03070B9C):'call   QWORD PTR [r11+0xe8]',
 ('member_receiver',0x03070BB9):'mov    eax,DWORD PTR [rbx+0x34]',
 ('member_receiver',0x03070BC1):'mov    ecx,0xd600',
 ('member_receiver',0x03070BCB):'lea    rcx,[rdi+0x328]',
 ('member_receiver',0x03070BD7):'lea    rcx,[rdi+0x330]',
 ('member_receiver',0x03070BFF):'lea    rcx,[rdi+0x328]',
 ('member_receiver',0x03070C0B):'lea    rcx,[rdi+0x330]',
 ('packet_special_action_ctor',0x0324E2DB):'mov    QWORD PTR [rcx],rdx',
 ('packet_special_action_ctor',0x0324E2DE):'mov    rax,QWORD PTR [r9]',
 ('packet_special_action_ctor',0x0324E2E1):'mov    QWORD PTR [rcx+0x38],rax',
 ('packet_special_action_ctor',0x0324E2E8):'mov    BYTE PTR [rcx+0x40],0x0',
 ('packet_generic_action_ctor',0x0324D9A7):'mov    QWORD PTR [rcx],rdx',
 ('packet_generic_action_ctor',0x0324D9AA):'mov    rax,QWORD PTR [r9]',
 ('packet_generic_action_ctor',0x0324D9AD):'mov    QWORD PTR [rcx+0x38],rax',
 ('packet_generic_action_ctor',0x0324D9B4):'mov    BYTE PTR [rcx+0x40],0x0',
 ('member_state16_virtual',0x0306F70B):'lea    rbp,[rbx+0x328]',
 ('member_state16_virtual',0x0306F712):'mov    DWORD PTR [rbx+0x324],0x10',
 ('state16_vector_task_ctor',0x0324DBC2):'mov    QWORD PTR [r10],rcx',
 ('state16_vector_task_ctor',0x0324DBC8):'mov    DWORD PTR [r10+0x38],eax',
 ('state16_vector_task_ctor',0x0324DBD0):'mov    DWORD PTR [r10+0x3c],eax',
 ('state16_vector_task_ctor',0x0324DBD8):'mov    DWORD PTR [r10+0x40],eax',
 ('state16_task_virtual_08',0x0325E50F):'lea    r8,[rdi+0x38]',
 ('state16_task_virtual_08',0x0325E513):'mov    rcx,QWORD PTR [rdi+0x8]',
 ('state16_task_virtual_08',0x0325E530):'lea    rdx,[rcx+0x1e0]',
 ('generic_action_virtual_10',0x03261A68):'mov    rcx,r10',
 ('generic_action_virtual_10',0x03261C65):'mov    rbx,QWORD PTR [rbx+0x8]',
 ('generic_action_virtual_10',0x03261C9B):'mov    rcx,rbx',
 ('special_action_virtual_10',0x03263D55):'mov    rbx,QWORD PTR [rbx+0x8]',
 ('special_action_virtual_10',0x03263D8A):'mov    rcx,rbx',
 ('member_state_restorer',0x03081EDB):'or     BYTE PTR [rdi+0x155],0x4',
 ('member_position_state_reset',0x03164776):'and    BYTE PTR [rdi+0x108],0xf5',
}

def classify_packet_mode(helper_nonzero,packet_50):
 """Branch predicate only; actual engine helper/Shift value is not inferred."""
 return 'inline_4a8' if not helper_nonzero and not (packet_50 & 0x20) else 'member_virtual_and_action_330'

def packet_action_type(kind):
 """Receiver's <=15 and bitset 0xd600 selection, not the whole motor state machine."""
 return 'packet_special' if 0<=kind<=15 and (0xd600 & (1<<kind)) else 'packet_generic'

def groups():
 out={};key=None
 for n,line in enumerate(MANIFEST.read_text('utf8').splitlines(),1):
  header=re.fullmatch(r'# (\w+) bounds=([0-9a-fA-F]+):([0-9a-fA-F]+) count=(\d+)',line)
  if header:
   key=header[1]
   if key in out:raise ValueError('DUPLICATE_GROUP')
   out[key]={'lo':int(header[2],16),'hi':int(header[3],16),'count':int(header[4]),'pins':{}}
   continue
  parts=line.split('#',1)[0].split()
  if not parts:continue
  if key is None or len(parts)!=2:raise ValueError('BAD_PIN_FORMAT:'+str(n))
  at=int(parts[0],16)
  if at in out[key]['pins']:raise ValueError('DUPLICATE_PIN:'+hex(at))
  out[key]['pins'][at]=bytes.fromhex(parts[1])
 if len(out)!=EXPECTED_GROUPS:raise ValueError('GROUP_COUNT_DRIFT')
 if sum(len(g['pins']) for g in out.values())!=EXPECTED_PINS:raise ValueError('PIN_COUNT_DRIFT')
 if len({site for g in out.values() for site in g['pins']})!=EXPECTED_PINS:
  raise ValueError('CROSS_GROUP_DUPLICATE')
 if any(len(g['pins'])!=g['count'] for g in out.values()):raise ValueError('GROUP_PIN_COUNT_DRIFT')
 return out

def audit(exe):
 exe=Path(exe)
 if not exe.is_file() or exe.stat().st_size!=SIZE:raise ValueError('EXE_MISSING_OR_SIZE_DRIFT')
 with exe.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
 if actual!=SHA:raise ValueError('EXE_SHA256_MISMATCH:'+actual)
 p=PE(exe)
 try:
  if p.base!=BASE:raise ValueError('IMAGEBASE_DRIFT')
  gs=groups();decoded={};raw={};owners=[]
  for name,g in gs.items():
   span=g['lo'],g['hi']
   if name=='packet_ctor_fixed_bit':
    if span!=LEAF_SPAN or p.owner(span[0]) is not None:
     raise ValueError('LEAF_OWNER_CHANGED')
   elif p.owner(span[0])!=span:
    raise ValueError('UNWIND_FUNCTION_OWNER_DRIFT:'+name)
   if not p.is_executable(span[0]):raise ValueError('NOT_EXECUTABLE:'+name)
   decoded[name]=disasm(p,*span)
   if name!='packet_ctor_fixed_bit':owners.append(span)
   for at,bytes_ in g['pins'].items():
    if not span[0]<=at<span[1] or at not in decoded[name]:
     raise ValueError('MID_INSTRUCTION:'+hex(at))
    if p.read(at,len(bytes_))!=bytes_:
     raise ValueError('OPCODE_DRIFT:'+hex(at))
    raw[at]=bytes_
  for (name,at),op in TEXT.items():
   if decoded[name].get(at)!=op:raise ValueError('REGISTER_OR_TYPE_DRIFT:'+name+':'+hex(at))
  for site,tgt in E8.items():
   b=raw.get(site,b'')
   if len(b)!=5 or b[0]!=0xe8 or site+5+struct.unpack_from('<i',b,1)[0]!=tgt:
    raise ValueError('E8_TARGET_DRIFT:'+hex(site))
  for site,tgt in JUMPS.items():
   if branch_dest(site,raw[site])!=tgt:raise ValueError('BRANCH_TARGET_DRIFT:'+hex(site))
  for (tbl,slot),tgt in TABLES.items():
   if struct.unpack('<Q',p.read(tbl+slot,8))[0]!=p.base+tgt:
    raise ValueError('VTABLE_SLOT_DRIFT:'+hex(tbl)+':'+hex(slot))
  callers=direct_callers(p,(0x0324DBAC,0x0306F594))
  if callers!={0x0324DBAC:(0x0306F733,),0x0306F594:()}:
   raise ValueError('STATE16_DIRECT_CALLER_INVENTORY_DRIFT:'+str(callers))
  # Same member has distinct task-owner and vtable identities.
  if not (0x03070BD2 < 0x03070BF8 < 0x03070BFD) or not (0x03070C06 < 0x03070C2D):
   raise ValueError('ACTION_REPLACEMENT_ORDER_DRIFT')
  if not (0x0306F712 < 0x0306F733 < 0x0325E544):
   raise ValueError('BUFFERED_TASK_ORDER_DRIFT')
  # B2 packet->member receiver and action methods provide no direct +0x550
  # call instruction. This is scoped and does not exclude indirect callbacks.
  scanned=['member_receiver','generic_action_virtual_10','special_action_virtual_10']
  bad=[]
  for name in scanned:
   for at,op in decoded[name].items():
    if op.startswith('call') and '+0x550]' in op:bad.append((name,hex(at),op))
  if bad:raise ValueError('DIRECT_MEMBER_STATE16_VIRTUAL_CALL_APPEARED:'+str(bad))
  # B2 packet constructor explicitly sets 0x06 | bit0 | bit4 (no bit0x20).
  # Two receiver branches are therefore determined by helper status here.
  for low in range(2):
   for high in range(2):
    flags=0x06|low|(high<<4)
    if flags&0x20:raise ValueError('B2_PACKET_BIT20_NOT_FIXED_ZERO')
    if classify_packet_mode(False,flags)!='inline_4a8':
     raise ValueError('MODE_ZERO_PATH_DRIFT')
    if classify_packet_mode(True,flags)!='member_virtual_and_action_330':
     raise ValueError('MODE_NONZERO_PATH_DRIFT')
  return {
   'schema':'bsc.n1.r45_b2_packet_vs_state16_task_provenance.v1',
   'proof':'EXACT_NEW_EXE_READ_ONLY_STATIC',
   'exe_sha256':actual,'exe_bytes':SIZE,'imagebase':hex(BASE),
   'verified_instruction_starts':len(raw),'verified_function_spans':len(owners),
   'verified_no_unwind_leaf_regions':1,
   'verified_direct_e8':len(E8),'verified_jump_edges':len(JUMPS),
   'verified_typed_vtable_slots':len(TABLES),
   'state16_buffer_task_constructor_direct_callers':[hex(x) for x in callers[0x0324DBAC]],
   'state16_member_method_direct_e8_callers':[hex(x) for x in callers[0x0306F594]],
   'B2_packet_mode0_path':'member+0x4a8 -> 0x02F647D0, jump out before member+0x330',
   'B2_packet_other_mode_path':'virtual+0x100/+0xe8; cleanup member+0x328 then install member+0x330 packet action',
   'packet_action_vtables':['0x039199F8','0x03919B28'],
   'buffered_state16_task_vtable':'0x03AE22D0',
   'packet_action_offset_38':'8-byte payload copied from action input, byte+0x40 then zeroed',
   'state16_task_offset_38':'three individual floats to +0x38/+0x3c/+0x40',
   'B2_action_state_reset':'packet action virtual+0x10 conditionally calls 0x03081D40; its own gated branch calls 0x03164710 clearing member+0x108 bit2/bit8 and restoring member+0x155 bit4',
   'direct_B2_packet_installs_R44_vector_task':False,
   'indirect_or_later_state16_install_excluded':False,
   'same_Shift_MOVE_instance_observed':False,
   'buffered_vector_live_goal_mismatch_observed':False,
   'motion_crowding_root_cause_proven':False,
   'gameplay_patch_authorized':False,
  }
 finally:p.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--exe',type=Path,required=True)
 ap.add_argument('--out',type=Path)
 args=ap.parse_args()
 if args.out and args.exe.resolve()==args.out.resolve():ap.error('FORBIDDEN_GAME_EXE_OVERWRITE')
 report=audit(args.exe)
 if args.out:
  args.out.parent.mkdir(parents=True,exist_ok=True)
  args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 print('R45_READ_ONLY_PASS',report['verified_instruction_starts'],'pins',report['verified_direct_e8'],'E8',report['verified_typed_vtable_slots'],'slots; NO GAMEPLAY PATCH')
if __name__=='__main__':main()
