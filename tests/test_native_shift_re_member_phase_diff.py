"""Machine-byte, branch-target, member-type and counterexample tests.

Expected from original EXE: STATIC; excludes V3 runtime claims and gameplay fixes.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

SRC=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(SRC))
import audit_member_phase_diff as m

class PinnedNativeMemberPhaseTests(unittest.TestCase):
    def test_exact_sha_configured(self):
        self.assertEqual(len(m.SHA256),64)
        self.assertTrue(m.SHA256.startswith('518c4f'))

    def test_guarded_anchors(self):
        self.assertEqual(len(m.GUARDS),40)
        self.assertEqual(len(m.DIRECT_EDGES),16)
        self.assertEqual(len(m.BRANCHES),3)

    def test_rmb_versus_queued_order_state_not_actor_state(self):
        self.assertIn('ordinary_move_initializes_null_state',m.GUARDS)
        self.assertIn('queued_handoff_state1',m.GUARDS)
        self.assertNotIn('member+0x104',m.BRANCHES)

    def test_early_same_pointer_shortcut(self):
        src,tgt=m.BRANCHES['identical_ref_shortcut']
        self.assertEqual(m.branch_dest(src,bytes.fromhex(m.GUARDS['same_ref_jump_to_compatible'][1])),tgt)
        self.assertEqual(tgt,0x0310255E)

    def test_group_skip_full_rebuild_on_compatible(self):
        src,tgt=m.BRANCHES['group_compatible_skips_rebuild']
        self.assertEqual(m.branch_dest(src,bytes.fromhex(m.GUARDS['group_if_compatible_keeps_goal'][1])),tgt)
        self.assertLess(m.GUARDS['group_if_incompatible_installs_new_goal'][0],tgt)

    def test_individual_compatible_skips_full_rebuild(self):
        src,tgt=m.BRANCHES['individual_compatible_skips_full_rebuild']
        self.assertEqual(m.branch_dest(src,bytes.fromhex(m.GUARDS['individual_if_compatible_uses_incremental_path'][1])),tgt)
        self.assertEqual(tgt,0x03083B5A)

    def test_two_compatible_subtypes_do_not_have_same_effect(self):
        self.assertEqual(m.model_group_action(action_phase=1,actor_enabled=True,has_reference=True,
                            spatial_compatible=True),'keep_existing_motor_goal')
        self.assertEqual(m.model_individual_action(action_active=True,found_candidate=True,
                            spatial_compatible=True),'incremental_cleanup_and_common_goal_writer')

    def test_divergent_group_members_can_respond_differently(self):
        a=m.model_group_action(action_phase=1,actor_enabled=True,has_reference=True,
                               spatial_compatible=True)
        b=m.model_group_action(action_phase=1,actor_enabled=True,has_reference=True,
                               spatial_compatible=False)
        self.assertEqual(a,'keep_existing_motor_goal')
        self.assertEqual(b,'full_target_reinitialization')
        # This is a native-control-flow counterexample, NOT observed V3 data.

    def test_invalid_or_other_action_state_is_not_assumed_affected(self):
        for phase in [0,2,3,4]:
            self.assertEqual(m.model_group_action(action_phase=phase,actor_enabled=True,
                             has_reference=True,spatial_compatible=False),'no_change_other_guards')
        self.assertEqual(m.model_group_action(action_phase=1,actor_enabled=True,
                         has_reference=True,spatial_compatible=False,action_e8=1),
                         'separate_e8_state_path')

    def test_full_and_incremental_both_can_reach_writer(self):
        self.assertEqual(m.DIRECT_EDGES['incremental_tail_calls_common_writer'][1],0x0311954C)
        self.assertEqual(m.DIRECT_EDGES['progression_to_common_writer_a'][1],0x0311954C)
        self.assertEqual(m.DIRECT_EDGES['progression_to_common_writer_b'][1],0x0311954C)
        self.assertIn('common_writer_can_exit_early',m.GUARDS)

    def test_bad_branch_opcode_fails(self):
        with self.assertRaisesRegex(ValueError,'NOT_SUPPORTED_CONDITIONAL_BRANCH'):
            m.branch_dest(0x5000,b'\x90\x90')

    def test_wrong_exe_never_accepted_or_modified(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'fake.exe';raw=b'MZ'+b'\x00'*70;path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'WRONG_EXE_SHA256'):
                m.inspect(path)
            self.assertEqual(path.read_bytes(),raw)

    def test_exe_cannot_be_output(self):
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'game.exe';raw=b'MZfake';path.write_bytes(raw)
            process=subprocess.run([sys.executable,str(SRC/'audit_member_phase_diff.py'),
                                    '--exe',str(path),'--out',str(path)],capture_output=True,text=True)
            self.assertNotEqual(process.returncode,0)
            self.assertEqual(path.read_bytes(),raw)

    def test_no_native_mutation_code(self):
        src=(SRC/'audit_member_phase_diff.py').read_text(encoding='utf8')
        for forbidden in ['WriteProcessMemory(', 'VirtualProtect(', 'OrderHead=', 'runtime_patch_authorized\':True']:
            self.assertNotIn(forbidden,src)

    def test_member_contact_path_not_automatically_move_activation(self):
        self.assertEqual(m.GUARDS['contact_pair_same_owner_skip'][0],0x030849A4)
        self.assertEqual(m.GUARDS['contact_dispatch_member_virtual_4b0_a'][0],0x03084AED)
        self.assertEqual(m.DIRECT_EDGES['common_member_update_to_contact_filter'][1],0x0308489C)
        self.assertEqual(m.DIRECT_EDGES['special_member_virtual_4b0_uses_3069844'][1],0x03069844)

    def test_full_binary_when_present(self):
        exe=os.environ.get('WH3_903_EXE')
        if not exe:self.skipTest('Original WH3 EXE not distributed to CI')
        report=m.inspect(Path(exe))
        self.assertEqual(len(report['guards']),40)
        self.assertEqual(len(report['direct_edges']),16)
        self.assertEqual(len(report['checked_branches']),3)
        self.assertFalse(report['runtime_patch_authorized'])
        self.assertEqual(report['member_interaction_vtables']['virtual_4b0'],{'0x8d3280':4,'0x3069844':32})
        self.assertEqual(report['member_interaction_vtables']['virtual_4d0'],{'0x3069b10':36})

if __name__=='__main__':unittest.main()