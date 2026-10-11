"""Static original-x64 predicates and negative-controls, not gameplay tests."""
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE=pathlib.Path(__file__).resolve()
CANDIDATES=[
  HERE.parents[1]/'src'/'audit_move_actor_phase.py',
  HERE.parents[1]/'maintenance_tools'/'native_shift_re'/'audit_move_actor_phase.py',
]
SOURCE=next((s for s in CANDIDATES if s.is_file()),None)
if SOURCE is None: raise FileNotFoundError(f'missing exact static RE verifier: {CANDIDATES}')
spec=importlib.util.spec_from_file_location('native_move_actor_phase',SOURCE)
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

class FakePE:
    def __init__(self, source): self.content=source
    def read(self, rva, size, code=False): return self.content[:size]


def deferred_actor_tick_permitted(tick_mask, actor_action_type, action_active,
                                  existing_started=False, action_finished=False):
    """Necessary checks from 0x0308227D and 0x03080F52-0x03080F87.

    A structural model ONLY: further native predicates and other actor tick
    implementations are not represented. True is not a guarantee of motion.
    """
    if not (tick_mask & 0x04):return False
    if actor_action_type not in (4,16):return False
    if not action_active or action_finished:return False
    return True


class NativeOriginalMoveActorPhase(unittest.TestCase):
    def test_machine_guard_coverage(self):
        self.assertEqual(len(a.PIN),97)
        self.assertIn('fallback_member_set_bit7',a.PIN)
        self.assertIn('mode_new_written',a.PIN)
        self.assertIn('move_callback_subtask_state58',a.PIN)
    def test_original_direct_edges(self):
        self.assertEqual(len(a.CALLS),40)
        self.assertEqual(len(a.JUMPS),1)
        self.assertEqual(a.CALLS['task_to_group_branch'],(0x02F56404,0x03279E40))
        self.assertEqual(a.CALLS['branch_to_fallback'],(0x03279ED8,0x03263AB0))
    def test_two_independent_native_task_types_not_confused(self):
        self.assertEqual(a.VTABLES['fallback_move_task_tick'],(0x03AE0138,0x03281408))
        self.assertEqual(a.VTABLES['actor_normal_action_tick'],(0x03914628,0x0325C818))
        self.assertNotEqual(a.VTABLES['fallback_move_task_tick'][0],a.VTABLES['actor_normal_action_tick'][0])
    def test_reusable_actor_action_tick_four_caller_sites(self):
        destinations=[target for name,(_,target) in a.CALLS.items() if name.startswith('actor_action_tick_case_')]
        self.assertEqual(len(destinations),4)
        self.assertTrue(all(x==0x0307885C for x in destinations))
    def test_group_eligibility_is_not_60_actor_completion(self):
        self.assertEqual(a.PIN['group_mode_bitmap'][1],'b929000000')
        self.assertEqual([x for x in range(6) if (0x29>>x)&1],[0,3,5])
    def test_actor_telemetry_field_is_mode_not_waypoint(self):
        self.assertEqual(a.PIN['mode_new_written'][1],'89b718030000')
        self.assertEqual(a.PIN['linked_siblings_check_count'][0],0x03078C10)
        self.assertEqual(a.PIN['linked_siblings_array'][0],0x03078C19)
    def test_second_branch_has_per_actor_spatial_predicate(self):
        self.assertEqual(a.CALLS['fallback_classify_each_member'][1],0x03068C38)
        self.assertEqual(a.PIN['fallback_member_mask_bit7'][1],'80a3100b00007f')
        self.assertEqual(a.PIN['fallback_member_write_bit7'][1],'0883100b0000')
    def test_group_callback_persists_subtask_lifecycle(self):
        self.assertIn('move_callback_subtask_one_shot',a.PIN)
        self.assertEqual(a.PIN['move_callback_subtask_live_ptr'][0],0x02F564D1)
        self.assertEqual(a.CALLS['move_callback_subtask_work'][1],0x02F36B1C)
        self.assertEqual(a.CALLS['move_callback_subtask_finalize'][1],0x02F32ED0)
    def test_packet_receipt_writes_pose_and_mode_before_spatial_cache(self):
        self.assertLess(a.CALLS['actor_pose'][0],a.CALLS['actor_mode_on_receipt'][0])
        self.assertLess(a.CALLS['actor_mode_on_receipt'][0],a.JUMPS['actor_receipt_tail_cache_refresh'][0])
    def test_fallback_subcontroller_is_distinct_from_packet_path(self):
        self.assertEqual(a.CALLS['fallback_submotor_existing'][1],0x03121ABC)
        self.assertEqual(a.CALLS['fallback_submotor_fresh'][1],0x031219B0)
        self.assertNotEqual(a.CALLS['fallback_submotor_fresh'][1],a.CALLS['actor_pose'][1])
    def test_fallback_creates_real_route_geometry_not_just_bitsets(self):
        self.assertEqual(a.CALLS['submotor_build_route'][1],0x030FE1E4)
        self.assertEqual(a.CALLS['submotor_emit_route_segments'][1],0x030C1FDC)
        self.assertEqual(a.CALLS['submotor_merge_route_segments'][1],0x030C7858)
        self.assertEqual(a.PIN['submotor_route_result_store'][1],'48894370')
    def test_group_submotor_is_linked_list_not_a_direct_motor_tick(self):
        self.assertEqual(a.PIN['submotor_link_write_previous'][1],'48894818')
        self.assertEqual(a.PIN['submotor_link_write_next'][1],'48894810')
        self.assertEqual(a.CALLS['submotor_link_neighbor_nodes'][1],0x0310E770)
        self.assertEqual(a.CALLS['submotor_insert_segment_node'][1],0x01325434)
    def test_fallback_existing_submotor_route_still_conditional(self):
        self.assertEqual(a.CALLS['submotor_existing_context_resync'][1],0x030FDA9C)
        self.assertEqual(a.CALLS['fallback_submotor_fresh'][1],0x031219B0)
    def test_structural_counterexample_same_packet_different_eligible_actor_ticks(self):
        # Same packet could have been received, yet action tick paths differ.
        # The two actors' distinct local tick flags / action types suffice.
        self.assertTrue(deferred_actor_tick_permitted(0x04,4,True))
        self.assertFalse(deferred_actor_tick_permitted(0x00,4,True))
        self.assertFalse(deferred_actor_tick_permitted(0x04,3,True))
        self.assertFalse(deferred_actor_tick_permitted(0x04,4,False))
        self.assertFalse(deferred_actor_tick_permitted(0x04,16,True,action_finished=True))
    def test_indirect_vtable_target_not_inferred_from_direct_e8(self):
        self.assertEqual(len(a.VTABLES),4)
        self.assertNotIn('member_packet_dispatch_v368',a.CALLS)
    def test_branch_decode_forward_backward_and_reject_non_branch(self):
        self.assertEqual(a.branch_dest(FakePE(bytes.fromhex('e805000000')),0x1000),0x100a)
        self.assertEqual(a.branch_dest(FakePE(bytes.fromhex('e8fbffffff')),0x1000),0x1000)
        self.assertEqual(a.branch_dest(FakePE(bytes.fromhex('e905000000')),0x1000,0xe9),0x100a)
        with self.assertRaises(ValueError):a.branch_dest(FakePE(b'\x90'*5),0x1000)
    def test_wrong_sha_rejected_before_pe_decode(self):
        with tempfile.TemporaryDirectory() as folder:
            candidate=pathlib.Path(folder)/'wrong.exe'
            original=b'MZthis is an invalid replacement'
            candidate.write_bytes(original)
            with self.assertRaisesRegex(ValueError,'WRONG_EXE_SHA256'):a.OriginalPE(candidate)
            self.assertEqual(candidate.read_bytes(),original)
    def test_cli_wrong_exe_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            candidate=pathlib.Path(folder)/'wrong.exe'
            output=pathlib.Path(folder)/'evidence.json'
            candidate.write_bytes(b'bad')
            run=subprocess.run([sys.executable,str(SOURCE),'--exe',str(candidate),'--output',str(output)],capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertFalse(output.exists())
            self.assertEqual(candidate.read_bytes(),b'bad')
    def test_cli_same_exe_output_path_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            candidate=pathlib.Path(folder)/'wrong.exe'
            original=b'MZ-do-not-overwrite'; candidate.write_bytes(original)
            run=subprocess.run([sys.executable,str(SOURCE),'--exe',str(candidate),'--output',str(candidate)],capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(candidate.read_bytes(),original)
    def test_original_exe_optional_in_repo_ci(self):
        # Local original always used here. Public Github CI cannot ship the EXE.
        exe=os.environ.get('WH3_903_EXE')
        if not exe:
            default=pathlib.Path('/mnt/data/Warhammer3.exe')
            if default.is_file():exe=str(default)
        if not exe:self.skipTest('Original game EXE deliberately not distributed in public repo CI')
        pe=a.OriginalPE(exe)
        try:
            proof=a.verify(pe)
            self.assertEqual(proof['exact_opcode_guards'],97)
            self.assertEqual(proof['verified_calls'],40)
            self.assertEqual(proof['verified_tail_jumps'],1)
            self.assertFalse(proof['patch_authorized'])
            self.assertEqual(proof['v3_real_runtime_branch'],'unknown')
        finally:pe.close()
    def test_verifier_does_not_patch_original_code(self):
        src=SOURCE.read_text(encoding='utf8')
        for forbidden in ('VirtualProtect(', 'WriteProcessMemory(', 'FlushInstructionCache(', 'ptrace(', 'task_for_pid(', 'ctypes.windll'):
            self.assertNotIn(forbidden,src)
    def test_binary_contains_all_pin_sites_in_executable_sections_if_present(self):
        exe=os.environ.get('WH3_903_EXE','/mnt/data/Warhammer3.exe')
        if not pathlib.Path(exe).exists():self.skipTest('Original EXE absent')
        p=a.OriginalPE(exe)
        try:
            self.assertTrue(all(p.read(rva,len(hx)//2,True).hex()==hx for rva,hx in a.PIN.values()))
        finally:p.close()

if __name__=='__main__':unittest.main()