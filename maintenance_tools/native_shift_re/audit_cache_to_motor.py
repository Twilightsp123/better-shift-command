#!/usr/bin/env python3
"""BSC 9.0.3 pinned-original-EXE cache -> native model-motion proof.

Strictly read only. Static branch reachability != proof the V3 battle took it.
Requires audit_903_queued_member_activation.py from the N1 research branch.
"""
from __future__ import annotations
import argparse
import json
import mmap
import struct
import sys
from pathlib import Path

from audit_903_queued_member_activation import (
    PinnedPE, SHA256, IMAGE_BASE, sha, e8_destination,
)

# Machine-code instruction starts and bytes independently decoded from the
# target original WH3 PE64. Freeze evidence; not runtime-discovered offsets.
GUARDS={
    'packet_consumer_old_cache_read': (0x03056F28,'4c8b8b30090000'),
    'packet_consumer_context_check':(0x03056F4A,'4c3b8908010000'),
    'packet_consumer_cache_replace':(0x03056FB7,'48898330090000'),
    'other_action_cache_read':(0x03083AD2,'488b9730090000'),
    'other_action_spatial_compare':(0x03083AFE,'e841e90700'),
    'other_action_test_result':(0x03083B03,'84c0'),
    'other_action_compatible_jump':(0x03083B05,'7553'),
    'other_action_rebuild_motor':(0x03083B53,'e8ace2feff'),
    'other_action_reuse_motor':(0x03083BB9,'e85eb3feff'),
    'group_predicate_cache_read':(0x03052355,'488b9730090000'),
    'group_predicate_spatial_compare':(0x0305237C,'e8c3000b00'),
    'group_motion_state_read':(0x03088639,'418b9110070000'),
    'group_motion_state_is_4':(0x0308865E,'83fa04'),
    'group_motion_self_target':(0x03088667,'4d8d81f8070000'),
    'group_motion_predicate_a':(0x03088671,'e8869cfcff'),
    'group_motion_context_from_action':(0x03088697,'488bb998000000'),
    'group_motion_group_lookup':(0x030886CA,'488bbff8320000'),
    'group_motion_group_reference':(0x030886D1,'4881c7100c0000'),
    'group_motion_predicate_b':(0x030886DB,'e81c9cfcff'),
    'group_motion_test_spatial_status':(0x030886E0,'84c0'),
    'group_motion_skip_if_compatible':(0x030886E2,'7556'),
    'group_motion_install_new_target':(0x0308872E,'e8d196feff'),
    'group_motion_mark_issued':(0x03088733,'c683e800000001'),
    'neighbor_action_calls_group_handler':(0x03088560,'e8b3000000'),
    'neighbor_action_dispatch_call':(0x030827E0,'e8ff580000'),
    'action_fanout_install_from_member':(0x03069924,'e8ab4cfeff'),
    'action_type_a_vtable_address':(0x0304E5E9,'488d0518eca700'),
    'action_type_a_vtable_install':(0x0304E5F0,'488903'),
    'action_type_b_vtable_address':(0x03069B4C,'488d051539a600'),
    'action_type_b_vtable_install':(0x03069B53,'488903'),
    'member_common_action_tick':(0x030822D2,'e875ecffff'),
    'action_tick_virtual_v08':(0x03080F71,'ff5008'),
    'action_tick_virtual_v10':(0x03080F84,'ff5010'),
    'action_type_b_routes_to_v130':(0x0308317A,'ff9030010000'),
    'fresh_target_copy_part_one':(0x03071E35,'0f1183f8070000'),
    'fresh_target_copy_part_two':(0x03071E4A,'0f118318080000'),
    'fresh_target_state_1':(0x03071E7C,'c7831007000001000000'),
    'fresh_target_start_native_progression':(0x03071E86,'e895000000'),
    'progression_read_actor_mode':(0x03071F68,'8b9310070000'),
    'progression_pass_new_target_record':(0x03072001,'4c8d83f8070000'),
    'progression_process_target_state':(0x030720E3,'e864740a00'),
    'progression_forward_to_native':(0x030723D9,'e86e710a00'),
    'progression_uses_new_record':(0x030723E6,'488d8bf8070000'),
    'progression_resolve_goal_position':(0x030723F2,'e8d5ac0a00'),
    'progression_uses_actual_x':(0x030723FB,'f30f108b88000000'),
    'progression_uses_actual_z':(0x03072403,'f30f108390000000'),
    'progression_read_new_target_y':(0x0307240B,'f3440f10831c080000'),
    'progression_delta_x':(0x03072419,'f30f5c08'),
    'progression_distance_sqrt':(0x03072432,'f3440f51c8'),
    'progression_choose_motor':(0x03072492,'e87963feff'),
    'motion_writer_copy_active_target':(0x0311963A,'0f1187e0010000'),
    'motion_writer_flags':(0x0311966A,'44898f88010000'),
    'motion_writer_update':(0x03119687,'e81896feff'),
    'compatibility_old_new_pointer_comparison':(0x03102461,'493bd1'),
    'compatibility_false_exit':(0x0310255A,'32c0'),
    'compatibility_true_exit':(0x0310255E,'b001'),
}

EDGES={
    'old_packet_cache_refresh':(0x03056F01,0x03057D24),
    'actor_cache_to_spatial_compatibility':(0x03083AFE,0x03102444),
    'actor_cache_to_full_member_target':(0x03083B53,0x03071E04),
    'actor_cache_to_existing_member_target':(0x03083BB9,0x0306EF1C),
    'group_predicate_to_compatibility':(0x0305237C,0x03102444),
    'group_motion_to_member_spatial_predicate_a':(0x03088671,0x030522FC),
    'group_motion_to_member_spatial_predicate_b':(0x030886DB,0x030522FC),
    'group_motion_to_full_member_target':(0x0308872E,0x03071E04),
    'group_motion_in_neighbor_update':(0x03088560,0x03088618),
    'neighbor_update_from_action':(0x030827E0,0x030880E4),
    'action_type_a_install_vtable':(0x03069924,0x0304E5D4),
    'member_update_process_action':(0x030822D2,0x03080F4C),
    'fresh_target_to_original_progression':(0x03071E86,0x03071F20),
    'original_progression_to_move_writer_a':(0x030720E3,0x0311954C),
    'original_progression_to_move_writer_b':(0x030723D9,0x0311954C),
    'native_record_transform':(0x030723F2,0x0311D0CC),
    'original_progression_to_motor_solver':(0x03072492,0x03058810),
    'original_move_writer_commits':(0x03119687,0x03102CA4),
}

# Pointer address = initial vtable + documented offset, then expected native RVA.
VFUNC={
    'action_type_a_neighbour_update':(0x03ACD208+0x10,0x0308279C),
    'action_type_b_spatial_target_update':(0x03ACD468+0x130,0x0308393C),
    'action_type_b_update':(0x03ACD468+0x10,0x03083120),
}

def group_movement_target_decision(*, flag_e8:int, group_action_mode:int,
    member_enabled:bool, candidate_available:bool, compatible:bool)->str:
    """Reconstruct only 0x03088618 conditional *second* action branch.

    NOTE: flag_e8!=0 first checks member+0x710==4 and own target; that is
    distinct. Other guards and context construction must also be satisfied.
    """
    if flag_e8!=0:return 'different_prior_target_check'
    if group_action_mode!=1 or not member_enabled or not candidate_available:
        return 'no_target_change'
    return 'retain_existing_target' if compatible else 'install_new_target_and_flag_e8'


def action_movement_target_decision(*, enabled:bool, old_cache_present:bool,
    new_spatial_target_found:bool, compatibility_result:bool)->str:
    """Bounded branch model for 0x0308393C, not full WH3 steering simulation."""
    if not enabled or not new_spatial_target_found:return 'other_action_path'
    if not old_cache_present:return 'fallback_action_path'
    return 'reuse_via_0306ef1c' if compatibility_result else 'full_replace_via_03071e04'


def audit(exe:Path)->dict:
    digest=sha(exe)
    if digest!=SHA256:raise ValueError('EXE_SHA256_MISMATCH:'+digest)
    with exe.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        pe=PinnedPE(mm)
        matched=[]
        for name,(site,hx) in GUARDS.items():
            expected=bytes.fromhex(hx)
            raw=pe.read(site,len(expected),True)
            if raw!=expected:raise ValueError('INSTRUCTION_GUARD_MISMATCH:'+name)
            matched.append({'name':name,'site':hex(site),'bytes':hx})
        checked=[]
        for name,(site,dest) in EDGES.items():
            if e8_destination(site,pe.read(site,5,True))!=dest:
                raise ValueError('E8_CALL_MISMATCH:'+name)
            checked.append({'name':name,'site':hex(site),'target':hex(dest)})
        vt=[]
        for name,(slot,expected) in VFUNC.items():
            got=pe.pointer_rva(slot)
            if got!=expected:raise ValueError('VTABLE_MISMATCH:'+name)
            vt.append({'name':name,'slot':hex(slot),'target':hex(got)})
    return {
      'schema':'bsc.903.cache_to_motor_context.v1',
      'binary_sha256':digest,'image_base':hex(IMAGE_BASE),
      'exact_instruction_guards':matched,
      'verified_direct_calls':checked,'verified_virtual_slots':vt,
      'proven':[
        'member+0x930 is used by original group action to determine whether to replace per-member target via 0x03071E04',
        'original target writer replaces actor+0x7F8/+0x818, sets actor+0x710=1 and immediately calls native 0x03071F20',
        'native 0x03071F20 consumes actor+0x7F8 and actor+0x88/+0x90 and computes target separation with sqrtss, calling movement writer 0x0311954C',
        'native 0x0311954C commits positional goal payload to actor+0x1E0 and calls native 0x03102CA4',
        'separate actor action variant 0x0308393C also tests member+0x930 compatibility and branches to full-target-replace versus existing-context movement handling'
      ],
      'v3_dynamic_evidence': {
        'symptom':'CONFIRMED_BY_PRIOR_V3',
        'branch_taken':'UNKNOWN',
        'why':'recorded V3 member movement samples have no member+0x930 or +0x710 or action vtable/callsite events; 0x03088618 and 0x0308393C were not instrumented',
        'scope':'EXACT_SHA_STATIC_AND_OFFLINE_BRANCH_MODEL_ONLY'
      },
      'native_patch_authorized':False,
      'windows_hook_tested':False,'wh3_gameplay_fix_tested':False,
    }

def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.exe.resolve()==args.out.resolve():parser.error('output cannot overwrite executable')
    try:
        report=audit(args.exe)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    except (OSError,struct.error,ValueError) as e:
        print('N1_EXACT_CACHE_TO_MOTOR_FAILED:',str(e),file=sys.stderr)
        return 2
    print('PASS static:',len(GUARDS),'opcodes;',len(EDGES),'E8 calls;',len(VFUNC),'vtables; NO HOOK')
    return 0

if __name__=='__main__':sys.exit(main())