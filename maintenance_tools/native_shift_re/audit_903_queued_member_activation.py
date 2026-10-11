#!/usr/bin/env python3
"""Read-only WH3 9.0.3: RMB replace / queued MOVE handoff / member task split.

Static EXE dataflow; NEVER assumes a branch was taken in a particular battle.
No writes, no detours, no experiment requiring WH3 gameplay.
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

SHA256 = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
IMAGE_BASE = 0x140000000
# Each guard begins on a decoded machine-instruction boundary of the pinned EXE.
# 0x030445xx (not 0x03045xx) is the native queue's special state-transfer block.
INSTRUCTIONS = {
    'issue_queue_flag_from_r9b': (0x030323FC,'458af1'),
    'issue_queue_policy_call': (0x030326BE,'e84dddf1ff'),
    'issue_original_move_constructor': (0x030326E4,'e8d369fdff'),
    'new_move_state_null': (0x030090E7,'4883a7a000000000'),
    'provider_old_move_state': (0x03039FB4,'488b91a0000000'),
    'provider_requires_state4': (0x03039FC0,'837a2004'),
    'provider_requires_flag24': (0x03039FC6,'807a2400'),
    'provider_requires_nonnull_158': (0x03039FCC,'4883ba5801000000'),
    'provider_group_flag_call': (0x03039FE5,'e8aa97d2ff'),
    'group_flag_a08_check': (0x02D63796,'3881080a0000'),
    'group_flag_928_load': (0x02D6379E,'8a8128090000'),
    'group_flag_return': (0x02D637A6,'0f94c0'),
    'next_move_handoff_accepts_unconditionally': (0x008D3350,'b001c3'),
    'special_at_least_two_orders': (0x03044539,'83bb102d000001'),
    'special_successor_accepts_v38': (0x03044596,'ff5038'),
    'special_old_state_incref': (0x0304459D,'ff4618'),
    'special_next_move_handoff_v48': (0x030445AB,'ff5048'),
    'special_native_pop': (0x030445B1,'e85ab7f0ff'),
    'ordinary_unit_move_completion_count': (0x030440FC,'83b84002000000'),
    'ordinary_unit_move_completion_result': (0x03044103,'0f94c0'),
    'native_unit_task_tick_v10': (0x0304357D,'ff5210'),
    'group_strategy_target_generator': (0x030D54CA,'41ff5248'),
    'group_record_copy_to_packet': (0x030D54FC,'e867a3e8ff'),
    'group_load_member_vector': (0x030D54D5,'488b4728'),
    'group_stride48_per_index': (0x030D54D9,'4c8d0476'),
    'group_record_vector_base': (0x030D54E6,'4c03442440'),
    'group_load_member_i': (0x030D54F0,'488b1cf0'),
    'group_loop_increment_i': (0x030D5515,'ffc6'),
    'group_loop_bound_membercount': (0x030D5517,'3b7724'),
    'group_loop_next': (0x030D551A,'72b9'),
    'group_send_packet_member_v368': (0x030D550F,'ff9068030000'),
    'packet_direct_flag_0x26': (0x02F5F8BD,'c6435026'),
    'receiver_checks_flag_0x20': (0x0306BA2F,'f6425020'),
    'receiver_skips_deferred_on_0x20': (0x0306BA33,'7530'),
    'receiver_deferred_member_task_ctor': (0x0306BA5B,'e8683defff'),
    'receiver_member_direct_v100': (0x0306BB0E,'41ff9300010000'),
    'receiver_member_direct_ve8': (0x0306BB44,'41ff93e8000000'),
    'deferred_task_vtable_init': (0x02F5F7DD,'488d0534669a00'),
    'deferred_task_own_condition': (0x02F83B2A,'80b99c00000000'),
    'deferred_task_own_done_byte': (0x02F83B61,'c6432001'),
    'common_member_target_handler': (0x0307328B,'e808ba0e00'),
    'member_target_old_resource_cleanup': (0x0315EE17,'e8e4560000'),
    'member_target_list_unlink': (0x0315EE1F,'e844560000'),
    'member_target_pointer20_reset': (0x0315EE24,'4c896620'),
    'member_target_pointer30_reset': (0x0315EE2B,'4c896630'),
    'active_move_new_task_constructor': (0x030260AF,'e88066f0ff'),
    'active_task_conditional_group_dispatch': (0x02F56404,'e8373a3200'),
    'group_dispatch_to_member_adapter': (0x03279EB3,'e894b6e5ff'),
    'adapter_to_member_group_fanout': (0x030D5603,'e888feffff'),
    # ALL 36 original common actor v+E8 handlers ultimately enter
    # 0x03073224. That function DIRECTLY handles new target and
    # immediately tail-jumps into independent actor-local route/cache refresh.
    'alternate_actor_wrapper_to_common': (0x02DCD724,'e8fb5a2a00'),
    'special_actor_wrapper_to_common_a': (0x02F4F940,'e8df381200'),
    'special_actor_wrapper_to_common_b': (0x02F4F992,'e88d381200'),
    'path_actor_wrapper_to_common': (0x0311C951,'e8ce68f5ff'),
    'common_actor_tail_to_cache_refresh': (0x030732C0,'e90f3cfeff'),
    'actor_cache_copy_first_half': (0x03056F15,'410f1102'),
    'actor_cache_copy_second_half': (0x03056F1D,'410f114a10'),
    'actor_cache_previous_path_read': (0x03056F28,'4c8b8b30090000'),
    'actor_cache_old_context_compare': (0x03056F4A,'4c3b8908010000'),
    'actor_cache_context_equal_branch': (0x03056F51,'750d'),
    'actor_cache_actor_mode_check': (0x03056F53,'8b8304010000'),
    'actor_cache_mode_outside_1_2_refresh': (0x03056F5E,'773a'),
    'actor_cache_geometry_predicate_jump': (0x03056F96,'84c07546'),
    'actor_cache_refresh_new_path_write': (0x03056FB7,'48898330090000'),
    'actor_cache_new_derived_token_write': (0x03056FC7,'48898338090000'),
    'actor_cache_clear_old_derived_token': (0x03056FD0,'4883a33809000000'),
    'actor_cache_clear_old_path': (0x03056FD8,'4883a33009000000'),
    'alternate_actor_position_reference': (0x0311C956,'488d9788000000'),
    'alternate_actor_local_spline_reference': (0x0311C960,'488d8f600b0000'),
    'special_actor_local_geometry_reference': (0x02F4F945,'488d9510090000'),
    'special_actor_local_cache_reference': (0x02F4F950,'488d8d800b0000'),
    # Previously described as "alternate member dispatch", actually a
    # 0x1C-stride vector APPENDER of spatial/route records, not a soldier call.
    'alternate_28byte_record_stride_alloc': (0x02DED14D,'486bc81c'),
    'alternate_28byte_record_stride_append': (0x02DED1EE,'486bc81c'),
    'alternate_28byte_record_count_inc': (0x02DED21F,'ff4304'),
    'alternate_record_facing_copy': (0x02E0B029,'66895f0c'),
    'alternate_record_coord_copy': (0x02E0B032,'f30f114710'),
}
DIRECT_CALLS = {
    'unit_issue_policy': (0x030326BE,0x02F50410),
    'unit_issue_move_ctor': (0x030326E4,0x030090BC),
    'old_move_handoff_provider_group_flag': (0x03039FE5,0x02D63794),
    'special_native_pop_old_move': (0x030445B1,0x02F4FD10),
    'group_target_payload_copy': (0x030D54FC,0x02F5F868),
    'receiver_make_individual_deferred_task': (0x0306BA5B,0x02F5F7C8),
    'mode0_member_direct_target': (0x0307328B,0x0315EC98),
    'member_target_release_references': (0x0315EE17,0x03164500),
    'member_target_detach_old_list': (0x0315EE1F,0x03164468),
    'move_worker_task_ctor': (0x030260AF,0x02F2C734),
    'move_task_conditional_group': (0x02F56404,0x03279E40),
    'group_to_target_adapter': (0x03279EB3,0x030D554C),
    'target_adapter_to_member_fanout': (0x030D5603,0x030D5490),
    'other_actor_calls_common_handler': (0x02DCD724,0x03073224),
    'special_actor_calls_common_handler_first': (0x02F4F940,0x03073224),
    'special_actor_calls_common_handler_again': (0x02F4F992,0x03073224),
    'spline_actor_calls_common_handler': (0x0311C951,0x03073224),
    'special_actor_builds_local_curve': (0x02F4F957,0x02F43218),
    'spline_actor_builds_local_curve': (0x0311C96B,0x03119E74),
    'common_actor_refreshes_target_cache': (0x03056F01,0x03057D24),
    'actor_cache_checks_spatial_list': (0x03056F91,0x018325EC),
    'actor_cache_refresh_uses_route_selector': (0x03056FB2,0x0312D088),
    'route_selector_converts_local_xy': (0x0312D0A1,0x0311D0CC),
    'route_selector_calls_original_policy': (0x0312D0C6,0x0312D0D0),
    'route_selector_fallback_global_context': (0x0312D114,0x02F8AB54),
    'alternate_unit_producer_mode0_first': (0x0301385E,0x030C9A64),
    'alternate_unit_producer_make_record_first': (0x0301389E,0x02E0AFDC),
    'alternate_unit_producer_append_record_first': (0x030138AD,0x02DED114),
    'alternate_unit_producer_mode0_second': (0x03013B5C,0x030C9A64),
    'alternate_unit_producer_make_record_second': (0x03013B9C,0x02E0AFDC),
    'alternate_unit_producer_append_record_second': (0x03013BAB,0x02DED114),
}
VTABLES = {
    'move_work_v8': (0x0390B4F0 + 0x08,0x03025D70),
    'move_complete_v10': (0x0390B4F0 + 0x10,0x030440F8),
    'move_accept_state_handoff_v38': (0x0390B4F0 + 0x38,0x008D3350),
    'move_shared_state_provider_v40': (0x0390B4F0 + 0x40,0x03039FB0),
    'move_receive_shared_state_v48': (0x0390B4F0 + 0x48,0x03040864),
    'unit_move_native_task_tick_v10': (0x03ABBE18 + 0x10,0x02F561E8),
    'separate_member_task_tick_v10': (0x03905E18 + 0x10,0x02F83B24),
}
RECEIVERS = {0x0306B9F0,0x0306B9CC,0x03117CE0}
EXPECTED_MEMBER_VE8 = {0x03073224:28,0x02DCD63C:3,0x02F4F910:4,0x0311C92C:1}

def e8_destination(rva, raw):
    if len(raw) != 5 or raw[0] != 0xE8: raise ValueError('NOT_DIRECT_E8')
    return rva+5+struct.unpack_from('<i',raw,1)[0]

def deferred_member_task_path(packet_flag50: int, context_mode_matches: bool) -> bool:
    """Exact receiver 0x0306BA2B-0x0306BA65 branch predicate, NOT movement simulation."""
    return not context_mode_matches and not bool(packet_flag50 & 0x20)

def local_cache_action(packet_requires_clear: bool, prior_cache_present: bool,
                       old_context_matches_current: bool, member_mode: int,
                       geometry_check_returns_one: bool) -> str:
    """Branch reconstruction ONLY for 0x03056F22..0x03056FDF.

    Return strings describe the original per-ACTOR cache policy, not tested
    game-crowding behavior. The geometry predicate is opaque in this model.
    """
    if packet_requires_clear: return 'clear_cache'
    if not prior_cache_present: return 'refresh_cache'
    if old_context_matches_current and member_mode not in (1, 2):
        return 'refresh_cache'
    if geometry_check_returns_one: return 'retain_old_cache'
    return 'refresh_cache'


def local_special_transfer_predicate(shared_ready: bool, group_flag_ok: bool, has_successor: bool) -> bool:
    """Local 0x03039FB0 + 0x03044539/96 gate only; excludes outer reachability checks."""
    return shared_ready and group_flag_ok and has_successor

class PinnedPE:
    def __init__(self, mm):
        self.mm=mm
        if len(mm)<0x100 or mm[:2]!=b'MZ': raise ValueError('NOT_MZ')
        nt=struct.unpack_from('<I',mm,0x3C)[0]
        if nt+24>len(mm) or mm[nt:nt+4]!=b'PE\0\0': raise ValueError('NOT_PE')
        machine,n=struct.unpack_from('<HH',mm,nt+4)
        sizeopt=struct.unpack_from('<H',mm,nt+20)[0]
        opt=nt+24
        if machine != 0x8664 or not 1<=n<=96 or sizeopt<144 or opt+sizeopt+40*n>len(mm):
            raise ValueError('NOT_AMD64')
        if struct.unpack_from('<H',mm,opt)[0] != 0x20B: raise ValueError('NOT_PE32_PLUS')
        if struct.unpack_from('<Q',mm,opt+24)[0] != IMAGE_BASE: raise ValueError('IMAGE_BASE_MISMATCH')
        self.sections=[]
        for i in range(n):
            q=opt+sizeopt+40*i
            name=bytes(mm[q:q+8]).split(b'\0',1)[0].decode('ascii','replace')
            _,rva,nraw,raw=struct.unpack_from('<IIII',mm,q+8)
            flags=struct.unpack_from('<I',mm,q+36)[0]
            if nraw and (raw+nraw>len(mm)):raise ValueError('TRUNCATED_SECTION')
            self.sections.append((name,rva,nraw,raw,bool(flags&0x20000000)))
    def read(self,rva,n,executable=None):
        if n<1: raise ValueError('BAD_LENGTH')
        for name,r,size,raw,x in self.sections:
            if r<=rva and rva+n<=r+size:
                if executable is not None and x!=executable:
                    raise ValueError('SECTION_PERMISSION_MISMATCH:'+name)
                return bytes(self.mm[raw+rva-r:raw+rva-r+n])
        raise ValueError('RVA_NOT_MAPPED:'+hex(rva))
    def pointer_rva(self,rva):
        p=struct.unpack('<Q',self.read(rva,8))[0]
        return p-IMAGE_BASE
    def member_vtable_census(self):
        # Member vtables have constructor-confirmed group getter +0x3F8 = 0x008F37B0.
        needle=struct.pack('<Q',IMAGE_BASE+0x008F37B0)
        tables={}
        for name,rva,size,raw,x in self.sections:
            if x or size==0:continue
            data=self.mm[raw:raw+size]
            off=data.find(needle)
            while off>=0:
                vt=rva+off-0x3F8
                if vt>=rva and vt%8==0 and vt+0x400<=rva+size:
                    rec=self.pointer_rva(vt+0x368)
                    if rec in RECEIVERS:
                        tables[vt]=(rec,self.pointer_rva(vt+0xE8))
                off=data.find(needle,off+1)
        return tables

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as fd:
        for b in iter(lambda:fd.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def audit(path):
    fingerprint=sha(path)
    if fingerprint!=SHA256: raise ValueError('EXE_SHA256_MISMATCH:'+fingerprint)
    with path.open('rb') as fd, mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ) as mm:
        pe=PinnedPE(mm)
        guards=[]
        for key,(site,hx) in INSTRUCTIONS.items():
            actual=pe.read(site,len(hx)//2,executable=True)
            if actual.hex()!=hx: raise ValueError('ORIGINAL_CODE_CHANGED:'+key)
            guards.append({'name':key,'rva':hex(site),'bytes':hx})
        edges=[]
        for key,(site,target) in DIRECT_CALLS.items():
            actual=e8_destination(site,pe.read(site,5,executable=True))
            if actual!=target:raise ValueError('ORIGINAL_E8_CHANGED:'+key)
            edges.append({'name':key,'at':hex(site),'to':hex(target)})
        v=[]
        for key,(slot,target) in VTABLES.items():
            actual=pe.pointer_rva(slot)
            if actual!=target:raise ValueError('ORIGINAL_VTABLE_CHANGED:'+key)
            v.append({'name':key,'slot':hex(slot),'to':hex(target)})
        types=pe.member_vtable_census()
        recvcount=Counter(t[0] for t in types.values())
        if len(types)!=38 or recvcount[0x0306B9F0]!=36:
            raise ValueError('MEMBER_DISPATCH_TYPES_MISMATCH:'+str(recvcount))
        direct_mode=Counter(t[1] for t in types.values() if t[0]==0x0306B9F0)
        if direct_mode!=EXPECTED_MEMBER_VE8:
            raise ValueError('MEMBER_VE8_CLASS_MISMATCH:'+str(direct_mode))
    return {
      'schema':'bsc.n1_903.move_member_handoff.v1',
      'exact_binary_sha256':fingerprint,'verification_grade':'PINNED_STATIC_EXE',
      'original_opcode_guards':guards,'direct_e8_edges':edges,'vtable_slots':v,
      'member_vtable_census':{
        'total_types':len(types),'common_receiver_0306b9f0':recvcount[0x0306B9F0],
        'common_receiver_e8_targets':{hex(x):n for x,n in direct_mode.items()},
        'other_receiver_types':{hex(k):n for k,n in recvcount.items() if k!=0x0306B9F0}},
      'critical_decisions':{
        'successor_move_v38':'0x008D3350 returns 1 regardless of member task state',
        'previous_move_v40':'0x03039FB0 checks shared state4, flag24, state+0x158 and group flag',
        'special_native_pop':'0x030445B1 follows transfer call without explicit member task+0x20 or unit+0x240 read in this block',
        'per_unit_finish':'0x030440F8 tests unit-associated auxiliary-task count +0x240',
        'group_packet_flag50':'0x26 (bit0x20 set) from 0x02F5F868',
        'group_packet_all_member_loop':'0x030D5490 enumerates group_member[i] and record[48*i] in a single call without testing each member local task completion',
        'common_member_receiver':'with flag0x20, 0x0306B9F0 skips 0x02F5F7C8 deferred task and uses v+0x100/+0xE8',
        'separate_member_task':'0x02F83B24 has its OWN +0x20 completion flag; this is not the unit MOVE completion',
        'common_member_target':'0x0315EC98 calls 0x03164500 and 0x03164468, clears member +0x20/+0x30 prior to downstream pose processing; cannot label this universal locomotion cancel',
        'all_common_receiver_actor_types':'36/36 common v+0xE8 actor types enter 0x03073224 (28 direct, 3/4/1 via wrappers), then all run tailjmp 0x03056ED4',
        'actor_per_target_cache':'0x03056ED4 always regenerates actor+0x910 (32 bytes); separately may retain, refresh or clear actor+0x930/+0x938 according to its OWN prior cached pointer/context/mode/geometry',
        'actor_private_cache_guard':'0x03056F28 tests each actor+0x930, 0x03056F4A compares context pointer, 0x03056F53 reads actor+0x104, 0x03056F91 geometry screen, 0x03056FB2 recomputes cache via 0x0312D088',
        'actor_target_subtypes':'Some v+0xE8 wrappers additionally rebuild their own local curve via 0x02F43218 (actor+0xB80) or 0x03119E74 (actor+0xB60); not one shared high-level waypoint completion timer',
        'alternate_0x030135e0_policy':'0x030135E0 invokes Mode0 generator, constructs 0x1C-byte record via 0x02E0AFDC and appends it via 0x02DED114; this is a VECTOR APPENDER, not proven direct member task dispatch'},
      'negative_boundaries':[
        'The V3 data did not record whether the conditional 0x03279E40 -> 0x030D5490 edge was taken.',
        'Shared state readiness is not proof that physical actors have arrived.',
        'No proof that individual soldiers independently promote the high-level Shift waypoint.',
        'No proof a single observed member holds its old motor target until task+0x20 becomes 1.',
        'Member target acceptance does not prove physically synchronized steering.',
        'The per-actor +0x930 cache branch is a real source of possible divergence, but actual V3 runtime cache/context values were not sampled.',
        'The parent queue fresh/inherited state has not been proven pointer-identical to the context pointer used at 0x03056F4A.',
        'Original local member cache reuse appears shared by RMB and Shift; no unconditional queue-specific gate found here.',
        'Alternate 0x030135E0 does not bypass the zero-hit member fanout to directly issue model-specific tasks; 0x02DED114 copies 28-byte records into a vector, no actor virtual method within inspected function.',
        'No safe native repair predicate or WH3 efficacy established.'
      ],
      'native_patch_authorized':False,'windows_tested':False,'wh3_tested':False
    }

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--exe',required=True,type=Path)
    a.add_argument('--out',required=True,type=Path)
    args=a.parse_args()
    if args.exe.resolve()==args.out.resolve():a.error('cannot overwrite original EXE')
    try:
        proof=audit(args.exe)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('PINNED_STATIC_PASS',len(proof['original_opcode_guards']),'instruction guards',len(proof['direct_e8_edges']),'E8 edges',len(proof['vtable_slots']),'vtable slots',proof['member_vtable_census']['total_types'],'member classes; NO PATCH')
        return 0
    except (ValueError,OSError,struct.error) as exc:
        print('FAIL_CLOSED',exc,file=sys.stderr)
        return 2
if __name__=='__main__':sys.exit(main())