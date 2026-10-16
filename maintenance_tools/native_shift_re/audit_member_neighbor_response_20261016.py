#!/usr/bin/env python3
"""Fixed WH3 original: member neighbour candidates -> guarded pair response.

SHA-pinned, read-only; virtual response's effect on velocity is NOT proven.
"""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA
MANIFEST=Path(__file__).with_name('member_neighbor_response_pins_20261016.txt')
E8={
0x030822F9:0x03054B84,0x03054DB3:0x03062988,
0x03054DEC:0x030765B0,0x03054DF7:0x03068B98,
0x03054F62:0x0305BEEC,0x03055029:0x0311CED4,
0x03055647:0x0324EB24,0x0305566A:0x0324E9DC,
0x03055688:0x0324E814,0x030556A1:0x0324EE00,
0x030556CA:0x0306E304,0x030557BC:0x030800C4,
0x03062A90:0x03062688,0x03062AFF:0x03062688,
0x03062C05:0x01325434,0x03062850:0x03068B98,
0x03062933:0x01325434,0x03082301:0x03088808}
JCC={
0x03054DCF:0x03054F71,0x03054ED3:0x03054EDF,
0x03054F37:0x03054DDE,0x03055137:0x03055161,
0x03062857:0x03062938,0x030628A3:0x030628AA,
0x030628AD:0x03062938,0x03062C11:0x03062B36}
REQUIRED={
0x03054D7B:'488d15563f2e01',0x03054DDE:'488b0dfb3e2e01',
0x03054DE8:'488b0cc1',0x03054E10:'488b8f80000000',
0x03054E17:'48398b80000000',0x03054F26:'488bf3',
0x030557BC:'e803a90200',0x0308024D:'498d8dd8010000',
0x03080257:'ff5010',0x030628A5:'f6c101',
0x030628AA:'f6c102',0x03062B36:'4c8b27'}
RESPONSES={
0x03055647:0x0324EB24,0x0305566A:0x0324E9DC,
0x03055688:0x0324E814,0x030556A1:0x0324EE00,
0x030557BC:0x030800C4}
def pins():
 d={}
 for line in MANIFEST.read_text('utf8').splitlines():
  words=line.split('#',1)[0].split()
  if not words:continue
  if len(words)!=2:raise ValueError('INVALID_ROW')
  at=int(words[0],16)
  if at in d:raise ValueError('DUPLICATE_PIN')
  d[at]=bytes.fromhex(words[1])
 if len(d)!=122:raise ValueError('PIN_COUNT_DRIFT')
 for at,raw in REQUIRED.items():
  if d[at]!=bytes.fromhex(raw):raise ValueError('FIELD_TYPE_DRIFT:'+hex(at))
 return d
def affiliation_gate(apply_filter,same_affiliation,current_flags,other_flags):
 """Bit filter at 0x0306288D..0x030628AD ONLY; not all native gates."""
 if not apply_filter:return True
 bits=current_flags&other_flags
 return bool(bits&(1 if same_affiliation else 2))
def jump_target(at,op):
 if len(op)==2 and 0x70<=op[0]<=0x7f:
  return at+2+struct.unpack_from('<b',op,1)[0]
 if len(op)==6 and op[0]==0x0f and 0x80<=op[1]<=0x8f:
  return at+6+struct.unpack_from('<i',op,2)[0]
 raise ValueError('BAD_CONDITIONAL_JUMP:'+hex(at))
def audit(exe):
 pe=OriginalEXE(Path(exe))
 try:
  if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
  entries=pins();owner_cache={}
  for at,raw in entries.items():
   if pe.section(at)!='.00cfg' or pe.read(at,len(raw))!=raw:
    raise ValueError('OPCODE_DRIFT:'+hex(at))
   owner=pe.owner(at)
   if owner is None:raise ValueError('OWNER_UNVERIFIED:'+hex(at))
   span=owner[:2]
   if span not in owner_cache:owner_cache[span]=pe.starts_in(*span)
   if at not in owner_cache[span]:raise ValueError('MID_INSTRUCTION:'+hex(at))
  for at,dest in E8.items():
   op=pe.read(at,5)
   if op[0]!=0xe8 or at+5+struct.unpack_from('<i',op,1)[0]!=dest:
    raise ValueError('E8_TARGET_DRIFT:'+hex(at))
  for at,dest in JCC.items():
   if jump_target(at,entries[at])!=dest:raise ValueError('JCC_TARGET_DRIFT:'+hex(at))
  return {
   'schema':'bsc.n1.member_neighbour_pair_response.v1',
   'proof':'EXACT_ORIGINAL_EXE_STATIC',
   'sha256':pe.sha,'verified_instruction_starts':len(entries),
   'verified_e8':len(E8),'verified_jcc':len(JCC),
   'verified_unwind_functions':len(owner_cache),
   'member_tick':'0x030822F9 -> 0x03054B84',
   'candidate_collection':'0x03054DB3 -> 0x03062988 -> 0x03062688; output candidate vector at RVA 0x04338CD8',
   'candidate_filter':'0x0306288D..0x030628AD uses bit1/bit2 for same/different affiliation reference',
   'selection':'0x03054DEC resolves object; 0x03054DF7 checks candidate; member+0x80 affiliation, +0x74 priority, positions and current movement; 0x03054F26 saves selected candidate in RSI',
   'world_goal_consumed':'0x03055029 -> 0x0311CED4, conditional direction calculation',
   'conditional_response_calls':[hex(x) for x in RESPONSES],
   'pair_response':'0x030557BC -> 0x030800C4 self RCX, candidate R8; builds per-pair response and calls virtual+0x10 on object at input-context+0x1D8',
   'member_target_directly_modified_by_pair_dispatch_proven':False,
   'pair_response_virtual_target_typed_proven':False,
   'physical_shift_crowding_cause_proven':False,'gameplay_patch_authorized':False}
 finally:pe.close()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True);p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():p.error('EXE_OVERWRITE_FORBIDDEN')
 v=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n','utf8')
 print('PASS',v['verified_instruction_starts'],'opcodes',v['verified_e8'],'E8',v['verified_jcc'],'JCC; NO PATCH')
if __name__=='__main__':main()
