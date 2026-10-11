#!/usr/bin/env python3
"""BSC exact WH3-9.0.3 RMB/Shift member phase-divergence decision audit.

Only native call/byte/dataflow facts; does not claim actual V3 action subtype.
No memory/EXE modifications, no Hook, no patch authorization.
"""
from __future__ import annotations
import argparse
import json
import mmap
import struct
import sys
from pathlib import Path
from audit_903_queued_member_activation import PinnedPE, SHA256, sha, e8_destination

# All sites are instruction boundaries on original user 9.0.3-labelled PE.
GUARDS = {
    'ordinary_move_initializes_null_state':(0x030090E7,'4883a7a000000000'),
    'queued_move_state_handoff':(0x030445AB,'ff5048'),
    'queued_handoff_state1':(0x030408CF,'c7422001000000'),
    'old_spatial_ref_from_member':(0x03052355,'488b9730090000'),
    'same_spatial_ref_fast_compare':(0x03102461,'493bd1'),
    'same_ref_jump_to_compatible':(0x03102464,'0f84f4000000'),
    'compatible_result':(0x0310255E,'b001'),
    'failed_compat_result':(0x0310255A,'32c0'),
    'group_checks_local_motor_state':(0x03088639,'418b9110070000'),
    'group_action_requires_first_phase':(0x0308868A,'83b99000000001'),
    'group_compatibility_test':(0x030886E0,'84c0'),
    'group_if_compatible_keeps_goal':(0x030886E2,'7556'),
    'group_if_incompatible_installs_new_goal':(0x0308872E,'e8d196feff'),
    'group_marks_goal_issued':(0x03088733,'c683e800000001'),
    'individual_reads_old_ref':(0x03083AD2,'488b9730090000'),
    'individual_compares_spatial_refs':(0x03083AFE,'e841e90700'),
    'individual_if_compatible_uses_incremental_path':(0x03083B05,'7553'),
    'individual_if_incompatible_rebuilds':(0x03083B53,'e8ace2feff'),
    'individual_compatible_incremental_goal_update':(0x03083BB9,'e85eb3feff'),
    'incremental_cleanup_old_aux_goal':(0x03071EC5,'e8eaf10a00'),
    'incremental_clear_goal_resource_pointer':(0x03071ECA,'4883a32808000000'),
    'incremental_clear_local_motor_state':(0x03071ED2,'83a31007000000'),
    'incremental_entry_calls_cleanup':(0x0306EF71,'e82e2f0000'),
    'incremental_tail_calls_common_writer':(0x0306EF96,'e9b1a50a00'),
    'full_rebuild_goal_7f8':(0x03071E35,'0f1183f8070000'),
    'full_rebuild_goal_818':(0x03071E4A,'0f118318080000'),
    'full_rebuild_sets_motor_state_one':(0x03071E7C,'c7831007000001000000'),
    'full_rebuild_starts_original_progress':(0x03071E86,'e895000000'),
    'original_progress_consumes_new_goal':(0x030723E6,'488d8bf8070000'),
    'common_writer_can_exit_early':(0x03119556,'80b92802000001'),
    'common_writer_commits_xyz_goal':(0x0311963A,'0f1187e0010000'),
    'common_writer_notifies_native':(0x03119687,'e81896feff'),
    'native_update_uses_own_mode_flags':(0x03102CAB,'f6c204'),
    'contact_pair_same_owner_first':(0x03084996,'488b8780000000'),
    'contact_pair_same_owner_cmp':(0x0308499D,'48398380000000'),
    'contact_pair_same_owner_skip':(0x030849A4,'0f84b3010000'),
    'contact_dispatch_member_virtual_4b0_a':(0x03084AED,'ff90b0040000'),
    'contact_dispatch_member_virtual_4b0_b':(0x03084D3E,'ff90b0040000'),
    'member_packet_direct_branch':(0x0306BA2F,'f6425020'),
    'member_packet_direct_e8_method':(0x0306BB44,'41ff93e8000000'),
}
DIRECT_EDGES = {
    'candidate_lookup_for_old_comparison':(0x03052350,0x0312D088),
    'group_spatial_compatibility':(0x0305237C,0x03102444),
    'group_compatibility_request_a':(0x03088671,0x030522FC),
    'group_compatibility_request_b':(0x030886DB,0x030522FC),
    'group_full_rebuild':(0x0308872E,0x03071E04),
    'individual_compatibility':(0x03083AFE,0x03102444),
    'individual_full_rebuild':(0x03083B53,0x03071E04),
    'individual_incremental_update':(0x03083BB9,0x0306EF1C),
    'incremental_calls_cleanup':(0x0306EF71,0x03071EA4),
    'incremental_tail_calls_common_writer':(0x0306EF96,0x0311954C),
    'full_rebuild_enters_progression':(0x03071E86,0x03071F20),
    'progression_to_common_writer_a':(0x030720E3,0x0311954C),
    'progression_to_common_writer_b':(0x030723D9,0x0311954C),
    'common_writer_native_notify':(0x03119687,0x03102CA4),
    'common_member_update_to_contact_filter':(0x030824A6,0x0308489C),
    'special_member_virtual_4b0_uses_3069844':(0x03116D70,0x03069844),
}
# Verify machine-code true-branch destination, independent of expected bytes.
BRANCHES = {
    'identical_ref_shortcut':(0x03102464,0x0310255E),
    'group_compatible_skips_rebuild':(0x030886E2,0x0308873A),
    'individual_compatible_skips_full_rebuild':(0x03083B05,0x03083B5A),
}
# Do not turn into claims of true per-member route-phase flags.

def branch_dest(site: int, insn: bytes) -> int:
    if len(insn)==2 and insn[0] in (0x74,0x75):
        return site+2+struct.unpack_from('<b',insn,1)[0]
    if len(insn)==6 and insn[:2] in (b'\x0f\x84',b'\x0f\x85'):
        return site+6+struct.unpack_from('<i',insn,2)[0]
    raise ValueError('NOT_SUPPORTED_CONDITIONAL_BRANCH:'+hex(site))


def model_group_action(*,action_phase:int,actor_enabled:bool,has_reference:bool,
                       spatial_compatible:bool,action_e8:int=0)->str:
    """Reduced conditional native 0x03088618 branch (not full engine)."""
    if action_e8:
        return 'separate_e8_state_path'
    if action_phase!=1 or not actor_enabled or not has_reference:
        return 'no_change_other_guards'
    return 'keep_existing_motor_goal' if spatial_compatible else 'full_target_reinitialization'


def model_individual_action(*,action_active:bool,found_candidate:bool,
                            spatial_compatible:bool)->str:
    """Reduced native 0x0308393C branch, both outcomes feed goal machinery."""
    if not action_active or not found_candidate:
        return 'other_action_path'
    return ('incremental_cleanup_and_common_goal_writer' if spatial_compatible
            else 'full_rebuild_and_original_progression')


def inspect(exe: Path) -> dict:
    digest=sha(exe)
    if digest!=SHA256:raise ValueError('WRONG_EXE_SHA256:'+digest)
    guards=[]; calls=[]; branches=[]; interaction_vtables={}
    with exe.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        pe=PinnedPE(mm)
        for name,(site,bytes_hex) in GUARDS.items():
            expected=bytes.fromhex(bytes_hex)
            if pe.read(site,len(expected),True)!=expected:
                raise ValueError('MACHINE_BYTE_MISMATCH:'+name)
            guards.append({'site':hex(site),'name':name,'bytes':bytes_hex})
        for name,(site,dest) in DIRECT_EDGES.items():
            raw=pe.read(site,5,True)
            if raw[0]==0xE8:
                actual=e8_destination(site,raw)
            elif raw[0]==0xE9:
                actual=site+5+struct.unpack_from('<i',raw,1)[0]
            else:raise ValueError('NOT_E8_OR_E9:'+name)
            if actual!=dest:raise ValueError('DIRECT_EDGE_MISMATCH:'+name)
            calls.append({'name':name,'call_site':hex(site),'destination':hex(dest)})
        for name,(site,dest) in BRANCHES.items():
            n=6 if site==0x03102464 else 2
            got=branch_dest(site,pe.read(site,n,True))
            if got!=dest:raise ValueError('CONDITIONAL_BRANCH_MISMATCH:'+name)
            branches.append({'name':name,'from':hex(site),'to':hex(got)})
        # Member+0x4B0 is also reached from contact/interaction callsites,
        # including one that skips actors sharing the same +0x80 owner pointer.
        # This is NOT evidence that action 0x03088618 runs under normal MOVE.
        for vt,(receiver,_ve8) in pe.member_vtable_census().items():
            if receiver!=0x0306B9F0:continue
            fn=pe.pointer_rva(vt+0x4B0)
            fn2=pe.pointer_rva(vt+0x4D0)
            interaction_vtables[vt]=(fn,fn2)
        from collections import Counter
        count_4b0=Counter(t[0] for t in interaction_vtables.values())
        count_4d0=Counter(t[1] for t in interaction_vtables.values())
        if len(interaction_vtables)!=36 or count_4b0!={0x03069844:32,0x008D3280:4} or count_4d0!={0x03069B10:36}:
            raise ValueError('INTERACTION_ACTOR_VTABLE_CENSUS_CHANGED')
    return {
      'schema':'bsc.903.rmb_shift_member_phase_decision.v1',
      'grade':'PINNED_EXE_STATIC_ONLY',
      'sha256':digest,
      'guards':guards,'direct_edges':calls,'checked_branches':branches,
      'member_interaction_vtables':{
          'common_member_classes':len(interaction_vtables),
          'virtual_4b0':{hex(k):v for k,v in sorted(count_4b0.items())},
          'virtual_4d0':{hex(k):v for k,v in sorted(count_4d0.items())},
      },
      'interpretation':[
        'Fresh RMB and eligible queued continuation carry different higher-level route-state lifetimes.',
        'Same spatial association identity short-circuits the original compatibility helper to TRUE.',
        'One actor action can retain existing motor goal on group-compatibility TRUE, while another action on TRUE calls an incremental path that still reaches the goal writer.',
        'Incompatibility can issue a full per-member target reset and progress through the original motor writer.',
        'Native goal writer can return early for original actor flags, so call-to-writer is not proof every invocation writes a goal.',
        'A group-action creation route is reachable via virtual+0x4B0 in a member-interaction screen; the screen skips same-owner (+0x80) candidate pairs in the examined branch. This does NOT prove the group action occurs in native RMB/Shift move handling.',
      ],
      'not_proven':[
        'Which actor action types were active in real V3 35-43s compressed turn.',
        'How often identity-equal cache and divergent action outcomes happened in the real battle.',
        'One specific branch as a proven cause of the observed model crowding.',
        'A native MOVE task calling group-action A 0x03088618 rather than a contact/event path.',
      ],
      'runtime_patch_authorized':False,
      'windows_build_tested':False,
      'wh3_fix_tested':False,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.exe.resolve()==args.out.resolve():parser.error('refusing to overwrite original EXE')
    try:
        result=inspect(args.exe)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    except (ValueError,struct.error,OSError) as exc:
        print('BSC_MEMBER_PHASE_AUDIT_BLOCKED:',exc,file=sys.stderr)
        return 2
    print('STATIC PASS:',len(GUARDS),'guards,',len(DIRECT_EDGES),'edges,',len(BRANCHES),'branches. NO PATCH')
    return 0
if __name__=='__main__':sys.exit(main())