#!/usr/bin/env python3
"""BSC R44: immutable read-only audit of member pending vs task-driven goal/delta updates.

This scans ONLY the exact new WH3 EXE and never attaches to the game or patches it.
Static reachability does NOT establish that a player's Shift MOVE hits any branch.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
from audit_r35_group_transaction_20261017 import PE,disasm,branch_dest
from audit_r43_member_pending_goal_delta_20261018 import direct_callers

DIR=Path(__file__).resolve().parent
PINS=DIR/'r44_member_task_pending_causality_pins_20261019.txt'
SHA='9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496'
SIZE=232531920
BASE=0x140000000
MEMBER_TABLE=0x03912950
TASK_TABLE=0x03AE22D0
TABLE={
 (MEMBER_TABLE,0x18):0x03086F04, (MEMBER_TABLE,0x20):0x030592BC,
 (MEMBER_TABLE,0x368):0x03070A48,(MEMBER_TABLE,0x470):0x03071DC8,
 (MEMBER_TABLE,0x550):0x0306F594,
 (TASK_TABLE,0x08):0x0325E4B4,(TASK_TABLE,0x10):0x032621E0,
}
CALLS={
 0x03053128:0x03051D98,
 0x0306F71F:0x02DB5A20,0x0306F733:0x0324DBAC,
 0x0324DBB6:0x03053630,
 0x03087013:0x03065DB8,0x03087322:0x03085F9C,
 0x03087349:0x03059BC8,0x03087351:0x0308D830,
 0x0325E544:0x03065DB8,0x03065EB2:0x03154974,
 0x0308D889:0x03091338,0x0308DA71:0x03065DB8,
 0x030728C1:0x03065DB8,
}
BRANCHES={
 0x030872CF:0x03087339,0x030872DA:0x0308731B,
 0x03087343:0x030873F0,
 0x03085FA9:0x03085FDA,0x03085FB3:0x03085FDA,
 0x03085FB9:0x03085FCE,
 0x0308D871:0x0308DA76,0x0308D883:0x0308DA76,
 0x0308D912:0x0308DA76,
}
DIRECT_EXPECTED={
 0x03065DB8:(0x030728C1,0x03087013,0x0308DA71,0x0325E544),
 0x03051D98:(0x03053128,),
 0x0324DBAC:(0x0306F733,),
}
COUNT=111
GROUP_COUNT=11

def manifest(path=PINS):
 groups={};which=None
 for line in Path(path).read_text('utf8').splitlines():
  m=re.fullmatch(r'# (\w+) bounds=([0-9a-fA-F]+):([0-9a-fA-F]+) count=(\d+)',line)
  if m:
   which=m[1];lo,hi=int(m[2],16),int(m[3],16)
   if which in groups:raise ValueError('DUPLICATE_GROUP')
   groups[which]=dict(lo=lo,hi=hi,count=int(m[4]),pins={})
   continue
  words=line.split('#',1)[0].split()
  if not words:continue
  if which is None or len(words)!=2:raise ValueError('BAD_PIN_ROW')
  at=int(words[0],16)
  if at in groups[which]['pins']:raise ValueError('DUPLICATE_PIN')
  groups[which]['pins'][at]=bytes.fromhex(words[1])
 if len(groups)!=GROUP_COUNT or sum(len(v['pins']) for v in groups.values())!=COUNT:
  raise ValueError('PIN_GROUP_COUNT_DRIFT')
 if any(len(v['pins'])!=v['count'] for v in groups.values()):raise ValueError('INCOMPLETE_PIN_GROUP')
 if len({at for v in groups.values() for at in v['pins']})!=COUNT:raise ValueError('CROSS_GROUP_PIN_DUPLICATE')
 return groups

def _must_decoded(decoded,group,at,expected):
 observed=decoded[group].get(at)
 if observed!=expected:raise ValueError(f'OBJECT_IDENTITY_OR_PHASE_DRIFT:{group}:{at:08X} {observed!r} != {expected!r}')

def audit(exe):
 exe=Path(exe)
 if not exe.is_file():raise ValueError('EXE_MISSING')
 if exe.stat().st_size!=SIZE:raise ValueError('EXE_SIZE_DRIFT')
 with exe.open('rb') as handle:actual_sha=hashlib.file_digest(handle,'sha256').hexdigest()
 if actual_sha!=SHA:raise ValueError('EXE_SHA256_MISMATCH:'+actual_sha)
 p=PE(exe)
 try:
  if p.base!=BASE:raise ValueError('IMAGEBASE_DRIFT')
  records=manifest();pins={};decoded={}
  for name,g in records.items():
   lo,hi=g['lo'],g['hi']
   if not p.is_executable(lo):raise ValueError('FUNCTION_NOT_EXECUTABLE:'+name)
   owner=p.owner(lo)
   if name=='member_task_base_leaf':
    if owner is not None or (lo,hi)!=(0x03053630,0x03053683):
     raise ValueError('LEAF_SPAN_DRIFT')
   elif owner!=(lo,hi):raise ValueError('UNWIND_OWNER_DRIFT:'+name)
   ins=disasm(p,lo,hi);decoded[name]=ins
   for at,raw in g['pins'].items():
    if not(lo<=at<hi) or at not in ins:raise ValueError('MID_INSTRUCTION:'+hex(at))
    if p.read(at,len(raw))!=raw:raise ValueError('INSTRUCTION_DRIFT:'+hex(at))
    pins[at]=raw
  for at,tgt in CALLS.items():
   raw=pins.get(at,b'')
   if len(raw)!=5 or raw[0]!=0xe8 or at+5+struct.unpack_from('<i',raw,1)[0]!=tgt:
    raise ValueError('DIRECT_CALL_TARGET_DRIFT:'+hex(at))
  for at,tgt in BRANCHES.items():
   if branch_dest(at,pins[at])!=tgt:raise ValueError('BRANCH_TARGET_DRIFT:'+hex(at))
  for (table,slot),tgt in TABLE.items():
   if struct.unpack('<Q',p.read(table+slot,8))[0]!=BASE+tgt:
    raise ValueError('VTABLE_IDENTITY_DRIFT:'+hex(table)+':'+hex(slot))
  # The saved member reference from action.base+0 is demonstrated by a
  # typed constructor and a typed task constructor -- not just same offsets.
  positive={
   ('member_ctor',0x03052D20):'lea    rax,[rip+0x8bfc29]        # 0x3912950',
   ('member_ctor',0x03052E7B):'lea    rsi,[rbx+0x328]',
   ('member_ctor',0x03052EEE):'mov    QWORD PTR [rsi],rbx',
   ('member_ctor',0x0305306F):'lea    rcx,[rbx+0x8d8]',
   ('member_state16_method',0x0306F70B):'lea    rbp,[rbx+0x328]',
   ('member_state16_method',0x0306F712):'mov    DWORD PTR [rbx+0x324],0x10',
   ('member_state16_method',0x0306F724):'lea    rcx,[rbp+0x8]',
   ('member_state16_method',0x0306F730):'mov    rdx,rbp',
   ('member_task_base_leaf',0x0305363D):'mov    rax,QWORD PTR [rdx]',
   ('member_task_base_leaf',0x03053640):'mov    QWORD PTR [rcx+0x8],rax',
   ('member_task_base_leaf',0x03053650):'mov    BYTE PTR [rdx+0x154],0x1',
   ('member_task_ctor',0x0324DBBB):'lea    rcx,[rip+0x89470e]        # 0x3ae22d0',
   ('member_task_ctor',0x0324DBC2):'mov    QWORD PTR [r10],rcx',
   ('member_task_ctor',0x0324DBC5):'mov    eax,DWORD PTR [r9]',
   ('member_task_ctor',0x0324DBC8):'mov    DWORD PTR [r10+0x38],eax',
   ('member_task_ctor',0x0324DBCC):'mov    eax,DWORD PTR [r9+0x4]',
   ('member_task_ctor',0x0324DBD0):'mov    DWORD PTR [r10+0x3c],eax',
   ('member_task_ctor',0x0324DBD4):'mov    eax,DWORD PTR [r9+0x8]',
   ('member_task_ctor',0x0324DBD8):'mov    DWORD PTR [r10+0x40],eax',
   ('member_tick',0x03086F2C):'mov    rdi,rcx',
   ('member_tick',0x03086FD2):'cmp    BYTE PTR [rdi+0x8d8],r14b',
   ('member_tick',0x03086FE5):'lea    r8,[rdi+0x8dc]',
   ('member_tick',0x03086FF1):'lea    rdx,[rdi+0x8e8]',
   ('member_tick',0x0308700C):'mov    BYTE PTR [rdi+0x8d8],r14b',
   ('member_tick',0x030872CD):'test   al,0x4',
   ('member_tick',0x030872D1):'mov    eax,DWORD PTR [rdi+0x324]',
   ('member_tick',0x0308731B):'lea    rcx,[rdi+0x328]',
   ('member_task_scheduler',0x03085FA2):'cmp    BYTE PTR [rcx+0x154],0x1',
   ('member_task_scheduler',0x03085FAB):'lea    rbx,[rcx+0x8]',
   ('member_task_scheduler',0x03085FB5):'cmp    BYTE PTR [rbx+0x18],0x0',
   ('member_task_scheduler',0x03085FC1):'call   QWORD PTR [rax+0x8]',
   ('member_task_scheduler',0x03085FC8):'mov    BYTE PTR [rbx+0x18],0x1',
   ('member_task_scheduler',0x03085FD4):'call   QWORD PTR [rax+0x10]',
   ('member_task_virtual_08',0x0325E50F):'lea    r8,[rdi+0x38]',
   ('member_task_virtual_08',0x0325E513):'mov    rcx,QWORD PTR [rdi+0x8]',
   ('member_task_virtual_08',0x0325E530):'lea    rdx,[rcx+0x1e0]',
   ('goal_delta_install',0x03065E9E):'movups XMMWORD PTR [rbx+0x1e0],xmm0',
   ('goal_delta_install',0x03065EAA):'movsd  QWORD PTR [rbx+0x1f0],xmm1',
   ('member_conditional_tick',0x0308D839):'cmp    QWORD PTR [rcx+0x30],0x0',
   ('member_conditional_tick',0x0308D857):'cmp    QWORD PTR [rcx+0x2e8],0x0',
   ('member_conditional_tick',0x0308D865):'mov    eax,DWORD PTR [rcx+0x26c]',
   ('member_conditional_tick',0x0308DA23):'lea    rdx,[rbx+0x1e0]',
   ('member_conditional_tick',0x0308DA33):'lea    r8,[rsp+0x40]',
   ('member_virtual_470',0x03071DE9):'mov    r14,rcx',
   ('member_virtual_470',0x03072893):'lea    rdx,[r14+0x1e0]',
   ('member_virtual_470',0x030728A6):'mov    rcx,r14',
  }
  for (group,at),text in positive.items():_must_decoded(decoded,group,at,text)
  direct=direct_callers(p,DIRECT_EXPECTED.keys())
  if direct!=DIRECT_EXPECTED:
   raise ValueError('DIRECT_CALLER_INVENTORY_DRIFT:'+str(direct))
  # Boundaries: in the selected, object-typed member functions, all explicit
  # member+0x8d8 accesses are initialization and consumption/clear. This is
  # NOT a PE-wide no-writer proof: aliases, SIMD block copy and virtuals remain.
  field_access=[]
  for group in ('member_ctor','member_tick','member_state16_method',
                'member_task_scheduler','member_conditional_tick','member_virtual_470'):
   for at,code in decoded[group].items():
    if '+0x8d8]' in code and re.search(r'\[(?:rdi|rbx|rsi|r14|rcx|r8|rdx)\+0x8d8\]',code):
     field_access.append((group,at,code))
  if sorted((name,at) for name,at,_ in field_access)!=sorted([
      ('member_ctor',0x0305306F),('member_tick',0x03086FD2),
      ('member_tick',0x0308700C),('member_tick',0x03087018)]):
   raise ValueError('TYPED_DIRECT_8D8_REFERENCE_DRIFT:'+str(field_access))
  if not(0x0306F712<0x0306F733) or not (0x0308731B<0x03087322<0x03087327):
   raise ValueError('STATE_TASK_PHASE_DRIFT')
  if not (0x03085FC1<0x03085FC8<0x03085FD4):
   raise ValueError('INITIAL_TASK_VIRTUAL_ORDER_DRIFT')
  if not (0x03087349<0x03087351):raise ValueError('STEERING_FOLLOWUP_ORDER_DRIFT')
  return {
   'schema':'bsc.n1.r44_member_task_vs_pending_state.v1',
   'proof':'EXACT_NEW_EXE_READ_ONLY_NATIVE_STATIC',
   'exe_sha256':actual_sha,'exe_bytes':SIZE,'imagebase':hex(BASE),
   'verified_full_opcodes':COUNT,'verified_function_spans':GROUP_COUNT,
   'verified_direct_calls':len(CALLS),'verified_conditional_edges':len(BRANCHES),
   'verified_typed_vtable_slots':len(TABLE),
   'all_direct_e8_to_goal_delta_handler':{hex(k):[hex(x) for x in v] for k,v in direct.items()},
   'member_pending_direct_references':[
      {'function':name,'rva':hex(at),'opcode':code} for name,at,code in field_access],
   'typed_member_task_path':'member+0x328 owner -> member+0x330 subtask; member +0x550 state 16 installs 0x03AE22D0; tick +0x08 -> 0x0325E4B4 -> 0x03065DB8 with member+0x1E0 and task+0x38',
   'buffered_vector_live_goal_temporal_seam':'constructor copies input+0,+4,+8 to task+0x38/+0x3c/+0x40, but the task virtual+8 later passes &member+0x1e0 as goal and &task+0x38 as input vector',
   'initial_task_dispatch_order':'if active/phase gate then virtual+0x08, mark task+0x18=1, and optionally virtual+0x10; per-member stages',
   'alternate_goal_delta_caller':'member Tick 0x03087349 steering, 0x03087351 0x0308D830; guarded rare/conditional path can call 0x03065DB8 without +0x8D8',
   'member_virtual_goal_caller':'member vtable+0x470=0x03071DC8 conditionally calls 0x03065DB8 without +0x8D8',
   'pending_record_is_required_for_all_goal_updates':False,
   'pending_record_producer_identified':False,
   'group_or_route_epoch_mismatch_proven':False,
   'Shift_move_reaches_this_specific_task_proven':False,
   'root_cause_proven':False,
   'per_member_physical_crowding_causality_proven':False,
   'gameplay_patch_authorized':False,
  }
 finally:p.close()

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--exe',type=Path,required=True)
 parser.add_argument('--out',type=Path)
 args=parser.parse_args()
 if args.out and args.out.resolve()==args.exe.resolve():parser.error('GAME_EXE_OVERWRITE_FORBIDDEN')
 result=audit(args.exe)
 if args.out:
  args.out.parent.mkdir(parents=True,exist_ok=True)
  args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
 print('R44_STATIC_PASS',result['verified_full_opcodes'],'opcodes',result['verified_direct_calls'],'E8',result['verified_typed_vtable_slots'],'vtable; NO PATCH')
if __name__=='__main__':main()
