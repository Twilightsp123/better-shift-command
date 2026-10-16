#!/usr/bin/env python3
"""Fixed original WH3: per-member Tick branch and distinct component+0xE0 write.

Read-only: no runtime Shift identity, velocity patch, or crowding-cause claim.
"""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA,IMAGEBASE

MANIFEST=Path(__file__).with_name('member_tick_motion_type_manifest_20261016.txt')
CALLS={0x0304E825:0x0304E6F8,0x030822D2:0x03080F4C,
 0x030822DA:0x03079768,0x030822DF:0x030834DC,
 0x030822F9:0x03054B84,0x03082301:0x03088808,
 0x03082E40:0x03085AC0,0x03082E6D:0x03085AC0}
BRANCHES={0x03082278:0x030823A9,0x0308227F:0x030822E9,
 0x0308228A:0x030822CB,0x0308228F:0x030822CB,
 0x030822E4:0x030823A9,0x030822F3:0x030823A0,
 0x03080F59:0x03080F8A,0x03080F7C:0x03080F8A}
COMP_TABLE=0x03ACD0D8;COMP_METHOD=0x03082CD4
CTOR_VTABLE_SITES=(0x0304E82A,0x0304FFB9)

def pins():
 d={}
 for i,line in enumerate(MANIFEST.read_text('utf8').splitlines(),1):
  fields=line.split('#',1)[0].split()
  if not fields:continue
  if len(fields)!=2:raise ValueError('ROW_DRIFT:'+str(i))
  at=int(fields[0],16)
  if at in d:raise ValueError('DUPLICATE_PIN:'+hex(at))
  d[at]=bytes.fromhex(fields[1])
 if len(d)!=66:raise ValueError('COUNT_DRIFT')
 return d

def jump(at,raw):
 if raw[0]==0xe9 and len(raw)==5:return at+5+struct.unpack_from('<i',raw,1)[0]
 if raw[0]==0x0f and len(raw)==6 and 0x80<=raw[1]<=0x8f:
  return at+6+struct.unpack_from('<i',raw,2)[0]
 if len(raw)==2 and 0x70<=raw[0]<=0x7f:
  return at+2+struct.unpack_from('<b',raw,1)[0]
 raise ValueError('NOT_BRANCH:'+hex(at))

def tick_state(flags108,state324,ref_b20_is_null=True):
 """Only the verified subgraph of member Tick; not a full state machine."""
 if flags108&0x08:return 'other_virtual_498'
 if flags108&0x04:
  return ('inline_action_tick_no_neighbor' if state324 in (4,16) else
          'another_state_branch')
 return ('neighbor_tick_then_special_state_check' if ref_b20_is_null else
         'other_virtual_490')

def audit(exe):
 pe=OriginalEXE(exe)
 try:
  if pe.sha!=SHA or pe.base!=IMAGEBASE:raise ValueError('WRONG_EXE_BUILD')
  d=pins();decoded={}
  for at,raw in d.items():
   if pe.section(at)!='.00cfg' or pe.read(at,len(raw))!=raw:
    raise ValueError('INSTRUCTION_DRIFT:'+hex(at))
   owner=pe.owner(at)
   if owner is None:raise ValueError('NO_UNWIND_OWNER:'+hex(at))
   bounds=owner[:2]
   if bounds not in decoded:decoded[bounds]=pe.starts_in(*bounds)
   if at not in decoded[bounds]:raise ValueError('MID_INSTRUCTION:'+hex(at))
  for at,target in CALLS.items():
   raw=pe.read(at,5)
   if raw[0]!=0xe8 or at+5+struct.unpack_from('<i',raw,1)[0]!=target:
    raise ValueError('E8_DRIFT:'+hex(at))
  for at,target in BRANCHES.items():
   if jump(at,d[at])!=target:raise ValueError('BRANCH_DRIFT:'+hex(at))
  for at in CTOR_VTABLE_SITES:
   raw=d[at]
   if raw[:3]!=bytes.fromhex('488d05') or at+7+struct.unpack_from('<i',raw,3)[0]!=COMP_TABLE:
    raise ValueError('COMPONENT_CTOR_DRIFT:'+hex(at))
  if struct.unpack('<Q',pe.read(COMP_TABLE+0x10,8))[0]!=IMAGEBASE+COMP_METHOD:
   raise ValueError('TYPED_VTABLE_DRIFT')
  for at,code in {0x03085AD2:'448a81e4000000',0x03085AE1:'488bd9',
   0x03085D06:'488b4308',0x03085D0A:'f30f1098e00000',
   0x03085D12:'f30f1090e80000',0x03085D89:'f30f1183e00000'}.items():
   if d[at].hex()!=code:raise ValueError('MEMBER_COMPONENT_ALIAS_ERROR:'+hex(at))
  return {'schema':'bsc.n1.member_tick_split_and_typed_component.v1',
   'sha256':pe.sha,'evidence':'EXACT_ORIGINAL_EXE_STATIC',
   'guarded_instruction_starts':len(d),'e8_edges':len(CALLS),
   'branch_targets':len(BRANCHES),'component_vtable_slots':1,
   'component_vtable':hex(COMP_TABLE),'component_method':hex(COMP_METHOD),
   'member_tick':'0x0308227D tests member+0x108 bit4; state+0x324 in {4,16} ticks member+0x328 inline action then jumps past neighbor call',
   'other_tick':'if bit4 clear and member+0xB20 NULL, call 0x03054B84 then 0x03088808',
   'typed_negative':'0x03085D89 stores component+0xE0; component+0xE4 is byte flags; component+0x08 points to separate member-like object',
   'same_SHIFT_unit_member_state_divergence_observed':False,
   'velocity_causality_proven':False,'gameplay_patch_authorized':False}
 finally:pe.close()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True);p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():p.error('EXE_OVERWRITE_FORBIDDEN')
 r=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('STATIC_PASS',r['guarded_instruction_starts'],'instructions',r['e8_edges'],'calls',r['branch_targets'],'branches; NO PATCH')
if __name__=='__main__':main()
