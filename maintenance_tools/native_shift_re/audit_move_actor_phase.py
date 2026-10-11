#!/usr/bin/env python3
"""WH3 9.0.3 exact-native SHA pinned RMB / queued MOVE / actor-phase static proof.

No game executable is redistributed. Read-only. No V3 branch-execution claim.
RVA values below are ORIGINAL executable RVAs relative to ImageBase 0x140000000.

Use: python audit_move_actor_phase.py --exe WH3.exe --output proof.json
"""
import argparse
import hashlib
import json
import mmap
import struct
import sys
from pathlib import Path

EXPECTED_SHA = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
IMAGE_BASE = 0x140000000

# Machine instruction bytes frozen against the user-supplied original EXE.
# Independent of disassembler output and not self-learned from the candidate EXE.
PIN = {
    'rmb_fresh_move_a0_null': (0x030090E7, '4883a7a000000000'),
    'native_group_queue_dispatch': (0x03043770, 'e8c70b0000'),
    'move_callback_guard_taskkind_4': (0x02F562E3, '83782004'),
    'move_callback_guard_taskready': (0x02F562F2, '40387024'),
    'move_callback_subtask_constructor': (0x02F56358, 'e80bda3000'),
    'move_callback_subtask_alt_constructor': (0x02F56431, 'e846da3000'),
    'move_callback_subtask_params': (0x02F56460, 'e8e7d73000'),
    'move_callback_subtask_one_shot': (0x02F564C4, '4038b3a1000000'),
    'move_callback_subtask_live_ptr': (0x02F564D1, '488b8390000000'),
    'move_callback_subtask_state60': (0x02F564E1, '40387060'),
    'move_callback_subtask_state58': (0x02F564EB, '488b5058'),
    'move_callback_subtask_gate_set': (0x02F564FB, 'c683a100000001'),
    'move_callback_subtask_sync': (0x02F56505, 'e81206feff'),
    'move_callback_finalize': (0x02F565C2, 'e809c9fdff'),
    'move_callback_final_state': (0x02F565C7, '884318'),
    'queued_continuation_refcount': (0x0304459D, 'ff4618498d'),
    'queued_successor_v48': (0x030445AB, 'ff5048'),
    'queued_old_move_pop': (0x030445B1, 'e85ab7f0ff'),
    'native_route_config': (0x03025E91, 'e8e6c9feff'),
    'native_move_task_ctor': (0x030260AF, 'e88066f0ff'),
    'move_callback_to_route_branch': (0x02F56404, 'e8373a3200'),
    'group_mode_classifier': (0x02DC2E04, '8b412883f8'),
    'group_mode_bounded': (0x02DC2E07, '83f805'),
    'group_mode_bitmap': (0x02DC2E0C, 'b929000000'),
    'group_mode_selected': (0x03279E62, 'e89d8fb4ff'),
    'fallback_if_mode_false': (0x03279E69, '744f'),
    'route_group_member_fanout': (0x03279EB3, 'e894b6e5ff'),
    'fallback_ctor_reset': (0x03279EC4, 'e80b02ccff'),
    'fallback_group_action_create': (0x03279ED8, 'e8d39bfeff'),
    'fallback_group_action_vtbl': (0x03263ACF, '488d0552c68700'),
    'fallback_group_aux_vtbl': (0x03263AD9, '488d0598c68700'),
    'fallback_action_type_0a': (0x03263AE4, 'c747480a000000'),
    'fallback_member_classifier_call': (0x03263BFB, 'e83850e0ff'),
    'fallback_member_mask_bit7': (0x03263C00, '80a3100b00007f'),
    'fallback_member_set_bit7': (0x03263C07, 'c0e007'),
    'fallback_member_write_bit7': (0x03263C0A, '0883100b0000'),
    'fallback_classify_member_pose': (0x03068C74, 'f3440f5c8188000000'),
    'fallback_task_check_existing': (0x03281411, '488b4958'),
    'fallback_task_update': (0x03281426, 'e819000000'),
    'fallback_task_embedded_predicate': (0x0328142F, 'e81ce059fe'),
    'fallback_task_mark_completion': (0x03281439, '884320'),
    'fallback_task_with_prior_context': (0x032814FB, 'e8bc05eaff'),
    'fallback_task_without_prior_context': (0x0328150A, 'e8a104eaff'),
    'group_member_packet_fn': (0x030D5490, '48895c2408'),
    'member_packet_emitter_option_one': (0x030D54EB, 'c644242001'),
    'member_packet_ctor': (0x030D54FC, 'e867a3e8ff'),
    'member_packet_dispatch_v368': (0x030D550F, 'ff9068030000'),
    'member_receiver_context_mode': (0x0306BA23, 'e8dc73d5ff'),
    'member_receiver_packet_flag': (0x0306BA2F, 'f6425020'),
    'member_receiver_target_transform_flag': (0x0306BA65, 'f6425102'),
    'member_receiver_target_transform': (0x0306BA75, 'e84e3b0100'),
    'member_mode_field': (0x0306BAD7, '8b8704010000'),
    'member_mode_vE8': (0x0306BB44, '41ff93e8000000'),
    'member_action_old_dispose': (0x0306BBA7, '488d8f28030000'),
    'member_action_install_normal': (0x0306BBD5, 'e832cf1d00'),
    'member_pose_received': (0x0307328B, 'e808ba0e00'),
    'member_mode_sync_received': (0x030732A4, 'e873580000'),
    'member_spatial_cache_tail': (0x030732C0, 'e90f3cfeff'),
    'member_tick_flag_mask': (0x0308227D, 'a804'),
    'member_tick_action_type_16': (0x03082287, '83f810'),
    'member_tick_action_type_4': (0x0308228C, '83f804'),
    'member_tick_embedded_action': (0x030822CB, '488d8f28030000'),
    'member_tick_call_embedded_update': (0x030822D2, 'e875ecffff'),
    'embedded_action_active_byte': (0x03080F52, '80b95401000001'),
    'embedded_action_v8': (0x03080F71, 'ff5008'),
    'embedded_action_v10': (0x03080F84, 'ff5010'),
    'embedded_action_step_counter': (0x03080F87, 'ff4314'),
    'action_tick_mode_query': (0x0325C845, 'ff9060020000'),
    'action_tick_mode0_3a_change': (0x0325C89B, 'e8bcbfe1ff'),
    'action_tick_mode7_change': (0x0325CA15, 'e842bee1ff'),
    'action_tick_mode4_change': (0x0325CA6F, 'e8e8bde1ff'),
    'action_tick_mode0_b_change': (0x0325CD2F, 'e828bbe1ff'),
    'mode_change_delegate_condition': (0x03078882, 'ff9060020000'),
    'mode_change_delegate': (0x030788AD, 'e86a020000'),
    'linked_siblings_check_count': (0x03078C10, '4439bbd40d0000'),
    'linked_siblings_array': (0x03078C19, '488b83d80d0000'),
    'linked_siblings_recursive_mode': (0x03078C5C, 'e8bbfeffff'),
    'mode_current_read': (0x03079021, '8b9718030000'),
    'mode_new_written': (0x0307902F, '89b718030000'),
    'motor_record_separate_writer': (0x03071E04, '48895c2408'),
    'submotor_route_input_copy': (0x030ECB3C, 'e8abfeffff'),
    'submotor_route_build': (0x030ECB98, 'e847160100'),
    'submotor_route_result_store': (0x030ECBA2, '48894370'),
    'submotor_route_normalize': (0x030ECBA9, 'e876ecfeff'),
    'submotor_route_flag': (0x030ECBB1, '66894b58'),
    'submotor_route_link_neighbors': (0x030ECBB8, 'e8b31b0200'),
    'submotor_link_load_next': (0x0310E770, '488b4110'),
    'submotor_link_write_previous': (0x0310E779, '48894818'),
    'submotor_link_load_previous': (0x0310E77D, '488b4118'),
    'submotor_link_write_next': (0x0310E786, '48894810'),
    'submotor_segment_link_insert': (0x030C78EA, 'e845db25fe'),
    'submotor_segment_build': (0x030FE272, 'e8653dfcff'),
    'submotor_segment_append': (0x030FE287, 'e8cc95fcff'),
    'submotor_existing_fields_copy': (0x03121A40, 'e8a7affcff'),
    'submotor_existing_optional_route': (0x03121A99, 'e8febffdff'),
    'fallback_context_submotor_initialization': (0x03121A37, '8903c743040100'),
    'fallback_context_other_submotor': (0x03121B40, 'e8cbaffcff'),
    # In B, an existing route subcontroller may be invalidated as soon as any
    # route-linked object's current resolved reference differs from the
    # single stored route reference. This is NOT a per-soldier finish barrier.
    'fallback_existing_route_read': (0x03281469, '488b4970'),
    'fallback_existing_route_first_gate': (0x03281474, '741d'),
    'fallback_existing_route_discard': (0x03281480, '4883635800'),
    'fallback_existing_route_same': (0x03281493, 'c6436001'),
    'route_reference_eval_non_null': (0x030DEA2A, '4883797800'),
    'route_reference_eval_nodes': (0x030DEA34, '488b7910'),
    'route_reference_eval_node_count': (0x030DEA38, '8b410c'),
    'route_reference_eval_vtbl_slot10': (0x030DEA4E, '4c8b4810'),
    'route_reference_eval_indirect_call': (0x030DEA5C, '41ffd1'),
    'route_reference_eval_against_saved': (0x030DEA5F, '483b4378'),
    'route_reference_eval_first_difference': (0x030DEA63, '7521'),
    'route_reference_eval_all_match_false': (0x030DEA79, '32c0'),
    'route_reference_eval_any_mismatch_true': (0x030DEA86, 'b001'),
    'route_reference_store_from_first_node': (0x030C78D0, '48894378'),
}
# Direct CALL edges verified against original 5-byte E8 instructions.
CALLS = {
    'queue_to_move_handoff': (0x03043770,0x0304433C),
    'move_callback_subtask_create':(0x02F56358,0x03263D68),
    'move_callback_subtask_create_alt':(0x02F56431,0x03263E7C),
    'move_callback_subtask_parameters':(0x02F56460,0x03263C4C),
    'move_callback_subtask_work':(0x02F56505,0x02F36B1C),
    'move_callback_subtask_finalize':(0x02F565C2,0x02F32ED0),
    'queued_old_move_pop':(0x030445B1,0x02F4FD10),
    'route_configure':(0x03025E91,0x0301287C),
    'task_ctor':(0x030260AF,0x02F2C734),
    'task_to_group_branch':(0x02F56404,0x03279E40),
    'group_classifier':(0x03279E62,0x02DC2E04),
    'branch_to_fanout':(0x03279EB3,0x030D554C),
    'branch_to_fallback':(0x03279ED8,0x03263AB0),
    'fallback_setup':(0x03279EC4,0x02F3A0D4),
    'fallback_classify_each_member':(0x03263BFB,0x03068C38),
    'fallback_tick_substate':(0x03281426,0x03281444),
    'fallback_tick_task_completion':(0x0328142F,0x0181F450),
    'fallback_submotor_existing':(0x032814FB,0x03121ABC),
    'fallback_submotor_fresh':(0x0328150A,0x031219B0),
    'native_formation_packet':(0x030D54FC,0x02F5F868),
    'actor_transform':(0x0306BA75,0x0307F5C8),
    'actor_pose':(0x0307328B,0x0315EC98),
    'actor_mode_on_receipt':(0x030732A4,0x03078B1C),
    'actor_install_normal_action':(0x0306BBD5,0x03248B0C),
    'actor_tick_embedded_action':(0x030822D2,0x03080F4C),
    'actor_action_tick_case_1':(0x0325C89B,0x0307885C),
    'actor_action_tick_case_2':(0x0325CA15,0x0307885C),
    'actor_action_tick_case_3':(0x0325CA6F,0x0307885C),
    'actor_action_tick_case_4':(0x0325CD2F,0x0307885C),
    'actor_conditioned_mode_apply':(0x030788AD,0x03078B1C),
    'linked_mode_recursive':(0x03078C5C,0x03078B1C),
    'submotor_copy_descriptor': (0x030ECB3C,0x030EC9EC),
    'submotor_build_route': (0x030ECB98,0x030FE1E4),
    'submotor_compute_route_heading': (0x030ECBA9,0x030DB824),
    'submotor_link_neighbor_nodes': (0x030ECBB8,0x0310E770),
    'submotor_insert_segment_node': (0x030C78EA,0x01325434),
    'submotor_emit_route_segments': (0x030FE272,0x030C1FDC),
    'submotor_merge_route_segments': (0x030FE287,0x030C7858),
    'submotor_existing_context_resync': (0x03121A99,0x030FDA9C),
    'fallback_motor_alloc':(0x03121B40,0x030ECB10),
    'fallback_existing_route_relation_gate':(0x0328146D,0x030DEA20),
}
JUMPS={
    'actor_receipt_tail_cache_refresh':(0x030732C0,0x03056ED4)
}
VTABLES={
    'fallback_move_task_tick':(0x03AE0128+0x10,0x03281408),
    'fallback_move_task_update':(0x03AE0128+0x08,0x03271A48),
    'actor_normal_action_tick':(0x03914618+0x10,0x0325C818),
    'actor_normal_action_setup':(0x03914618+0x08,0x03258B8C),
}

class OriginalPE:
    def __init__(self,path):
        self.path=Path(path)
        with self.path.open('rb') as stream:
            self.sha=hashlib.file_digest(stream,'sha256').hexdigest()
        if self.sha != EXPECTED_SHA: raise ValueError('WRONG_EXE_SHA256 '+self.sha)
        self.fd=self.path.open('rb')
        self.m=mmap.mmap(self.fd.fileno(),0,access=mmap.ACCESS_READ)
        b=self.m
        if b[:2]!=b'MZ': raise ValueError('NOT_A_PE')
        nt=struct.unpack_from('<I',b,0x3c)[0]
        if b[nt:nt+4]!=b'PE\0\0': raise ValueError('BAD_PE')
        machine,n=struct.unpack_from('<HH',b,nt+4)
        if machine!=0x8664:raise ValueError('NOT_X64_PE')
        sz=struct.unpack_from('<H',b,nt+20)[0]
        opt=nt+24
        self.image=struct.unpack_from('<Q',b,opt+24)[0]
        if self.image!=IMAGE_BASE: raise ValueError('IMAGE_BASE_CHANGED')
        self.sections=[]
        for i in range(n):
            o=opt+sz+i*40
            name=b[o:o+8].split(b'\0')[0].decode('ascii')
            vs,rva,rawsize,raw=struct.unpack_from('<IIII',b,o+8)
            flags=struct.unpack_from('<I',b,o+36)[0]
            self.sections.append((name,rva,rawsize,raw,vs,flags))
    def close(self):
        self.m.close();self.fd.close()
    def read(self,rva,size,code=False):
        for name,s,n,offset,vs,flags in self.sections:
            if s<=rva and rva+size<=s+n:
                if code and not (flags & 0x20000000):raise ValueError(f'NOT_CODE {rva:x} {name}')
                return bytes(self.m[offset+rva-s:offset+rva-s+size])
        raise ValueError(f'UNMAPPED_RVA {rva:x}+{size:x}')


def branch_dest(pe,site,opcode=0xe8):
    data=pe.read(site,5,True)
    if data[0]!=opcode:raise ValueError(f'CALL_OR_JMP_OPCODE_MISMATCH {site:#x} {data.hex()}')
    return (site+5+struct.unpack_from('<i',data,1)[0]) & 0xffffffff


def verify(pe):
    for name,(rva,hx) in PIN.items():
        actual=pe.read(rva,len(hx)//2,True).hex()
        if actual != hx: raise ValueError(f'OPCODE_MISMATCH {name} {rva:#x}: {actual} != {hx}')
    for name,(site,dest) in CALLS.items():
        actual=branch_dest(pe,site)
        if actual!=dest:raise ValueError(f'CALL_MISMATCH {name} {actual:#x} != {dest:#x}')
    for name,(site,dest) in JUMPS.items():
        actual=branch_dest(pe,site,0xe9)
        if actual!=dest:raise ValueError(f'JUMP_MISMATCH {name} {actual:#x} != {dest:#x}')
    for name,(rva,expected) in VTABLES.items():
        observed=struct.unpack('<Q',pe.read(rva,8))[0]
        if observed != IMAGE_BASE+expected:raise ValueError(f'VTABLE_MISMATCH {name} {observed:#x}')
    return dict(
      schema='bsc.903.rmb_queued_original_move_actor_state_machine.v1',
      original_exe_sha256=pe.sha,
      exact_opcode_guards=len(PIN),verified_calls=len(CALLS),verified_tail_jumps=len(JUMPS),
      verified_vtable_entries=len(VTABLES),
      evidence={
        'high_level_callback_wait':'0x02F561E8 checks task kind/status and can retain a live subordinate at MOVE-task+0x90; later gates on subtask+0x60 and subtask+0x58, sets task+0xA1, updates 0x02F36B1C and derives task+0x18 final state; this task is distinct from the alternate group-task object 0x03AE0128',
        'group_mode_0_3_5':'0x02DC2E04 tests owner mode +0x28 against bitmask 0x29',
        'group_branch_A':'0x03279E40 only enters 0x030D5490 when group mode classifier is true',
        'group_branch_B':'0x03279E40 else creates 0x03AE0128 group task and sets per actor +0xB10 bit7 from spatial predicate',
        'fallback_submotor_geometry':'0x03281444 may call 0x03121ABC, which calls 0x030ECB10; the latter copies a route descriptor via 0x030EC9EC, builds route segments via 0x030FE1E4->0x030C1FDC/0x030C7858, stores the resulting route pointer at submotor+0x70, calls 0x030DB824 to read orientation and 0x0310E770 to connect doubly-linked-list neighbors; this is NOT proof the actor motor has consumed the route; alternative 0x031219B0 has separate inherited-context path',
        'fallback_progress':'0x03281408 advances / installs sub-controller through 0x03281444 and task +0x20 depends on embedded-list predicate',
        'fallback_prior_route_relation_gate':'0x03281444 invokes 0x030DEA20 on existing subcontroller+0x70, which holds the route descriptor. 0x030DEA20 iterates route+0x10 / route+0x0C entries and calls per-entry vtable+0x10 against route+0x78 saved relation. It returns TRUE on FIRST mismatch and FALSE if empty/all match. In 0x03281444 TRUE disposes existing subcontroller and allows reconstruction; FALSE sets task+0x60. This is a relation consistency test, not proof of per-soldier waypoint completion. 0x030C7858 can populate route+0x78 from a selected candidate +0x40.',
        'group_branch_A_packet':'0x030D5490 builds transformed 0x26 target packets and invokes each actor vfunc+0x368 within one loop',
        'actor_receipt':'0x03073224 invokes 0x0315EC98 pose then 0x03078B1C mode then 0x03056ED4 spatial cache',
        'actor_subaction':'0x0306B9F0 conditionally replaces actor+0x328 action with vtable 0x03914618 (packet+0x34=0)',
        'actor_deferred':'0x03081EB4 when tick flag and actor+0x324=4/16 calls 0x03080F4C on actor+0x328',
        'actor_mode_update':'0x0325C818 may call 0x0307885C and then 0x03078B1C which conditionally writes actor+0x318',
        'related_group_mode_propagation':'0x03078B1C may recurse over related actor list +0xDD4/+0xDD8; no unconditional whole unit barrier',
      },
      strict_negative_findings=[
        'V3 did not record positive call at 0x030D5490, so its activation in V3 is not confirmed',
        'No instruction-only proof that actor+0x318 is a Shift user-waypoint index',
        'No verified direct chain from this packet to persistent primary actor+0x7F8/+0x818 locomotion targets',
        '0x0310E770 is only previous/next pointer relinking; no proven producer-to-consumer edge from fallback submotor+0x70 to main soldier velocity',
        '0x030DEA20 checks route-linked object reference consistency, not verified member completion; its first-mismatch return cannot alone prove 60 actors changed frames',
        'Per-actor conditional update DOES NOT prove different rendered frames absent tick trace',
        'Original B-group member+0xB10 bit7 is not proven to control Shift waypoint progression',
        'No evidence for safely replacing group branch condition, the actor mode or the queue with a global hook',
      ],
      v3_real_runtime_branch='unknown',
      actual_fix='not_yet_proven',patch_authorized=False,
    )


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',required=True,type=Path)
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    if args.output and args.exe.resolve()==args.output.resolve():p.error('No output may overwrite the original EXE')
    try:
        exe=OriginalPE(args.exe)
        try:result=verify(exe)
        finally:exe.close()
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        print('PASS',result['exact_opcode_guards'],'instructions',result['verified_calls'],'calls',result['verified_vtable_entries'],'vtables; STATIC, no patch')
        return 0
    except (ValueError,OSError,struct.error) as e:
        print('FAILED_CLOSED:',e,file=sys.stderr)
        return 2
if __name__=='__main__':raise SystemExit(main())