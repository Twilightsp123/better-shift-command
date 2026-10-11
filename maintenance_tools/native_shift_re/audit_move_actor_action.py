#!/usr/bin/env python3
"""Exact WH3 SHA: trace native MOVE packet to member-action replacement.

READ ONLY. This is STATIC, not proof that V3 took this conditional fanout.
The 0x03914618 subaction is not assumed to be the entire soldier motor.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import mmap
from pathlib import Path
import struct
import sys

EXPECTED_SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
BASE=0x140000000
# Original bytes from instruction-aligned LLVM disassembly, not array-offset guesses.
GUARDS={
 'fanout_member_index':(0x030D54F0,'488b1cf0'),
 'fanout_member_goal_copy':(0x030D54FC,'e867a3e8ff'),
 'fanout_member_v368':(0x030D550F,'ff9068030000'),
 'packet_zero_qword_30':(0x02F5F8A5,'48894b30'),
 'fanout_enable_target_adjustment':(0x030D54EB,'c644242001'),
 'packet_constructor_option_check':(0x02F5F8C4,'384c2450'),
 'packet_constructor_optional_helper_call':(0x02F5F8CD,'e84e2c0100'),
 'packet_set_option_2':(0x02F72526,'80495102'),
 'packet_adjusts_heading_for_code_26':(0x02F7252D,'f6415002'),
 'packet_heading_member_source_call':(0x02F72542,'e831cf1000'),
 'packet_write_member_adjusted_facing':(0x02F7254A,'66890b'),
 'packet_34_zero_is_30_qword':(0x02F5F8A9,'48894b38'),
 'packet_51_clear_bit1':(0x02F5F89D,'24fd'),
 'packet_51_set_bit0':(0x02F5F8A3,'0c01'),
 'packet_code_26':(0x02F5F8BD,'c6435026'),
 'receiver_test_packet_direct_20':(0x0306BA2F,'f6425020'),
 'receiver_direct_jne':(0x0306BA33,'7530'),
 'receiver_packet_51_bit1':(0x0306BA65,'f6425102'),
 'receiver_option2_branch':(0x0306BA69,'7415'),
 'receiver_option2_member_target_transform':(0x0306BA75,'e84e3b0100'),
 'member_heading_reads_parent':(0x0307F482,'488b81e8020000'),
 'member_heading_reads_scale':(0x0307F494,'f30f108984090000'),
 'member_heading_reads_parent_value':(0x0307F49C,'8b80cc360000'),
 'member_heading_add_to_record_angle':(0x0307F4C6,'660307'),
 'member_target_transform_begin':(0x0307F5E8,'e8a3000000'),
 'member_target_transform_finalize':(0x0307F673,'e860890800'),
 'actor_target_local_goal_transform':(0x0307F6A8,'e81fda0900'),
 'actor_target_local_facing_vector':(0x0307F6D6,'e809feffff'),
 'actor_target_add_offset_x':(0x0307F6EA,'f30f5807'),
 'actor_target_add_offset_z':(0x0307F6EE,'f30f584f04'),
 'receiver_member_mode':(0x0306BAD7,'8b8704010000'),
 'receiver_mode_1_2_range':(0x0306BAE4,'83f801'),
 'receiver_select_mode1_2':(0x0306BB0E,'41ff9300010000'),
 'receiver_select_mode0':(0x0306BB44,'41ff93e8000000'),
 'receiver_command_code_34':(0x0306BB61,'8b4334'),
 'receiver_dispatch_0xd600_bitmask':(0x0306BB69,'b900d60000'),
 'receiver_bt_code_bit':(0x0306BB6E,'0fa3c1'),
 'receiver_zero_code_to_81_branch':(0x0306BB71,'7334'),
 'receiver_other_action_reset':(0x0306BB73,'488d8f28030000'),
 'receiver_other_action_reset_call':(0x0306BB7A,'e8914ed4ff'),
 'receiver_zero_code_action_reset':(0x0306BBA7,'488d8f28030000'),
 'receiver_zero_code_action_reset_call':(0x0306BBAE,'e85d4ed4ff'),
 'receiver_zero_code_81':(0x0306BBCE,'c7452481000000'),
 'receiver_zero_code_action_install':(0x0306BBD5,'e832cf1d00'),
 'cleanup_check_owned_action':(0x02DB0A1E,'389154010000'),
 'cleanup_virtual_dispose':(0x02DB0A2F,'ff10'),
 'cleanup_clear_owned_action_flag':(0x02DB0A31,'c6835401000000'),
 'new_subaction_vtable':(0x03248B18,'488d15f9ba6c00'),
 'new_subaction_vtable_store':(0x03248B1F,'488911'),
 'new_subaction_zero_done_flag':(0x03248B2C,'c6414000'),
 'common_type_goal_forward':(0x0307328B,'e808ba0e00'),
 'common_type_action_state':(0x030732A4,'e873580000'),
 'common_type_spatial_cache_tail':(0x030732C0,'e90f3cfeff'),
 'group_task_to_native_fanout':(0x030D5603,'e888feffff'),
 'native_active_move_to_task_ctor':(0x030260AF,'e88066f0ff'),
 'task_conditional_dispatch':(0x02F56404,'e8373a3200'),
}
EDGES={
 'fanout_copy':(0x030D54FC,0x02F5F868),
 'packet_ctor_actor_adjustment':(0x02F5F8CD,0x02F72520),
 'packet_member_heading_adjustment':(0x02F72542,0x0307F478),
 'receiver_member_target_adjustment':(0x0306BA75,0x0307F5C8),
 'member_transform_original_goal':(0x0307F5E8,0x0307F690),
 'member_transform_finalize':(0x0307F673,0x03107FD8),
 'actor_goal_local_frame':(0x0307F6A8,0x0311D0CC),
 'actor_goal_direction_offset':(0x0307F6D6,0x0307F4E4),
 'common_goal_processing':(0x0307328B,0x0315EC98),
 'common_actor_state_transition':(0x030732A4,0x03078B1C),
 'common_actor_cache_tail':(0x030732C0,0x03056ED4),
 'reset_old_member_subaction':(0x0306BBAE,0x02DB0A10),
 'build_new_0x81_subaction':(0x0306BBD5,0x03248B0C),
 'new_0x81_ctor':(0x03248B13,0x0304E580),
 'unit_task_constructor':(0x030260AF,0x02F2C734),
 'conditional_bridge':(0x02F56404,0x03279E40),
 'bridge_to_adapter':(0x03279EB3,0x030D554C),
 'adapter_to_fanout':(0x030D5603,0x030D5490),
}
VTABLES={
 'new_status_class_v8':(0x03914618+0x8,0x03258B8C),
 'new_status_class_v10':(0x03914618+0x10,0x0325C818),
 'contact_action_a_v10':(0x03ACD208+0x10,0x0308279C),
 'contact_action_b_v10':(0x03ACD468+0x10,0x03083120),
 'contact_action_b_v130':(0x03ACD468+0x130,0x0308393C),
}
EXPECTED_COMMON_E8={0x03073224:28,0x02DCD63C:3,0x02F4F910:4,0x0311C92C:1}

class PE:
 def __init__(self,raw):
  self.raw=raw
  if len(raw)<0x100 or raw[:2]!=b'MZ':raise ValueError('BAD_DOS')
  nt=struct.unpack_from('<I',raw,0x3c)[0]
  if nt+24>len(raw) or raw[nt:nt+4]!=b'PE\0\0':raise ValueError('BAD_PE')
  machine,n=struct.unpack_from('<HH',raw,nt+4)
  sz=struct.unpack_from('<H',raw,nt+20)[0]
  opt=nt+24
  if machine!=0x8664 or not (0<n<=96) or sz<144 or opt+sz+n*40>len(raw):raise ValueError('NOT_AMD64')
  if struct.unpack_from('<H',raw,opt)[0]!=0x20b or struct.unpack_from('<Q',raw,opt+24)[0]!=BASE:raise ValueError('BAD_PE64_BASE')
  self.sections=[]
  for i in range(n):
   p=opt+sz+i*40
   _,rv,szraw,off=struct.unpack_from('<IIII',raw,p+8)
   flag=struct.unpack_from('<I',raw,p+36)[0]
   if szraw and (off>len(raw) or szraw>len(raw)-off):raise ValueError('SECTION_OOB')
   self.sections.append((rv,szraw,off,bool(flag&0x20000000)))
 def get(self,rva,n,x=None):
  if n<1:raise ValueError('NEG_LENGTH')
  for start,size,off,exe in self.sections:
   if rva>=start and rva+n<=start+size:
    if x is not None and x!=exe:raise ValueError('WRONG_SECTION_PERMISSIONS:'+hex(rva))
    return bytes(self.raw[off+rva-start:off+rva-start+n])
  raise ValueError('UNMAPPED:'+hex(rva))
 def pointer(self,rva):return struct.unpack('<Q',self.get(rva,8))[0]-BASE
 def member_tables(self):
  # Constructor-anchored native member-family getter virtual+0x3F8.
  needle=struct.pack('<Q',BASE+0x008F37B0); result={}
  for rv,size,off,exe in self.sections:
   if exe or not size:continue
   area=self.raw[off:off+size]; pos=0
   while True:
    found=area.find(needle,pos)
    if found<0:break
    pos=found+1; v=rv+found-0x3f8
    if v<rv or v%8 or v+0x400>rv+size:continue
    receiver=self.pointer(v+0x368)
    if receiver in (0x0306B9F0,0x0306B9CC,0x03117CE0):
     result[v]=(receiver,self.pointer(v+0xe8))
  return result

def direct_target(site,b):
 if b[0] not in (0xe8,0xe9) or len(b)!=5:raise ValueError('NOT_DIRECT_E8_E9')
 return site+5+struct.unpack_from('<i',b,1)[0]

def decode_packet():
 # Derive flow from guarded opcodes, NOT from guesses about English names.
 payload=bytearray(0x58)
 payload[0x30:0x38]=bytes(8) # mov [packet+0x30],zero clears packet+0x34
 payload[0x50]=0x26
 payload[0x51]=(payload[0x51]&0xfd)|1
 # Caller 0x030D54EB passes stack argument byte=1. Callee 0x02F5F8C4
 # reads the matching fifth Win64 argument at its [rsp+0x50] after prologue.
 # Thus 0x02F72520 is called and ORs +0x51 with 0x02. It also adjusts
 # the heading at +0x40 with actor-specific data, without changing +0x34.
 payload[0x51]|=2
 return {'packet_flag50':payload[0x50], 'command_code34':struct.unpack_from('<I',payload,0x34)[0],
   'option_51_low2_guaranteed':payload[0x51]&3, 'option_51_full_value_unknown':True,
   'deferred_member_task':(payload[0x50]&0x20)==0,
   'receiver_uses_optional_transformed_packet':bool(payload[0x51]&2),
   'member_action_zero_code_replacement':(struct.unpack_from('<I',payload,0x34)[0]>0xf or not bool((0xd600>>struct.unpack_from('<I',payload,0x34)[0])&1))}

def audit(path:Path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(4<<20),b''):h.update(chunk)
 if h.hexdigest()!=EXPECTED_SHA:raise ValueError('WRONG_EXE_SHA')
 with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mem:
  pe=PE(mem)
  guards=[]
  for label,(rva,hx) in GUARDS.items():
   b=pe.get(rva,len(hx)//2,True)
   if b.hex()!=hx:raise ValueError('GUARD_MISMATCH:'+label+':'+b.hex())
   guards.append(label)
  edges=[]
  for label,(rva,target) in EDGES.items():
   got=direct_target(rva,pe.get(rva,5,True))
   if got!=target:raise ValueError('BAD_CALL:'+label+':'+hex(got))
   edges.append(label)
  pointers=[]
  for label,(slot,target) in VTABLES.items():
   got=pe.pointer(slot)
   if got!=target:raise ValueError('BAD_VTABLE:'+label+':'+hex(got))
   pointers.append(label)
  if pe.get(0x03248B18,7,True)!=bytes.fromhex('488d15f9ba6c00'):raise ValueError('CTOR_CLASS_MISMATCH')
  # LEA at 0x03248B18 points at 0x03914618, not either contact action class.
  lea=0x03248B18+7+struct.unpack_from('<i',pe.get(0x03248B18,7,True),3)[0]
  if lea!=0x03914618 or lea in (0x03ACD208,0x03ACD468):raise ValueError('CLASS_SOURCE_INVALID')
  m=pe.member_tables()
  count=Counter(a for a,b in m.values())
  freq=Counter(b for a,b in m.values() if a==0x0306B9F0)
  if len(m)!=38 or count[0x0306B9F0]!=36 or freq!=EXPECTED_COMMON_E8:
   raise ValueError('MEMBER_METHOD_CENSUS_CHANGED:'+str(freq))
  # All four subtype +E8 methods lead into common 0x03073224.
  for rva in (0x02DCD724,0x02F4F940,0x02F4F992,0x0311C951):
   if direct_target(rva,pe.get(rva,5,True))!=0x03073224:raise ValueError('SUBTYPE_RECEIVER_DIVERGED:'+hex(rva))
  packet=decode_packet()
  if packet['command_code34']!=0 or packet['deferred_member_task'] or not packet['receiver_uses_optional_transformed_packet'] or not packet['member_action_zero_code_replacement']:
   raise ValueError('DERIVED_PACKET_POLICY_MISMATCH')
  return {
   'grade':'PINNED_EXE_STATIC_NO_RUNTIME_ASSERTION','exe_sha256':EXPECTED_SHA,
   'opcode_guards':len(guards),'direct_call_edges':len(edges),'vtable_slots':len(pointers),
   'vtable_method_frequency':{hex(k):v for k,v in freq.items()},'common_receiver_count':count[0x0306B9F0],
   'total_member_vtables':len(m),'packet':packet,
   'new_member_subaction_vtable':hex(lea),
   'action_a_vtable':'0x3acd208','action_b_vtable':'0x3acd468',
   'precise_result':[
    'Conditional MOVE-group fanout creates packet 0x26 with code +0x34 ZERO; caller enables optional helper so packet +0x51 bit 0x2 is SET.',
    'Common receiver skips the per-member delayed task for bit 0x20; optional 0x0307F5C8 actor-specific target transform runs before native v+0xE8 for member mode 0.',
    '36 common receiver variants use four v+0xE8 methods, each entering 0x03073224 (28 direct; 3/4/1 wrappers).',
    '0x03073224 calls target 0x0315EC98, reprocesses actor state 0x03078B1C and tail-calls member cache 0x03056ED4.',
    'With packet +0x34 zero, receiver calls 0x02DB0A10 to dispose an owned previous +0x328 action and builds a 0x03914618 action via 0x03248B0C.',
    'The newly constructed subaction is distinct from prior studied contact action A/B classes, which are NOT thereby proven to represent this MOVE packet.',
   ],
   'limits':['Existing V3 probes did not hit this group fanout: static reachability cannot establish that V3 followed it.',
             'Disposing +0x328 subaction does not prove the full motor path +0x7F8/+0x818 is reset.',
             'Member-dependent heading and local target transformation is native for both RMB and queued paths using this packet. It is not by itself a Shift-only defect.',
             '0x03069844/0x03069B10 may be invoked via other interactions and are not synonymous with this MOVE packet.',
             'The two exceptional member receiver classes are not covered by the 36 common class inference.'],
   'native_patch_authorized':False,'win64_runtime_tested':False,'gameplay_fix_tested':False,
  }

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.exe.resolve()==a.out.resolve():p.error('output must not overwrite EXE')
 try:
  result=audit(a.exe)
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  print('EXACT-EXE STATIC PASS',result['opcode_guards'],'byte guards',result['direct_call_edges'],'call edges',result['total_member_vtables'],'member tables; NO HOOK')
  return 0
 except (ValueError,OSError,struct.error) as exc:
  print('STRICT_FAIL:',exc,file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())