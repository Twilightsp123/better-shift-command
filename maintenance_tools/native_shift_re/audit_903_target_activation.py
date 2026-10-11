#!/usr/bin/env python3
"""Read-only WH3 9.0.3 exact-EXE proof of per-member issue vs motor activation.

Scope: CONDITIONAL 0x030D5490 fanout. V3 collector had zero hits there.
The emitted member pose and per-member action tick are verifiable; a producer
edge into 0x03071E04 primary-motor record is NOT established by this path.
"""
from __future__ import annotations
import argparse, hashlib, json, mmap, struct, sys, bisect
from collections import Counter
from pathlib import Path

SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
IMAGE_BASE=0x140000000
# Machine-code bytes are from the ORIGINAL supplied EXE and at instruction boundaries.
OPCODES={
 'group_generate_once':(0x030d54ca,'41ff5248'),
 'group_load_indexed_member':(0x030d54f0,'488b1cf0'),
 'group_copy_packet':(0x030d54fc,'e867a3e8ff'),
 'group_call_actor_virtual':(0x030d550f,'ff9068030000'),
 'group_increment_index':(0x030d5515,'ffc6'),
 'group_loop_count':(0x030d5517,'3b7724'),
 'group_postprocess_after_loop':(0x030d5522,'ff5020'),
 'actor_transform_goal':(0x0306ba75,'e84e3b0100'),
 'actor_action_mode_gate':(0x0306bad7,'8b8704010000'),
 'actor_submit_mode0':(0x0306bb44,'41ff93e8000000'),
 'actor_dispose_old_subaction':(0x0306bbae,'e85d4ed4ff'),
 'actor_construct_new_subaction':(0x0306bbd5,'e832cf1d00'),
 'mode0_apply_pose':(0x0307328b,'e808ba0e00'),
 'mode0_actor_state':(0x030732a4,'e873580000'),
 'mode0_refresh_local_cache':(0x030732c0,'e90f3cfeff'),
 'pose_write_xy_branch_a':(0x0315f311,'f20f118e88000000'),
 'pose_write_xy_branch_b':(0x0315f327,'f20f118688000000'),
 'pose_write_z':(0x0315f33f,'898690000000'),
 'pose_write_heading':(0x0315f34d,'66899eb0000000'),
 'pose_notify_mode':(0x0315f35f,'ff90e0000000'),
 'pose_update_spatial_a':(0x0315f368,'e86726feff'),
 'pose_update_spatial_b':(0x0315f370,'e87f24feff'),
 'cache_write_xyz':(0x03056f15,'410f1102'),
 'cache_read_old_assoc':(0x03056f28,'4c8b8b30090000'),
 'cache_assign_assoc':(0x03056fb7,'48898330090000'),
 'subaction_ctor_vtable':(0x03248b1f,'488911'),
 'actor_tick_subaction_site':(0x030822d2,'e875ecffff'),
 'actor_tick_status_flag_0x4':(0x0308227d,'a804'),
 'actor_tick_class_gate_0x10':(0x03082281,'8b872403000083'),
 'actor_tick_class_gate_0x4':(0x0308228c,'83f80474'),
 'actor_tick_subaction_subobject':(0x030822cb,'488d8f28030000'),
 'subaction_owned_gate':(0x03080f52,'80b95401000001'),
 'subaction_wait_initialized':(0x03080f5f,'807b1000'),
 'subaction_virtual_start':(0x03080f71,'ff5008'),
 'subaction_virtual_tick':(0x03080f84,'ff5010'),
 'subaction_local_counter':(0x03080f87,'ff4314'),
 'group_mean_transform_same_actor':(0x030d579b,'e8289efaff'),
 'group_current_pose_x':(0x030d57af,'f3410f108e88000000'),
 'group_current_pose_z':(0x030d57bb,'f3410f108690000000'),
 'group_distance_sqrt':(0x030d57f1,'f30f51d0'),
 'group_far_actor_counter':(0x030d580e,'ff83c4d00000'),
 'group_mean_divide':(0x030d585e,'f30f5ef0'),
 'group_mean_compare_threshold':(0x030d5862,'0f2ff7'),
 'group_ready_stamp':(0x030d5878,'89bbb8d00000'),
 'group_cohesion_generate_once':(0x030d56f6,'41ff5248'),
 'group_cohesion_evaluate':(0x030d5705,'e822000000'),
 'other_gate_queries_group_freshness':(0x0327e629,'e8fa6fe5ff'),
 'other_gate_checks_far_actor_count':(0x0327e644,'4183b8c4d00000'),
 'other_motor_goal_write_A':(0x03071e35,'0f1183f8070000'),
 'other_motor_goal_write_B':(0x03071e4a,'0f118318080000'),
 'other_motor_state_1':(0x03071e7c,'c7831007000001000000'),
 'other_motor_plan_update':(0x03071e86,'e895000000'),
}
EDGES={
 'group_packet_copy':(0x030d54fc,0x02f5f868),
 'actor_target_transform':(0x0306ba75,0x0307f5c8),
 'mode0_pose_receiver':(0x0307328b,0x0315ec98),
 'mode0_state_update':(0x030732a4,0x03078b1c),
 'mode0_cache_refresh_tail':(0x030732c0,0x03056ed4),
 'actor_old_subaction_cleanup':(0x0306bbae,0x02db0a10),
 'actor_new_subaction_ctor':(0x0306bbd5,0x03248b0c),
 'actor_tick_update_subaction':(0x030822d2,0x03080f4c),
 'group_metric_uses_same_target_transform':(0x030d579b,0x0307f5c8),
 'group_metric_calculator':(0x030d5705,0x030d572c),
 'other_motor_goal_builder':(0x03071e86,0x03071f20),
 'other_gate_group_freshness':(0x0327e629,0x030d5628),
}
VTABLES={
 'new_status_subaction_start':(0x03914618+0x8,0x03258b8c),
 'new_status_subaction_tick':(0x03914618+0x10,0x0325c818),
}
# Audited direct function bodies; absence of an E8/E9 edge does NOT exclude
# indirect/virtual dispatch or other paths and is never a negative runtime claim.
AUDITED_RECEIVE_FUNCS=(0x0306b9f0,0x03073224,0x0315ec98,0x03056ed4)
SEPARATE_MOTOR_FUNCS={0x03071e04,0x03071f20,0x0311954c}

class PE:
 def __init__(self,data):
  if len(data)<0x100 or data[:2]!=b'MZ':raise ValueError('NOT_MZ')
  peoff=struct.unpack_from('<I',data,0x3c)[0]
  if peoff+24>len(data) or data[peoff:peoff+4]!=b'PE\0\0':raise ValueError('NOT_PE')
  machine,n=struct.unpack_from('<HH',data,peoff+4)
  osz=struct.unpack_from('<H',data,peoff+20)[0];opt=peoff+24
  if machine!=0x8664 or not 1<=n<=96 or osz<144 or opt+osz+n*40>len(data):
   raise ValueError('NOT_PE32PLUS_AMD64')
  if struct.unpack_from('<H',data,opt)[0]!=0x20b:raise ValueError('NOT_PE32PLUS')
  if struct.unpack_from('<Q',data,opt+24)[0]!=IMAGE_BASE:raise ValueError('IMAGEBASE_MISMATCH')
  self.data=data;self.sections=[]
  for k in range(n):
   at=opt+osz+40*k
   name=bytes(data[at:at+8]).split(b'\0',1)[0].decode('ascii','replace')
   virtual,rva,size,raw=struct.unpack_from('<IIII',data,at+8)
   x=bool(struct.unpack_from('<I',data,at+36)[0]&0x20000000)
   if size and (raw>len(data) or size>len(data)-raw):raise ValueError('SECTION_OOB')
   self.sections.append((name,rva,size,raw,x))
  er,esize=struct.unpack_from('<II',data,opt+112+3*8)
  if not esize or esize%12:raise ValueError('BAD_EXCEPTION_DIR')
  rows=list(struct.iter_unpack('<III',self.read(er,esize)))
  if any(rows[k][0]>=rows[k+1][0] for k in range(len(rows)-1)):
   raise ValueError('BAD_EXCEPTION_SORT')
  self.funcs=rows;self.starts=[x[0] for x in rows]
 def read(self,rva,n,executable=None):
  if n<=0:raise ValueError('INVALID_LENGTH')
  for name,base,size,raw,x in self.sections:
   if base<=rva and rva+n<=base+size:
    if executable is not None and x!=executable:raise ValueError('PERMISSION_MISMATCH:'+hex(rva))
    return bytes(self.data[raw+rva-base:raw+rva-base+n])
  raise ValueError('UNMAPPED:'+hex(rva))
 def ptr(self,rva):
  val=struct.unpack('<Q',self.read(rva,8,False))[0]
  if val<IMAGE_BASE:raise ValueError('BAD_NATIVE_PTR')
  return val-IMAGE_BASE
 def func(self,site):
  i=bisect.bisect_right(self.starts,site)-1
  if i>=0 and self.funcs[i][0]<=site<self.funcs[i][1]:return self.funcs[i][:2]
  return None
 def relatives(self,start,end):
  raw=self.read(start,end-start,True)
  for op in (0xe8,0xe9):
   pos=raw.find(bytes([op]))
   while pos>=0 and pos+5<=len(raw):
    rel=struct.unpack_from('<i',raw,pos+1)[0]
    yield start+pos,start+pos+5+rel
    pos=raw.find(bytes([op]),pos+1)

def signed_target(site,buf):
 if len(buf)!=5 or buf[0] not in (0xe8,0xe9):raise ValueError('NOT_REL32_CALL_JUMP')
 return site+5+struct.unpack_from('<i',buf,1)[0]

def verify(exe:Path):
 h=hashlib.sha256()
 with exe.open('rb') as f:
  for part in iter(lambda:f.read(4<<20),b''):h.update(part)
 if h.hexdigest()!=SHA:raise ValueError('EXE_SHA256_MISMATCH')
 with exe.open('rb') as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as mm:
  p=PE(mm)
  for label,(site,bytestr) in OPCODES.items():
   if p.read(site,len(bytestr)//2,True)!=bytes.fromhex(bytestr):
    raise ValueError('ORIGINAL_OPCODE_CHANGED:'+label)
  for label,(site,dest) in EDGES.items():
   if signed_target(site,p.read(site,5,True))!=dest:
    raise ValueError('ORIGINAL_EDGE_CHANGED:'+label)
  for label,(slot,dest) in VTABLES.items():
   if p.ptr(slot)!=dest:raise ValueError('ACTION_VTABLE_CHANGED:'+label)
  if len(p.funcs)!=209180:raise ValueError('UNEXPECTED_UNWIND_FUNCTION_COUNT')
  funs={}
  motor_raw_edges=[]
  for addr in AUDITED_RECEIVE_FUNCS:
   bnd=p.func(addr)
   if not bnd or bnd[0]!=addr:raise ValueError('BAD_FUNCTION_ENTRY:'+hex(addr))
   funs[hex(addr)]=[hex(x) for x in bnd]
   for site,dest in p.relatives(*bnd):
    if dest in SEPARATE_MOTOR_FUNCS:
     motor_raw_edges.append([hex(site),hex(dest)])
  # The audited group packet passes +0x26 and option flag; proof at original
  # creation site in sibling audit. No direct edge from these four functions
  # to unrelated +0x7F8/+0x818 motor-path routines is found here.
  if motor_raw_edges:raise ValueError('UNEXPECTED_MOTOR_DIRECT_EDGE')
  return {
   'binary_sha256':SHA,'grade':'EXACT_BINARY_STATIC_WITH_CONDITIONAL_REACHABILITY',
   'exception_function_count':len(p.funcs),'machine_guard_count':len(OPCODES),
   'verified_native_edges':len(EDGES),'verified_action_vtable_slots':len(VTABLES),
   'group_fanout':{'rva':hex(0x030d5490),'actor_loop_start':hex(0x030d54d5),
     'target_generation_before_loop':hex(0x030d54ca),'per_actor_virtual_call':hex(0x030d550f),
     'postprocessing_after_loop':hex(0x030d5522)},
   'pose_writer':{'rva':hex(0x0315ec98),'writes_member_current_pose':
     ['+0x88 X/Y','+0x90 Z','+0xB0 facing'],'places':
     [hex(0x0315f311),hex(0x0315f327),hex(0x0315f33f),hex(0x0315f34d)]},
   'status_subaction':{'vtable':hex(0x03914618),'actor_tick':hex(0x03081eb4),
     'dispatch':hex(0x03080f4c),'individual_v8':hex(0x03080f71),
     'individual_v10':hex(0x03080f84),'increment_local_counter':hex(0x03080f87),
     'note':'0x03080F4C receives &actor+0x328, so +0x154 relative to argument is actor+0x47C, NOT actor+0x154'},
   'cohesion_measure':{'group_rva':hex(0x030d572c),'same_transform_as_receiver':hex(0x0307f5c8),
     'counts_far_members':True,'computes_mean_distance':True,
     'marks_timestamp_on_average_below_threshold':True,
     'is_NOT_all_members_exact_arrival_barrier':True,
     'other_unlinked_gate_inspects_far_count_at':hex(0x0327e644),
     'other_gate_condition_not_proven_V3_MOVE':True},
   'separate_motor_path':{'goal_copy_rva':hex(0x03071e04),'motor_update_rva':hex(0x03071f20),
     'current_motion_writer_rva':hex(0x0311954c),'direct_edges_from_audited_receivers':motor_raw_edges,
     'limit':'No E8/E9 into these functions in bounded receiver code; indirect calls/callers not excluded.'},
   'audited_receivers':funs,
   'limits':['Old V3 probe had zero hits at 0x030D5490, so runtime execution is not established',
     'Synchronous actor call is not a proof of same-frame physical steering',
     'Pose write does NOT by itself prove overwrite of independently maintained main motor target',
     'Per-actor subaction tick is gated; not proven used by all 38 actor types or all Move episodes',
     'A group mean-distance timestamp is not a proven queued Shift transition gate',
     'No native patch is authorized by this read-only audit'],
   'native_patch_authorized':False,'windows_tested':False,'wh3_fix_verified':False,
  }

def main():
 q=argparse.ArgumentParser(description=__doc__)
 q.add_argument('--exe',type=Path,required=True);q.add_argument('--out',type=Path,required=True)
 a=q.parse_args()
 if a.exe.resolve()==a.out.resolve():q.error('output cannot overwrite game EXE')
 try:
  result=verify(a.exe)
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  print('STATIC PASS:',len(OPCODES),'opcode guards;',len(EDGES),'E8/E9;',len(VTABLES),'vtables; no patch')
  return 0
 except (OSError,ValueError,struct.error) as e:
  print('EXACT_AUDIT_FAILED:',e,file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())