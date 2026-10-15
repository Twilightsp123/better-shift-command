#!/usr/bin/env python3
"""WH3 ordinary-B fast vs deferred member-input ABI; fixed original EXE only.

No executable modification, runtime Shift identity, or gameplay-fix claim.
"""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA,IMAGEBASE
PINS=Path(__file__).with_name('b_two_path_compare_pins_20261015.txt')
E8={0x03271b71:0x030c4bbc,0x03271b8e:0x03265b24,
 0x032815a7:0x030c4bbc,0x032815c5:0x03265b24,
 0x03265c69:0x0326a3a0,0x03271be9:0x030eca50,
 0x03271c04:0x031219b0}
VTABLE={(0x03ae00e8,0x08):0x03271b0c,(0x03ae00e8,0x10):0x03281520}
# Pinned typed operands: selected instructions prove the source/record layout,
# without falsely asserting initialized padding or equal live route objects.
OFFSETS={
 0x03271b1e:'488b4160',0x0328153d:'488b4178',0x03281554:'488b4070',
 0x03271b32:'488b5118',0x0328155d:'488b5118',
 0x03271b65:'f30f1145ef',0x0328159d:'f30f11442428',
 0x03271b6a:'44894dfb',0x03281561:'8364243400',
 0x03271b6e:'8945ff',0x032815a3:'89442438',
 0x03271b7b:'488b4b10',0x032815b1:'488b4b10',
 0x03271b83:'4c8b4318',0x032815ba:'4c8b4318',
 0x03271b87:'488b5108',0x032815be:'488b5108',
 0x03271b7f:'4c8d4de7',0x032815b5:'4c8d4c2420',
 0x03265bbe:'41ff5248',0x03265bdb:'4c8b34c8',
 0x03265be3:'49c1e004',0x03265be7:'4c0345c7',
 0x03265bf1:'418b402c',0x03265d3f:'ff9068030000',
}
def pins():
 data={}
 for i,line in enumerate(PINS.read_text('utf8').splitlines(),1):
  fields=line.split('#',1)[0].split()
  if not fields:continue
  if len(fields)!=2:raise ValueError('INVALID_PIN:'+str(i))
  addr=int(fields[0],16)
  if addr in data:raise ValueError('DUPLICATE_PIN:'+hex(addr))
  data[addr]=bytes.fromhex(fields[1])
 if len(data)!=82:raise ValueError('PIN_COUNT_DRIFT')
 for addr,raw in OFFSETS.items():
  if data.get(addr)!=bytes.fromhex(raw):raise ValueError('DATAFLOW_GUARD_DRIFT:'+hex(addr))
 return data

def parameter_fields(route,scale,flags,status):
 """Only initialized byte/word/dword or pointer fields of a 0x30 record."""
 if len(flags)!=6:raise ValueError('EXPECTED_SIX_FLAGS')
 return {0:route,8:scale,12:flags[0],13:flags[1],14:flags[2],
         15:flags[3],16:flags[4],20:0,24:status,28:flags[5]}

def audit(exe):
 pe=OriginalEXE(exe)
 try:
  if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
  owner_cache={}
  ins=pins()
  for addr,raw in ins.items():
   if pe.section(addr)!='.00cfg' or pe.read(addr,len(raw))!=raw:
    raise ValueError('BYTE_GUARD_DRIFT:'+hex(addr))
   owner=pe.owner(addr)
   if owner is None:raise ValueError('MISSING_UNWIND_OWNER:'+hex(addr))
   span=owner[:2]
   if span not in owner_cache:owner_cache[span]=pe.starts_in(*span)
   if addr not in owner_cache[span]:raise ValueError('MID_INSTRUCTION:'+hex(addr))
  for site,dest in E8.items():
   op=pe.read(site,5)
   if op[0]!=0xe8 or site+5+struct.unpack_from('<i',op,1)[0]!=dest:
    raise ValueError('E8_TARGET_DRIFT:'+hex(site))
  for (table,offset),dest in VTABLE.items():
   if struct.unpack('<Q',pe.read(table+offset,8))[0]!=IMAGEBASE+dest:
    raise ValueError('TYPED_VTABLE_DRIFT')
  return {'schema':'bsc.n1.ordinary_b_two_sender_input_contract.v1',
   'sha256':pe.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
   'decoded_instructions':len(ins),'direct_e8':len(E8),'vtable_slots':2,
   'route_fast':'aux+0x60','route_deferred':'aux+0x78 -> node+0x70 gated node+0x08',
   'argument_fields_proven_equal_layout':True,'padding_bytes_equal_proven':False,
   'per_member_strategy_same_function':True,
   'member_source':'aux+0x10 -> +0x08, aux+0x18',
   'route_object_same_generation_proven':False,'gameplay_patch_authorized':False}
 finally:pe.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--exe',type=Path,required=True)
 ap.add_argument('--out',type=Path)
 args=ap.parse_args()
 if args.out and args.exe.resolve()==args.out.resolve():ap.error('EXE_OVERWRITE_FORBIDDEN')
 r=audit(args.exe)
 if args.out:
  args.out.parent.mkdir(parents=True,exist_ok=True)
  args.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('PASS',r['decoded_instructions'],'instructions',r['direct_e8'],'E8',r['vtable_slots'],'vtables; NO PATCH')
if __name__=='__main__':main()
