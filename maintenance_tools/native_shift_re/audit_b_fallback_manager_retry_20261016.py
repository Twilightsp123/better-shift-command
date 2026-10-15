#!/usr/bin/env python3
"""Original WH3 B fallback route-node retry: read-only exact EXE proof."""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA,IMAGEBASE

PINS={int(a,16):bytes.fromhex(b) for a,b in (line.split() for line in '''030eca5f 4c8911
030eca66 48895108
030ecaa4 c74148ffffffff
030ecaab 4488514c
03128eaf 4533e4
03128ec6 458d6c2401
03129031 488bbbd0020000
03129038 418bec
03129055 488b7718
03129059 44396704
0312905d 750d
0312906c 4401ab500b0000
03129073 413bed
03129076 732a
03129078 44386708
0312907c 7524
0312907e 488d5720
03129082 488bca
03129085 e88e2dffff
0312908a 85c0
0312908c 7414
0312908e 488d4b18
03129092 e8054afdff
03129097 48894770
0312909b 4103ed
0312909e 44886f08
031290a2 44386f08
031290a6 7509
031290b1 4401ab580b0000
031290b8 488bfe
0311be1c 8b4148
0311be1f 83f8ff
0311be22 751b
0311be24 488b01
0311be27 4885c0
0311be2a 750b
0311be2c 488b4108
0311be30 488b80100a0000
0311be37 488bc8
0311be3a e809bcf1ff
03037a48 488b8198000000
03037a4f 4885c0
03037a54 83780400
03037a58 7507
03037a52 740d
03037a5a 8b81a4000000
03037a60 c3
03037a61 8b8184010000
03037a67 c3
03271bee 488b4b30
03271bf6 488b8140040000
03271bfd 488b8860010000
03271c04 e8a7fdeaff
03271c09 48894378
03121a25 6683630800
03121a39 c7430401000000
03121a40 e8a7affcff
03121a45 4883637000
03121a4d e81ecdfeff
03121a58 4883bfd002000000
03121a69 488b4708
03121a82 e87d13caff
03121a89 7406
03121a8b 807e4c01
03121a8f 7515
03121a91 488d4f18
03121a95 488d5320
03121a99 e8febffdff
03121a9e 48894370
03121aa2 c6430801
0328152a 80b98000000000
03281537 0f85a1000000
0328153d 488b4178
0328154a 80780800
0328154e 0f8497000000
03281554 488b4070
03281566 4889442420
032815c5 e85a45feff'''.strip().splitlines())}
LEAVES=((0x03037a48,0x03037a68),(0x030eca50,0x030ecab0))
E8={0x03271c04:0x031219b0,0x03121a40:0x030ec9ec,
 0x03121a4d:0x0310e770,0x03121a82:0x02dc2e04,
 0x03121a99:0x030fda9c,0x03129085:0x0311be18,
 0x03129092:0x030fda9c,0x0311be3a:0x03037a48,
 0x032815c5:0x03265b24}
JCC={0x0312905d:0x0312906c,0x03129076:0x031290a2,
 0x0312907c:0x031290a2,0x0312908c:0x031290a2,
 0x0311be22:0x0311be3f,0x03121a89:0x03121a91,
 0x03121a8f:0x03121aa6,0x03281537:0x032815de,
 0x0328154e:0x032815eb}
VTABLE={(0x03ae00e8,0x10):0x03281520}

def manager_can_attempt(*,linked_and_live,handled,validator_nonzero,prior_attempts):
 return bool(linked_and_live and not handled and validator_nonzero and prior_attempts<1)

def validator_result(record_plus48,derived_value):
 return derived_value if record_plus48==0xffffffff else record_plus48

def audit(path):
 pe=OriginalEXE(Path(path))
 try:
  if pe.sha!=SHA or pe.base!=IMAGEBASE:raise ValueError('EXE_DRIFT')
  starts={}
  for at,raw in PINS.items():
   if pe.section(at)!='.00cfg' or pe.read(at,len(raw))!=raw:
    raise ValueError('OPCODE_DRIFT:'+hex(at))
   owner=pe.owner(at)
   span=owner[:2] if owner else next((a for a in LEAVES if a[0]<=at<a[1]),None)
   if span is None:raise ValueError('OWNER_DRIFT:'+hex(at))
   if span not in starts:starts[span]=pe.starts_in(*span)
   if at not in starts[span]:raise ValueError('MID_INSTRUCTION:'+hex(at))
  for at,dest in E8.items():
   raw=pe.read(at,5)
   if raw[0]!=0xe8 or at+5+struct.unpack_from('<i',raw,1)[0]!=dest:
    raise ValueError('E8_DRIFT:'+hex(at))
  for at,dest in JCC.items():
   raw=pe.read(at,6)
   if raw[0]==0x0f and 0x80<=raw[1]<=0x8f:
    actual=at+6+struct.unpack_from('<i',raw,2)[0]
   elif 0x70<=raw[0]<=0x7f:
    actual=at+2+struct.unpack_from('<b',raw,1)[0]
   else:raise ValueError('NOT_JCC:'+hex(at))
   if actual!=dest:raise ValueError('JCC_DRIFT:'+hex(at))
  for (table,slot),dest in VTABLE.items():
   if struct.unpack('<Q',pe.read(table+slot,8))[0]!=IMAGEBASE+dest:
    raise ValueError('B_VTABLE_DRIFT')
  if any(pe.owner(s[0]) for s in LEAVES):raise ValueError('LEAF_OWNER_DRIFT')
  for ret in (0x03037a60,0x03037a67,0x030ecaaf):
   if pe.read(ret,1)!=b'\xc3':raise ValueError('LEAF_RET_DRIFT:'+hex(ret))
  return {'schema':'bsc.n1.b_generic_node_manager_retry.v1',
   'sha256':pe.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
   'opcode_instruction_starts':len(PINS),'E8_edges':len(E8),
   'JCC_edges':len(JCC),'typed_vtable_slots':len(VTABLE),
   'fallback_record_plus48':'0xffffffff from 0x030ECAA4',
   'fallback_record_plus4c':'0; no forced initial conversion',
   'manager_node_list':'manager+0x2D0, node+0x18 next',
   'node_initialization':{'plus4':1,'plus8':0,'plus70':'NULL'},
   'manager_budget':'at most one validator-passing conversion attempt per call',
   'manager_retry_gate':'node+4 nonzero and node+8 zero and budget<1 and validator nonzero',
   'validator_sentinel':'record+0x48 == -1 uses group+0xA10 UnitRoot-derived context',
   'retry_writes':'node+0x70 = 0x030FDA9C return; node+0x08 = 1',
   'consumer':'ordinary B +0x10 tests node+0x08 then reads node+0x70; no local non-null gate',
   'null_route_occurs_in_shift_observed':False,
   'group_generation_mismatch_proven':False,
   'gameplay_patch_authorized':False}
 finally:pe.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--out',type=Path)
 args=ap.parse_args()
 if args.out and args.out.resolve()==args.exe.resolve():ap.error('EXE_OVERWRITE_FORBIDDEN')
 data=audit(args.exe)
 if args.out:
  args.out.parent.mkdir(parents=True,exist_ok=True)
  args.out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print('PASS',data['opcode_instruction_starts'],'opcodes',data['E8_edges'],'E8',data['JCC_edges'],'JCC; NO PATCH')
if __name__=='__main__':main()
