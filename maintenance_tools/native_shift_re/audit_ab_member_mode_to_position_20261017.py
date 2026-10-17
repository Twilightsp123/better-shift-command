#!/usr/bin/env python3
"""Read-only original WH3: Group A/B -> member packet receiver -> typed position."""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA,IMAGEBASE
PINS=Path(__file__).with_name('ab_member_mode_pins_20261017.txt')
MEMBER_VTABLE=0x0390D4F8
VTABLE={0x368:0x0306B9F0,0x100:0x03073568,0xe8:0x03073224}
CALLS={0x02F56404:0x03279E40,0x03279E62:0x02DC2E04,
0x03279EB3:0x030D554C,0x03279ED8:0x03263AB0,
0x0306BA23:0x02DC2E04,0x0306BA5B:0x02F5F7C8,
0x0307328B:0x0315EC98,0x03073571:0x0315F4E0,
0x0307358A:0x03078B1C}
JCC={0x03279E69:0x03279EBA,0x0306BA33:0x0306BA65,
0x0306BA2D:0x0306BA65,0x0306BAFA:0x0306BB17,
0x0306BA60:0x0306BBDA}
FIELDS={0x030D5509:'41b001',0x03265D39:'4533c0',
0x0306BA0F:'458af0',0x0306BB0B:'458ace',0x0306BB29:'4488742420',
0x0306BB0E:'41ff9300010000',0x0306BB44:'41ff93e8000000',
0x03073271:'8a442460',0x03073284:'88442420',
0x0315F52C:'f20f118788000000',0x0315F53E:'898790000000',
0x0315F311:'f20f118e88000000',0x0315F327:'f20f118688000000',
0x0315F33F:'898690000000',
0x0315F54A:'24f7',0x0315F553:'0c02',0x0315F555:'888708010000',
0x0315F34B:'24f7',0x0315F354:'0c02',0x0315F356:'888608010000'}

def inventory():
 out={}
 for no,line in enumerate(PINS.read_text('utf8').splitlines(),1):
  a=line.split('#',1)[0].split()
  if not a:continue
  if len(a)!=2:raise ValueError('INVALID_PIN_ROW:'+str(no))
  at=int(a[0],16)
  if at in out:raise ValueError('DUPLICATE_PIN')
  out[at]=bytes.fromhex(a[1])
 if len(out)!=88:raise ValueError('PIN_COUNT_DRIFT')
 for at,raw in FIELDS.items():
  if out.get(at)!=bytes.fromhex(raw):raise ValueError('FIELD_OWNER_DRIFT:'+hex(at))
 return out

def mode_route(helper_nonzero,packet_flag_50):
 """The first 0x0306B9F0 branch; A/B R8B does NOT choose this predicate."""
 return 'inline_task' if not helper_nonzero and not (packet_flag_50&0x20) else 'member_virtual'
def member_virtual_slot(state104):
 return 0x100 if state104 in (1,2) else 0xe8
def branch_destination(at,raw):
 if len(raw)==2 and (0x70<=raw[0]<=0x7f or raw[0]==0xeb):
  return at+2+struct.unpack_from('<b',raw,1)[0]
 if len(raw)==5 and raw[0]==0xe9:return at+5+struct.unpack_from('<i',raw,1)[0]
 if len(raw)==6 and raw[0]==0x0f and 0x80<=raw[1]<=0x8f:
  return at+6+struct.unpack_from('<i',raw,2)[0]
 raise ValueError('NOT_BRANCH:'+hex(at))
def audit(exe):
 pe=OriginalEXE(exe)
 try:
  if pe.sha!=SHA or pe.base!=IMAGEBASE:raise ValueError('EXE_DRIFT')
  pins=inventory();owners={}
  for at,raw in pins.items():
   if pe.section(at)!='.00cfg' or pe.read(at,len(raw))!=raw:
    raise ValueError('OPCODE_DRIFT:'+hex(at))
   o=pe.owner(at)
   if not o:raise ValueError('OWNER_MISSING:'+hex(at))
   span=o[:2]
   if span not in owners:owners[span]=pe.starts_in(*span)
   if at not in owners[span]:raise ValueError('MID_INSTRUCTION:'+hex(at))
  for at,dest in CALLS.items():
   b=pe.read(at,5)
   if b[0]!=0xe8 or at+5+struct.unpack_from('<i',b,1)[0]!=dest:
    raise ValueError('E8_DRIFT:'+hex(at))
  for at,dest in JCC.items():
   if branch_destination(at,pins[at])!=dest:raise ValueError('JUMP_DRIFT:'+hex(at))
  for offset,dest in VTABLE.items():
   if struct.unpack('<Q',pe.read(MEMBER_VTABLE+offset,8))[0]!=IMAGEBASE+dest:
    raise ValueError('VTABLE_DRIFT:'+hex(offset))
  return dict(schema='bsc.n1.ab_member_receiver_position_dispatch.v1',
   proof='EXACT_ORIGINAL_EXE_STATIC',original_exe_sha256=pe.sha,
   verified_full_opcodes=len(pins),verified_direct_e8=len(CALLS),
   verified_conditional_edges=len(JCC),verified_member_vtable_slots=len(VTABLE),
   typed_function_owners=len(owners),
   A_receiver_r8b=1,B_receiver_r8b=0,
   shared_receiver='member vtable+0x368 -> 0x0306B9F0',
   inline_gate='helper=0 and packet+0x50 bit0x20=0; R8B not used in predicate',
   other_state_gate='member+0x104 in (1,2) -> virtual+0x100 -> 0x0315F4E0; otherwise +0xe8 -> 0x0315EC98',
   position_writes=['0x0315F52C/53E write member+0x88/+0x90',
                    '0x0315F311/327 and 33F conditionally write member+0x88/+0x90'],
   flag_writes='(member+0x108 & 0xF7) | 0x02; clears bit8 not bit4',
   r9_width_is_A_B_flag_bug_proven=False,
   shift_branch_hit_proven=False,bad_position_write_observed=False,
   root_cause_proven=False,gameplay_patch_authorized=False)
 finally:pe.close()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True);p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():p.error('EXE_OVERWRITE_FORBIDDEN')
 data=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n','utf8')
 print('ORIGINAL_STATIC_PASS',data['verified_full_opcodes'],'opcodes',data['verified_direct_e8'],'E8',data['verified_member_vtable_slots'],'vtable; NO PATCH')
if __name__=='__main__':main()
