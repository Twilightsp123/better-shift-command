#!/usr/bin/env python3
"""BSC N1 Round 26: original WH3 typed-member state writers & Tick ordering.

Read-only, exact original EXE only. No Shift runtime correlation or patch.
"""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA,IMAGEBASE
PINS=Path(__file__).with_name('member_state_transition_pins_20261016.txt')
TABLE=0x0390D4F8
SLOTS={0x128:0x0307FB0C,0x130:0x0307FC3C,0x138:0x0307FB50,
       0x538:0x0306A100,0x550:0x0306A53C}
E8={
0x0307FB15:0x0307EE8C,0x0307FB3B:0x0307F760,
0x0306A121:0x02DB0A10,0x0306A135:0x03248B38,
0x0306A6C7:0x02DB0A10,0x03117226:0x0306A100,
0x03068172:0x0307F760,0x03068187:0x0302EF58,
0x03068197:0x03080F4C,0x0306819F:0x03079768,
0x030822D2:0x03080F4C,0x030822F9:0x03054B84,
0x03082301:0x03088808,0x03082399:0x03068154,
0x0308238F:0x03070E38}
JUMPS={
0x0306816D:0x03068177,0x030681AB:0x030681B6,
0x0308226A:0x0308227D,0x03082278:0x030823A9,
0x0308227F:0x030822E9,0x0308228A:0x030822CB,
0x0308228F:0x030822CB,0x030822E4:0x030823A9,
0x030822F3:0x030823A0,0x0308230D:0x03082328,
0x03082338:0x03082396,0x03082356:0x03082396,
0x03082394:0x030823A9,0x0308239E:0x030823A9}
OFFSETS={
0x0307FB40:'808b0801000006',0x0307FB5A:'80a108010000fb',
0x0307FB6E:'4008b908010000',0x0307FC77:'24fb',
0x0307FC79:'0c02',0x0307FC7B:'888108010000',
0x0306A111:'c7812403000004000000',
0x0306A6BA:'c7832403000010000000',
0x030681A4:'f6830801000004',
0x030681B0:'ff9088040000',
0x03068197:'e8b08d0100',
0x030822CB:'488d8f28030000',
0x030822D2:'e875ecffff',
0x030822F9:'e88628fdff',
0x03082301:'e802650000',
0x03082399:'e8b65dfeff',
0x03068235:'83a32403000000',0x0306826B:'83a32403000000',
0x03068293:'83a32403000000',0x030682AF:'83a32403000000'}
def pins():
 d={}
 for line_no,line in enumerate(PINS.read_text('utf8').splitlines(),1):
  w=line.split('#',1)[0].split()
  if not w:continue
  if len(w)!=2:raise ValueError('PIN_FORMAT:'+str(line_no))
  addr=int(w[0],16)
  if addr in d:raise ValueError('DUPLICATE_PIN')
  d[addr]=bytes.fromhex(w[1])
 if len(d)!=142:raise ValueError('PIN_COUNT_DRIFT')
 for addr,raw in OFFSETS.items():
  if d.get(addr)!=bytes.fromhex(raw):raise ValueError('MEMBER_FIELD_TYPE_DRIFT:'+hex(addr))
 return d
def branch(at,raw):
 if len(raw)==2 and (0x70<=raw[0]<=0x7f or raw[0]==0xeb):
  return at+2+struct.unpack_from('<b',raw,1)[0]
 if len(raw)==5 and raw[0]==0xe9:return at+5+struct.unpack_from('<i',raw,1)[0]
 if len(raw)==6 and raw[0]==0x0f and 0x80<=raw[1]<=0x8f:
  return at+6+struct.unpack_from('<i',raw,2)[0]
 raise ValueError('BAD_BRANCH')
def native_flags(initial):
 return {'set_action':initial|6,'exit_a':(initial&0xfb)|2,
         'exit_b':(initial&0xfb)|0xa}
def tick_branch(flag108,state324,b20_null=True):
 if flag108&8:return 'other_virtual_0x498'
 if flag108&4:
  if state324 in (4,16):return 'inline_action_no_neighbor_this_tick'
  return 'other_state_dispatch_no_claim'
 return 'neighbor_then_optional_reset' if b20_null else 'other_virtual_0x490'
def audit(path):
 exe=OriginalEXE(path)
 try:
  if exe.sha!=SHA or exe.base!=IMAGEBASE:raise ValueError('EXE_DRIFT')
  data=pins();starts={}
  for addr,raw in data.items():
   if exe.section(addr)!='.00cfg' or exe.read(addr,len(raw))!=raw:
    raise ValueError('OPCODE_CHANGED:'+hex(addr))
   owner=exe.owner(addr)
   if owner is None:raise ValueError('NO_UNWIND_OWNER:'+hex(addr))
   bound=owner[:2]
   if bound not in starts:starts[bound]=exe.starts_in(*bound)
   if addr not in starts[bound]:raise ValueError('MID_INSTRUCTION:'+hex(addr))
  for addr,target in E8.items():
   code=exe.read(addr,5)
   if code[0]!=0xe8 or addr+5+struct.unpack_from('<i',code,1)[0]!=target:
    raise ValueError('E8_DRIFT:'+hex(addr))
  for addr,target in JUMPS.items():
   if branch(addr,data[addr])!=target:raise ValueError('BRANCH_DRIFT:'+hex(addr))
  for off,target in SLOTS.items():
   if struct.unpack('<Q',exe.read(TABLE+off,8))[0]!=IMAGEBASE+target:
    raise ValueError('TYPED_MEMBER_VTABLE_DRIFT:'+hex(off))
  if not(0x0308227D<0x030822D2<0x030822E4<0x030822F9<0x03082301<0x03082399<0x030823A9):
   raise ValueError('TICK_ORDER_DRIFT')
  return {'schema':'bsc.n1.member_state_typed_phase.v1',
    'proof':'EXACT_ORIGINAL_EXE_STATIC','sha256':exe.sha,
    'opcode_starts':len(data),'e8_edges':len(E8),
    'branch_targets':len(JUMPS),'member_vtable_slots':len(SLOTS),
    'same_member_vtable':hex(TABLE),
    'flag_bit4_set':'virtual+0x128 OR member+0x108,6',
    'flag_bit4_clear':'virtual+0x130 and +0x138; later exit +0x138 also sets bit8',
    'state4':'virtual+0x538 writes member+0x324=4',
    'state16':'virtual+0x550 conditionally writes member+0x324=16',
    'conditional_reset':'0x03068154 has four guarded member+0x324=0 stores',
    'same_tick_order':'0x03082399 after neighbor 0x030822F9 and special 0x03082301; cannot retroactively choose earlier branch',
    'state324_zero_implies_neighbor':False,
    'player_SHIFT_instance_bound':False,
    'member_pair_divergence_observed':False,
    'native_patch_authorized':False}
 finally:exe.close()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True);p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():p.error('NEVER_OVERWRITE_EXE')
 result=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('STATIC_PASS',result['opcode_starts'],'opcodes',result['e8_edges'],'E8',result['branch_targets'],'jumps',result['member_vtable_slots'],'slots; NO PATCH')
if __name__=='__main__':main()
