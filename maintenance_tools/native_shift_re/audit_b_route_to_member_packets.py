#!/usr/bin/env python3
"""SHA-pinned, read-only WH3 B route-node -> per-member packet proof.

An original EXE STATIC proof, never proof of V3 execution or final motor
commit. Aborts on wrong SHA/image/opcode/vtable/call, never modifies EXE.
"""
import argparse,hashlib,json,mmap,struct,sys
from pathlib import Path
SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
BASE=0x140000000
PINS={
 'subtype_ctor_vtbl':(0x3263ed5,'488d150cc28700'),
 'subtype_ctor_install':(0x3263edc,'488913'),
 'subtype_route_node_assigned':(0x3271c09,'48894378'),
 'subtype_cache_pointer':(0x328153d,'488b4178'),
 'subtype_cache_not_null':(0x3281541,'4885c0'),
 'subtype_cache_ready':(0x328154a,'80780800'),
 'subtype_cache_ready_branch':(0x328154e,'0f8497000000'),
 'subtype_node_route_read':(0x3281554,'488b4070'),
 'subtype_packet_geometry_pointer':(0x3281566,'4889442420'),
 'subtype_dispatch':(0x32815c5,'e85a45feff'),
 'other_subtype_vtbl':(0x3263fe4,'488d151dc18700'),
 'main_B_task_vtbl':(0x3263acf,'488d0552c68700'),
 'packet_member_array':(0x3265bd4,'488b4628'),
 'packet_strategy_v48':(0x3265bbe,'41ff5248'),
 'packet_geom_r8':(0x3265b8b,'4d8b07'),
 'packet_ctor':(0x3265c69,'e832470000'),
 'packet_member_adjustment':(0x3265ca9,'e872c8d0ff'),
 'packet_member_v368':(0x3265d3f,'ff9068030000'),
 'packet_loop_count':(0x3265d4d,'443b6624'),
 'task_factory_vtbl':(0x2f6eee5,'488d058c80b500'),
 'active_task_vtbl_install':(0x2f6efde,'488d05b36d9900'),
 'active_task_state3':(0x2f6efeb,'c783a000000003000000'),
 'B_member_bit7_write':(0x3263c0a,'0883100b0000'),
 'active_task_bit7_read':(0x2f879c7,'8a97100b0000'),
 'associated_member_bit7_read':(0x2f879d7,'410fb687100b0000'),
 'active_task_bit7_clear':(0x2f879f3,'8897100b0000'),
 'separate_motor_goal_commit':(0x311963a,'0f1187e0010000'),
 'B_packet_code_4c_zero':(0x2f5f91a,'41894a4c'),
 'B_packet_code50_bits':(0x2f5f940,'80c906'),
 'B_packet_code50_store':(0x2f5f95e,'41884a50'),
 'B_packet_creator_call_1':(0x326a423,'e8b454cfff'),
 'B_packet_creator_call_2':(0x326a466,'e87154cfff'),
 'member_mode_classifier':(0x306ba23,'e8dc73d5ff'),
 'member_deferred_guard':(0x306ba2f,'f6425020'),
 'member_deferred_builder_call':(0x306ba5b,'e8683defff'),
 'deferred_task_vtable_install':(0x2f5f7dd,'488d0534669a00'),
 'deferred_task_payload_offset':(0x2f5f843,'034b4c'),
 'deferred_task_deadline_store':(0x2f5f84a,'898fa0000000'),
 'deferred_task_deadline_read':(0x2f6b184,'8b81a0000000'),
 'deferred_task_deadline_compare':(0x2f6b18a,'398298000000'),
}
VTABLES={
 'cached_subtype_v8':(0x3ae00e8+0x08,0x3271b0c),
 'cached_subtype_v10':(0x3ae00e8+0x10,0x3281520),
 'other_subtype_v10':(0x3ae0108+0x10,0x3281600),
 'main_B_v10':(0x3ae0128+0x10,0x3281408),
 'member_task_factory_v90':(0x3ac6f78+0x90,0x2f6ef4c),
 'bit7_active_v28':(0x3905d98+0x28,0x2f85960),
 'bit7_active_v78':(0x3905d98+0x78,0x2f87684),
 'bit7_negative_v78':(0x3905d18+0x78,0x11287fc),
 'member_deferred_task_tick':(0x3905e18+0x10,0x2f83b24),
}
CALLS={
 'cached_subtype_constructor':(0x3279f71,0x3263ec4),
 'other_subtype_constructor':(0x327a001,0x3263fcc),
 'cache_to_fanout':(0x32815c5,0x3265b24),
 'related_fanout':(0x3271b8e,0x3265b24),
 'per_member_packet_builder':(0x3265c69,0x326a3a0),
 'per_member_adjustment':(0x3265ca9,0x2f72520),
 'B_member_preclassification':(0x3263bfb,0x3068c38),
 'B_packet_ctor_call_a':(0x326a423,0x2f5f8dc),
 'B_packet_ctor_call_b':(0x326a466,0x2f5f8dc),
 'B_receiver_deferred_ctor':(0x306ba5b,0x2f5f7c8),
}
class StrictPE:
 def __init__(self,path):
  self.path=Path(path)
  with self.path.open('rb') as f:self.sha=hashlib.file_digest(f,'sha256').hexdigest()
  if self.sha!=SHA:raise ValueError('SHA_MISMATCH:'+self.sha)
  self.fd=self.path.open('rb')
  self.mm=mmap.mmap(self.fd.fileno(),0,access=mmap.ACCESS_READ)
  raw=self.mm
  if raw[:2]!=b'MZ':raise ValueError('BAD_MZ')
  nt=struct.unpack_from('<I',raw,0x3c)[0]
  if raw[nt:nt+4]!=b'PE\0\0':raise ValueError('BAD_PE')
  machine,n=struct.unpack_from('<HH',raw,nt+4)
  if machine!=0x8664:raise ValueError('NOT_AMD64')
  self.base=struct.unpack_from('<Q',raw,nt+48)[0]
  if self.base!=BASE:raise ValueError('IMAGE_BASE_MISMATCH')
  opt=nt+24; sz=struct.unpack_from('<H',raw,nt+20)[0]
  self.sections=[]
  for i in range(n):
   p=opt+sz+i*40
   _,rva,size,off=struct.unpack_from('<IIII',raw,p+8)
   flags=struct.unpack_from('<I',raw,p+36)[0]
   self.sections.append((rva,size,off,flags))
 def read(self,rva,length,code=False):
  for start,size,off,flags in self.sections:
   if start<=rva and rva+length<=start+size:
    if code and not flags&0x20000000:raise ValueError('NON_CODE:'+hex(rva))
    return bytes(self.mm[off+rva-start:off+rva-start+length])
  raise ValueError('RVA_NOT_MAPPED:'+hex(rva))
 def close(self):self.mm.close();self.fd.close()
def e8_destination(site,raw):
 if len(raw)!=5 or raw[0]!=0xe8:raise ValueError('NOT_E8:'+hex(site))
 return site+5+struct.unpack_from('<i',raw,1)[0]
def audit(path):
 pe=StrictPE(path)
 try:
  for key,(site,expected) in PINS.items():
   if pe.read(site,len(expected)//2,True).hex()!=expected:raise ValueError('BYTE_GUARD_FAIL:'+key)
  for key,(slot,target) in VTABLES.items():
   if struct.unpack('<Q',pe.read(slot,8))[0]!=BASE+target:raise ValueError('VTABLE_FAIL:'+key)
  for key,(site,target) in CALLS.items():
   if e8_destination(site,pe.read(site,5,True))!=target:raise ValueError('E8_FAIL:'+key)
  return {'sha256':SHA,'level':'ORIGINAL_EXE_STATIC','machine_guards':len(PINS),
          'vtable_slots':len(VTABLES),'direct_calls':len(CALLS),
          'route_bridge':'0x3AE00E8+0x10 -> 0x03281520: task+0x78 -> node+0x70 geometry -> 0x03265B24 -> member virtual+0x368',
          'bit7_bridge':'0x3AC6F78+0x90 -> 0x02F6EF4C -> task vtable 0x03905D98 +0x78 -> 0x02F87684',
          'different_B_main_vtable':'0x3AE0128+0x10 -> 0x03281408',
          'conditional_deferred_member_path':'0x02F5F8DC produces packet+0x50 with no bit 0x20; if native mode check 0x02DC2E04 is false, receiver 0x0306B9F0 builds 0x03905E18 deferred task at 0x02F5F7C8',
          'deferred_task_deadline':'task+0xA0 = native group tick+packet+0x4C; branch checks it in 0x02F6B170; no guarantee motor changes during same tick',
          'unproven':['whether either path executed in historic V3',
                       'packet+0x368 to normal soldier motor+0x1E0 and its activation timing',
                       'whether bit7 task belongs to B movement in V3',
                       'safe repair predicate'],
          'patch_authorized':False,'wh3_game_verified':False}
 finally:pe.close()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--exe',required=True,type=Path);ap.add_argument('--out',required=True,type=Path)
 args=ap.parse_args()
 if args.exe.resolve()==args.out.resolve():ap.error('NEVER_OVERWRITE_EXE')
 try:
  result=audit(args.exe)
  args.out.parent.mkdir(parents=True,exist_ok=True)
  args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
  print('EXACT STATIC PASS',len(PINS),'bytes',len(VTABLES),'vtables',len(CALLS),'calls; no patch')
  return 0
 except (ValueError,OSError,struct.error) as e:
  print('B_ROUTE_AUDIT_REFUSED',e,file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
