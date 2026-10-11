"""Pinned original EXE and synthetic control-flow tests, not game-motion proof."""
import importlib.util
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

SRC=Path(__file__).resolve().parents[1]/'src'/'audit_member_handoff.py'
spec=importlib.util.spec_from_file_location('audit_member_handoff', SRC)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
EXE=Path(os.environ.get('WH3_903_EXE','')) if os.environ.get('WH3_903_EXE') else None

class HandoffContracts(unittest.TestCase):
    def test_binary_contract_has_three_distinct_completion_layers(self):
        self.assertEqual(mod.VTABLES['move_complete_v10'][1],0x030440F8)
        self.assertEqual(mod.VTABLES['separate_member_task_tick_v10'][1],0x02F83B24)
        self.assertEqual(mod.VTABLES['move_accept_state_handoff_v38'][1],0x008D3350)

    def test_new_move_accepts_native_handoff_without_member_specific_args(self):
        self.assertEqual(mod.INSTRUCTIONS['next_move_handoff_accepts_unconditionally'][1],'b001c3')
        self.assertNotIn('actor_task_done',mod.local_special_transfer_predicate.__code__.co_varnames)

    def test_unit_handoff_can_pass_while_all_actor_tasks_pending_in_local_model(self):
        # Only the audited NATIVE local predicate; no claim about global engine reachability.
        actor_done=[False]*60
        unit_subtasks=6
        self.assertFalse(all(actor_done))
        self.assertGreater(unit_subtasks,0)
        self.assertTrue(mod.local_special_transfer_predicate(True,True,True))

    def test_special_handoff_not_unconditionally_advance(self):
        for a,b,c in [(False,True,True),(True,False,True),(True,True,False)]:
            self.assertFalse(mod.local_special_transfer_predicate(a,b,c))

    def test_unflagged_member_target_may_construct_deferred_task(self):
        self.assertTrue(mod.deferred_member_task_path(0x06,False))
        self.assertTrue(mod.deferred_member_task_path(0,False))

    def test_group_packet_0x26_skips_individual_wait(self):
        flag=0x26
        self.assertNotEqual(flag & 0x20,0)
        self.assertFalse(mod.deferred_member_task_path(flag,False))
        self.assertFalse(mod.deferred_member_task_path(flag,True))
        self.assertEqual(mod.INSTRUCTIONS['packet_direct_flag_0x26'][1], 'c6435026')

    def test_receiver_mode_gate_for_other_packet(self):
        self.assertFalse(mod.deferred_member_task_path(0,True))

    def test_one_group_generator_loops_through_all_members_in_single_call(self):
        self.assertEqual(mod.INSTRUCTIONS['group_loop_next'][0],0x030D551A)
        self.assertEqual(mod.INSTRUCTIONS['group_record_vector_base'][0],0x030D54E6)
        self.assertEqual(mod.INSTRUCTIONS['group_send_packet_member_v368'][0],0x030D550F)
        self.assertLess(mod.INSTRUCTIONS['group_strategy_target_generator'][0],mod.INSTRUCTIONS['group_load_member_i'][0])

    def test_member_direct_branch_is_distinct_from_task_completion(self):
        self.assertEqual(mod.INSTRUCTIONS['deferred_task_own_done_byte'][0],0x02F83B61)
        self.assertEqual(mod.INSTRUCTIONS['receiver_skips_deferred_on_0x20'][0],0x0306BA33)
        self.assertEqual(mod.INSTRUCTIONS['receiver_deferred_member_task_ctor'][0],0x0306BA5B)

    def test_fresh_move_constructor_distinct_from_shared_rebase(self):
        self.assertEqual(mod.INSTRUCTIONS['new_move_state_null'][0],0x030090E7)
        self.assertEqual(mod.VTABLES['move_receive_shared_state_v48'][1],0x03040864)

    def test_e8_decode_signed_and_reject_bad_opcode(self):
        self.assertEqual(mod.e8_destination(0x1000,b'\xe8\x05\0\0\0'),0x100A)
        self.assertEqual(mod.e8_destination(0x1000,b'\xe8\xfb\xff\xff\xff'),0x1000)
        with self.assertRaisesRegex(ValueError,'NOT_DIRECT_E8'):
            mod.e8_destination(0x1000,b'\xff'*5)

    def test_wrong_exe_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fake.exe';raw=b'MZwrong game';p.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'EXE_SHA256_MISMATCH'):
                mod.audit(p)
            self.assertEqual(p.read_bytes(),raw)

    def test_cli_report_may_not_overwrite_exe(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fake.exe';raw=b'MZwrong game';p.write_bytes(raw)
            r=subprocess.run([sys.executable,str(SRC),'--exe',str(p),'--out',str(p)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertEqual(p.read_bytes(),raw)

    def test_code_path_is_read_only(self):
        source=SRC.read_text(encoding='utf-8')
        self.assertIn("'native_patch_authorized':False",source)
        for forbidden in ['WriteProcessMemory(', 'VirtualProtect(', 'OrderHead=', 'PatchMemory(']:
            self.assertNotIn(forbidden,source)

    def test_common_all_actor_receivers_enter_cache_refresh(self):
        # Frozen +0xe8 wrapper census, and verified tailjmp 0x03073224→0x03056ED4
        self.assertEqual(sum(mod.EXPECTED_MEMBER_VE8.values()),36)
        self.assertEqual(mod.INSTRUCTIONS['common_actor_tail_to_cache_refresh'][1], 'e90f3cfeff')
        self.assertEqual(mod.DIRECT_CALLS['other_actor_calls_common_handler'][1],0x03073224)
        self.assertEqual(mod.DIRECT_CALLS['special_actor_builds_local_curve'][1],0x02F43218)

    def test_per_actor_cache_has_three_distinct_outcomes(self):
        self.assertEqual(mod.local_cache_action(True,True,False,0,True),'clear_cache')
        self.assertEqual(mod.local_cache_action(False,False,False,0,True),'refresh_cache')
        self.assertEqual(mod.local_cache_action(False,True,False,0,True),'retain_old_cache')
        self.assertEqual(mod.local_cache_action(False,True,False,0,False),'refresh_cache')

    def test_same_shared_group_target_may_yield_different_actor_cache(self):
        # Minimal branch witness, not a claim that this exact state occurred in V3.
        member_a=mod.local_cache_action(False,True,False,0,True)
        member_b=mod.local_cache_action(False,True,True,0,True)
        self.assertEqual(member_a,'retain_old_cache')
        self.assertEqual(member_b,'refresh_cache')
        self.assertNotEqual(member_a,member_b)

    def test_all_v3_mode_zero_members_need_context_difference_to_retain(self):
        for mode in [0,3,4,5]:
            self.assertEqual(mod.local_cache_action(False,True,True,mode,True),'refresh_cache')
        for mode in [1,2]:
            self.assertEqual(mod.local_cache_action(False,True,True,mode,True),'retain_old_cache')

    def test_cache_target_part_recomputed_even_when_prior_cache_retained(self):
        self.assertLess(mod.INSTRUCTIONS['actor_cache_copy_first_half'][0],
                        mod.INSTRUCTIONS['actor_cache_previous_path_read'][0])
        self.assertEqual(mod.INSTRUCTIONS['actor_cache_refresh_new_path_write'][0],0x03056FB7)
        self.assertEqual(mod.INSTRUCTIONS['actor_cache_clear_old_path'][0],0x03056FD8)

    def test_type_specific_local_curve_differs_from_member_cache(self):
        self.assertEqual(mod.INSTRUCTIONS['alternate_actor_local_spline_reference'][0],0x0311C960)
        self.assertEqual(mod.INSTRUCTIONS['special_actor_local_cache_reference'][0],0x02F4F950)
        self.assertEqual(mod.DIRECT_CALLS['spline_actor_builds_local_curve'][1],0x03119E74)

    def test_alt_issuer_is_actually_vector_append_not_member_dispatch(self):
        self.assertEqual(mod.DIRECT_CALLS['alternate_unit_producer_append_record_first'][1],0x02DED114)
        self.assertEqual(mod.DIRECT_CALLS['alternate_unit_producer_append_record_second'][1],0x02DED114)
        self.assertEqual(mod.INSTRUCTIONS['alternate_28byte_record_stride_alloc'][1],'486bc81c')
        self.assertEqual(mod.INSTRUCTIONS['alternate_28byte_record_count_inc'][1],'ff4304')

    def test_alt_issuer_28byte_record_copies_position_and_angle(self):
        self.assertEqual(mod.DIRECT_CALLS['alternate_unit_producer_make_record_first'][1],0x02E0AFDC)
        self.assertEqual(mod.INSTRUCTIONS['alternate_record_facing_copy'][1],'66895f0c')
        self.assertEqual(mod.INSTRUCTIONS['alternate_record_coord_copy'][1],'f30f114710')

    def test_pinned_binary_when_available(self):
        if not EXE or not EXE.exists():self.skipTest('original WH3 EXE absent (CI expected)')
        report=mod.audit(EXE)
        self.assertEqual(len(report['original_opcode_guards']),75)
        self.assertEqual(len(report['direct_e8_edges']),31)
        self.assertEqual(len(report['vtable_slots']),7)
        self.assertEqual(report['member_vtable_census']['common_receiver_0306b9f0'],36)
        self.assertFalse(report['native_patch_authorized'])

if __name__=='__main__': unittest.main()