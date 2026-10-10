#!/usr/bin/env python3
"""Exact WH3 binary RMB-vs-queued-MOVE route-state producer/consumer proof.

Static actual x64 instructions, no Hook, no game execution, no fabricated V3 branch.

The distinction is:
  REPLACE RMB: new MOVE +0xA0 cleared; newly created route-state = state 0.
  queued MOVE successor (only eligible branch): SAME state object (refcounted),
      state 1 and new pending route data +0x120...+0x148.
  Native state=1 planner copies pending into active +0x60...+0xA8, then
      re-runs native route solver, preserving the *object identity* of state.
Do not mistake this for different per-model motor algorithms or proven collision cause.
"""
from __future__ import annotations
import argparse,bisect,hashlib,json,mmap,struct,sys
from pathlib import Path
SHA = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
BASE=0x140000000
# The exact machine instructions verify each labeled writer or reader. No pattern-only matching.
GUARDS={
 'issuer_saves_enqueue_flag':(0x030323FC,'458af1'),
 'issuer_passes_enqueue_flag':(0x030326BB,'418ad6'),
 'move_constructor_zero_shared_state_ptr':(0x030090E7,'4883a7a000000000'),
 'move_worker_reads_optional_inherited_state':(0x03025DE1,'4d8b1e'),
 'move_worker_test_optional_inherited_state':(0x03025DE4,'4d85db'),
 'move_worker_reuse_check_state25':(0x03025DE9,'41387b25'),
 'move_worker_compare_width_against_old_state':(0x03025E03,'f3410f108ba0000000'),
 'move_worker_reuse_tolerance_001':(0x03025E2C,'0f2f05c96e8f00'),
 'move_worker_discard_old_reference':(0x03025E35,'41ff4b18'),
 'move_worker_null_old_state':(0x03025E39,'49893e'),
 'move_scalar_source_flag':(0x0301C1B4,'f6819a00000004'),
 'move_scalar_source_explicit':(0x0301C1BD,'f30f108180000000'),
 'move_scalar_source_route_pointer':(0x0301C1CE,'488b8170020000'),
 'move_scalar_source_route_width':(0x0301C1D5,'f30f104040'),
 'queue_successor_min_two':(0x03044539,'83bb102d000001'),
 'queue_successor_get_current':(0x0304455F,'488b01'),
 'queue_successor_get_eligibility_current_v40':(0x03044562,'ff5040'),
 'queue_successor_get_eligibility_next_v38':(0x03044596,'ff5038'),
 'queue_successor_test_eligibility':(0x03044599,'84c0'),
 'queue_successor_increments_shared_ref':(0x0304459D,'ff4618'),
 'queue_successor_virtual_transfer_call':(0x030445AB,'ff5048'),
 'queue_successor_native_pop':(0x030445B1,'e85ab7f0ff'),
 'transfer_sets_state_one':(0x030408CF,'c7422001000000'),
 'transfer_pending_block_120':(0x030408EC,'0f118220010000'),
 'transfer_pending_block_130':(0x030408F8,'0f118a30010000'),
 'transfer_pending_block_140':(0x030408FF,'0f118240010000'),
 'transfer_attaches_same_ptr_to_next_move':(0x03040906,'498991a0000000'),
 'fresh_state_ctor_sets_zero':(0x030EE88D,'44894120'),
 'fresh_state_ctor_zero_160':(0x030EE92B,'4d898260010000'),
 'native_planner_state_switch':(0x0311DEA7,'8b4a20'),
 'native_planner_state0_branch':(0x0311DEB7,'0f843b080000'),
 'native_planner_state1_branch':(0x0311DEC0,'0f84b2060000'),
 'state1_activate_120_to_60_load':(0x0311E5C2,'0f108720010000'),
 'state1_activate_120_to_60_store':(0x0311E5CF,'0f114760'),
 'state1_activate_130_to_70_load':(0x0311E5D3,'0f108f30010000'),
 'state1_activate_130_to_70_store':(0x0311E5DA,'0f114f70'),
 'state1_activate_120_to_80_store':(0x0311E5E5,'0f118780000000'),
 'state1_activate_130_to_90_store':(0x0311E5F3,'0f118f90000000'),
 'state1_activate_140_to_a0_load':(0x0311E5FA,'8b8740010000'),
 'state1_activate_140_to_a0_store':(0x0311E600,'8987a0000000'),
 'state1_activate_144_to_a4_load':(0x0311E606,'8b8744010000'),
 'state1_activate_144_to_a4_store':(0x0311E60C,'8987a4000000'),
 'state1_activate_148_to_a8_load':(0x0311E612,'8b8748010000'),
 'state1_activate_148_to_a8_store':(0x0311E618,'8987a8000000'),
 'state1_solver_load_existing_nested':(0x0311E829,'4c8baa60010000'),
 'state1_solver_uses_active_a0':(0x0311E834,'f3410f104760'),
 'state1_solver_dispatches_spatial_path':(0x0311EAC7,'e8940affff'),
 'fresh_planner_path_initialization':(0x0311E733,'e8d4830000'),
 'state0_origin_optional_cached_flag':(0x03126B2A,'80b9c000000000'),
 'state0_origin_from_state_if_cached':(0x03126B51,'8b81a0000000'),
 'state0_origin_load_current_geometry':(0x03126B93,'e8504dfbff'),
 'group_current_geometry_source_flag':(0x030DB8F3,'4180b8083e000000'),
 'group_current_cached_x':(0x030DB8FD,'418b80103e0000'),
 'group_fallback_native_x':(0x030DB92E,'8b8138010000'),
 'reused_state_planner_reset':(0x0311E57B,'e878a1feff'),
 'fresh_state_planner_reset':(0x0311E6FB,'e8f89ffeff'),
 'native_reset_replaces_nested_route_context':(0x03108808,'4c898660010000'),
 'native_route_builder_from_planner':(0x03129092,'e8054afdff'),
 'common_group_target_segment_builder':(0x030D55F5,'e8a2840200'),
 'common_group_fanout_after_builder':(0x030D5603,'e888feffff'),
}
EDGES={
 'enqueue_selects_queue_management':(0x030326BE,0x02F50410),
 'enqueue_creates_same_move_type':(0x030326E4,0x030090BC),
 'move_worker_builds_route':(0x03025E91,0x0301287C),
 'move_worker_reuses_or_invalidates_state':(0x03025DFA,0x0311C634),
 'move_worker_original_scalar_from_move_or_route':(0x03025DD2,0x0301C1B4),
 'move_worker_builds_native_task':(0x030260AF,0x02F2C734),
 'fresh_state_from_planner':(0x0310EDA7,0x030EE850),
 'fresh_state_activate_state_machine':(0x0310EDF1,0x0311DE74),
 'native_planner_initial_route':(0x0311E733,0x03126B0C),
 'native_initial_position_source_pointer':(0x03126B86,0x031268BC),
 'native_initial_position_group_or_fallback':(0x03126B93,0x030DB8E8),
 'native_planner_fresh_reset_context':(0x0311E6FB,0x031086F8),
 'native_planner_reused_reset_context':(0x0311E57B,0x031086F8),
 'native_state1_recomputes_auxiliary':(0x0311E61E,0x0310EB80),
 'native_state1_uses_shared_route_solver':(0x0311E636,0x0311E80C),
 'native_state0_uses_shared_route_solver':(0x0311E772,0x0311E80C),
 'route_solver_uses_original_route_compute':(0x0311EAC7,0x0310F560),
 'group_dispatch_uses_native_segments':(0x030D55F5,0x030FDA9C),
 'group_dispatch_sends_member_records':(0x030D5603,0x030D5490),
 'group_fanout_copies_native_payload':(0x030D54FC,0x02F5F868),
 'planner_builds_route_segments':(0x03129092,0x030FDA9C),
 'planner_explicit_state_tick':(0x03128F1D,0x0311DE74),
 'task_tick_can_broadcast_group':(0x02F56404,0x03279E40),
 'native_broadcast_to_fanout_adapter':(0x03279EB3,0x030D554C),
}
FLOAT_CONSTANTS={
 'native_reuse_tolerance_001':(0x0391CCFC,0.01),
 'native_reference_half_width_05':(0x0391CBC8,0.5),
}
VTABLE={
 'MOVE_work_virtual_08':(0x0390B4F0+0x08,0x03025D70),
 'MOVE_successor_transfer_virtual_48':(0x0390B4F0+0x48,0x03040864),
 'MOVE_provider_virtual_40':(0x0390B4F0+0x40,0x03039FB0),
 'MOVE_task_virtual_10':(0x03ABBE18+0x10,0x02F561E8),
}
class PE:
 def __init__(self,data):
  self.data=data
  if len(data)<1024 or data[:2]!=b'MZ':raise ValueError('NOT_MZ')
  nt=struct.unpack_from('<I',data,0x3c)[0]
  if nt+24>len(data) or data[nt:nt+4]!=b'PE\0\0':raise ValueError('INVALID_PE')
  machine,ns=struct.unpack_from('<HH',data,nt+4)
  osz=struct.unpack_from('<H',data,nt+20)[0];opt=nt+24
  if machine!=0x8664 or not 1<=ns<=96 or osz<144 or opt+osz+40*ns>len(data):raise ValueError('NOT_AMD64')
  if struct.unpack_from('<H',data,opt)[0]!=0x20b or struct.unpack_from('<Q',data,opt+24)[0]!=BASE:raise ValueError('WRONG_PE_IMAGE_BASE')
  ex,exsize=struct.unpack_from('<II',data,opt+112+3*8)
  self.sections=[]
  for i in range(ns):
   p=opt+osz+40*i
   _,rva,n,off=struct.unpack_from('<IIII',data,p+8)
   exec_=bool(struct.unpack_from('<I',data,p+36)[0]&0x20000000)
   if n and (off>len(data) or n>len(data)-off):raise ValueError('TRUNCATED_SECTION')
   self.sections.append((rva,n,off,exec_))
  if exsize<12 or exsize%12:raise ValueError('BAD_EXCEPTION_DIRECTORY')
  self.funcs=list(struct.iter_unpack('<III',self.read(ex,exsize)))
  if any(self.funcs[i][0]>=self.funcs[i+1][0] for i in range(len(self.funcs)-1)):raise ValueError('UNSORTED_EXCEPTION_TABLE')
  self.starts=[r[0] for r in self.funcs]
 def read(self,rva,length,executable=False):
  for r,n,off,x in self.sections:
   if r<=rva and rva+length<=r+n:
    if executable and not x:raise ValueError('NOT_EXECUTABLE:'+hex(rva))
    return bytes(self.data[off+rva-r:off+rva-r+length])
  raise ValueError('RVA_UNMAPPED:'+hex(rva))
 def owner(self,rva):
  i=bisect.bisect_right(self.starts,rva)-1
  if i<0 or not self.funcs[i][0]<=rva<self.funcs[i][1]:raise ValueError('NO_FUNCTION_OWNER:'+hex(rva))
  return self.funcs[i][:2]
def e8_target(site,b):
 if len(b)!=5 or b[0]!=0xe8:raise ValueError('NOT_CALL_E8:'+hex(site))
 return site+5+struct.unpack_from('<i',b,1)[0]
def original_contract(exe):
 hasher=hashlib.sha256()
 with exe.open('rb') as f:
  for part in iter(lambda:f.read(4<<20),b''):hasher.update(part)
 sha=hasher.hexdigest()
 if sha!=SHA:raise ValueError('EXE_SHA256_MISMATCH')
 with exe.open('rb') as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as mapped:
  pe=PE(mapped)
  checked=[];calls=[];vt=[]
  for name,(site,hx) in GUARDS.items():
   b=bytes.fromhex(hx)
   if pe.read(site,len(b),True)!=b:raise ValueError('ORIGINAL_INSTRUCTION_MISMATCH:'+name)
   # x64 pdata normally covers non-leaf functions; tiny leaf methods can lack entries.
   try:owner=hex(pe.owner(site)[0])
   except ValueError:owner=None
   checked.append({'name':name,'rva':hex(site),'bytes':b.hex(),'pdata_function_start':owner})
  for name,(site,dest) in EDGES.items():
   b=pe.read(site,5,True)
   if e8_target(site,b)!=dest:raise ValueError('ORIGINAL_CALL_TARGET_MISMATCH:'+name)
   bounds=pe.owner(site)
   calls.append({'name':name,'site':hex(site),'target':hex(dest),'function_start':hex(bounds[0])})
  consts=[]
  for name,(site,expected) in FLOAT_CONSTANTS.items():
   actual=struct.unpack('<f',pe.read(site,4))[0]
   if abs(actual-expected)>1e-6:raise ValueError('NATIVE_SCALAR_MISMATCH:'+name)
   consts.append({'name':name,'site':hex(site),'float_value':actual})
  for name,(slot,dest) in VTABLE.items():
   p=struct.unpack('<Q',pe.read(slot,8))[0]
   if p!=BASE+dest:raise ValueError('ORIGINAL_VTABLE_MISMATCH:'+name)
   vt.append({'name':name,'slot':hex(slot),'target_rva':hex(dest)})
  # Both state-0 and state-1 callsites are in the same native state dispatcher.
  for pos in [0x0311E733,0x0311E5C2,0x0311E636,0x0311E772]:
   if pe.owner(pos)[0]!=0x0311DE74:raise ValueError('STATE_BRANCH_OBJECT_IDENTITY_MISMATCH')
  # Native group route and planner share route-segment builder but NOT proven same runtime call instance.
  assert EDGES['group_dispatch_uses_native_segments'][1]==EDGES['planner_builds_route_segments'][1]
  return {
   'schema':'bsc.wh3_903.rmb_queued_native_state_rebase.v1','grade':'EXACT_SHA_STATIC_ORIGINAL_MACHINE_CODE',
   'source_exe_sha256':sha,'image_base':hex(BASE),'exception_functions':len(pe.funcs),
   'machine_instruction_guards':checked,'direct_e8_calls':calls,'vtables':vt,'native_constants':consts,
   'proven_first_divergence':{
    'rmb_replace': 'native R9B=0 queue clear; MOVE+0xA0=NULL; new state 0; state+0x160 initially null',
    'queued_successor_eligible':'state object refcount++; MOVE virtual+0x48 assigns SAME state object to successor and sets state=1; successor geometry staged at +0x120/+0x130/+0x140',
    'state1_native_consumption':'pending blocks +0x120/+0x130 moved into +0x60/+0x70 and +0x80/+0x90; +0x140/+0x144/+0x148 moved into +0xA0/+0xA4/+0xA8; native route solver called',
    'fresh_state0_native_consumption':'initial route setup 0x03126B0C and same solver 0x0311E80C, without the state1 pending-block copy; conditional original initial-position helper 0x030DB8E8 selects live group cached +0x3E10 if flag +0x3E08, otherwise input +0x138',
    'planner_nested_state':'both state0 and state1 call 0x031086F8, which writes state+0x160 to a reset/reinitialized nested context; old nested route is NOT shown to survive unchanged',
    'reuse_gate':'MOVE work keeps inherited +0xA0 only if condition 0x0311C634 and tolerance abs(new scalar - (state+0xA0-state+0xA4)) <= 0.01; otherwise decrements refcount and clears +0xA0. Scalar source is MOVE+0x80 when flag +0x9A &4, else UnitRoot route descriptor +0x270/+0x40' 
   },
   'limits':[
    'This is the exact coded RMB/queued difference, NOT a proof that state rebasing alone causes the V3 observed compression.',
    'No user V3 trace of state+0x120/+0x160 or 48-byte generated per-member targets is available.',
    'The native reuse gate can discard state before next MOVE work: queued does NOT imply reuse always happens.',
    'Native state0 may also use cached fields when +0xC0 is set; do not claim all RMB starts always use live group origin.',
    'Both ordinary RMB and queued Shift ultimately use overlapping native movement/formation routines; distinct effective route inputs are sufficient to produce different trajectories.',
    '0x030D554C and 0x03128E80 call the same route-segment builder but this does not certify same runtime route object across their calls.',
    'Both state0 and state1 call 0x031086F8 to refresh the nested context, so no proof of permanent old-route geometry reuse.',
    'Do not enable the previous skip-state-inheritance DLL; original progressive turning may depend on rebase.',
   ],'patch_authorized':False,'windows_tested':False,'wh3_tested':False}

def native_inherited_state_remains(scalar,prev_a0,prev_a4,state25=0,extra_gate=True):
 """Finite-float model of verified 0x03025DE9–0x03025E39 gates."""
 if state25!=0 or not extra_gate:return False
 if not all(__import__('math').isfinite(x) for x in (scalar,prev_a0,prev_a4)):return False
 return abs(scalar-(prev_a0-prev_a4))<=0.01

def model_fresh():
 """Simple struct offsets mirroring exact x64 stores, not physics or native runtime."""
 memory=bytearray(0x200)
 struct.pack_into('<I',memory,0x20,0)
 struct.pack_into('<Q',memory,0x160,0)
 return memory

def model_queued_rebase(memory,pending):
 """Mirrors the original constructor/transfer/state=1 load-store spans."""
 if len(memory)<0x200 or len(pending)!=0x30:raise ValueError('BAD_STRUCT_OR_PAYLOAD')
 struct.pack_into('<I',memory,0x20,1)
 memory[0x120:0x150]=pending
 # state1: +0x120..0x13f twice, +0x140..+0x14b once.
 # The REAL native code also calls 0x031086F8 to replace nested +0x160;
 # the structural toy model stops before that reset, not a gameplay replay.
 memory[0x60:0x80]=memory[0x120:0x140]
 memory[0x80:0xa0]=memory[0x120:0x140]
 memory[0xa0:0xac]=memory[0x140:0x14c]
 return memory

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',required=True,type=Path);p.add_argument('--report',required=True,type=Path)
 a=p.parse_args()
 if a.exe.resolve()==a.report.resolve():p.error('report cannot overwrite original EXE')
 try:
  result=original_contract(a.exe)
  a.report.parent.mkdir(parents=True,exist_ok=True)
  a.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 except (ValueError,OSError,struct.error) as err:
  print('RMB_QUEUE_ORIGINAL_AUDIT_BLOCKED:',err,file=sys.stderr);return 2
 print('EXACT_ORIGINAL_BINARY_PASS',len(GUARDS),'opcodes',len(EDGES),'calls',len(VTABLE),'vtables; NO PATCH')
 return 0
if __name__=='__main__':sys.exit(main())