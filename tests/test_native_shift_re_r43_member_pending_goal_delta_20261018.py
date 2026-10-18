#!/usr/bin/env python3
"""R43 SHA-locked native static checks. Synthetic tests are NOT gameplay evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'maintenance_tools'/'native_shift_re'))
import audit_r43_member_pending_goal_delta_20261018 as a


class R43PendingMemberHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=a.inventory()
        cls.pins={at:b for group in cls.g.values() for at,b in group['pins'].items()}

    def test_01_manifest_has_101_opcode_sites(self):self.assertEqual(len(self.pins),101)
    def test_02_manifest_has_nine_distinct_function_groups(self):self.assertEqual(len(self.g),9)
    def test_03_member_constructor_virtual_type(self):
        self.assertEqual(a.VTABLE_SLOTS[0x18],0x03086F04)
        self.assertEqual(a.VTABLE_SLOTS[0x20],0x030592BC)
    def test_04_tick_gate_and_pointers_to_inline_fields(self):
        for at in (0x03086FD2,0x03086FE5,0x03086FF1,0x0308700C,0x03087013):
            self.assertIn(at,self.g['member_tick']['pins'])
    def test_05_tick_zero_setup(self):self.assertEqual(self.pins[0x03086F48],bytes.fromhex('4533f6'))
    def test_06_member_target_copy_positions(self):
        self.assertIn(0x03065E9E,self.pins)
        self.assertIn(0x03065EAA,self.pins)
    def test_07_motion_vector_passes_into_same_member(self):
        self.assertIn(0x03065E98,self.pins)
        self.assertIn(0x03065EB2,self.pins)
    def test_08_delta_writer_installs_three_components(self):
        self.assertIn(0x03154A10,self.pins)
        self.assertIn(0x03154A18,self.pins)
        self.assertIn(0x031549DC,self.pins)
    def test_09_pending_flag_clear_precedes_consumer_call(self):
        self.assertLess(0x0308700C,0x03087013)
        self.assertLess(0x03087013,0x03087018)
    def test_10_vector_and_status_are_not_always_applied(self):
        self.assertEqual(a.JUMPS[0x03086FD9],0x0308706F)
    def test_11_both_14c_and_150_writer_fields_reset(self):
        for group,sites in [('delta_install',[0x03154A26,0x03154A44]),
                            ('delta_alt',[0x0315FBBA,0x0315FBCA]),
                            ('integrator',[0x031472E7,0x031472FE,0x03148442,0x03148452])]:
            for at in sites:self.assertIn(at,self.g[group]['pins'])
    def test_12_same_integrator_reuses_delta_fields(self):
        self.assertIn(0x031471B8,self.pins)
        self.assertIn(0x031471C4,self.pins)
    def test_13_alternate_goal_delta_clears_before_state_update(self):
        self.assertLess(0x03071CC9,0x03071CE5)
        self.assertIn(0x0315FB68,self.pins)
    def test_14_leaf_helper_must_not_assume_volatile_preservation(self):
        self.assertIn('unlink_leaf',self.g)
        self.assertEqual(self.g['unlink_leaf']['span'],(0x03169594,0x03169629))
    def test_15_all_expected_e8_sites_are_pinned(self):
        for at in a.CALLS:self.assertEqual(self.pins[at][0],0xe8)
    def test_16_decode_e8_targets(self):
        import struct
        for at,dst in a.CALLS.items():
            self.assertEqual(at+5+struct.unpack_from('<i',self.pins[at],1)[0],dst)
    def test_17_decode_branch_targets(self):
        from audit_r35_group_transaction_20261017 import branch_dest
        for at,dst in a.JUMPS.items():self.assertEqual(branch_dest(at,self.pins[at]),dst)
    def test_18_caller_inventory_has_only_scoped_function_list(self):
        self.assertEqual(a.DIRECT_CALLER_EXPECTED[0x03154974],(0x03065EB2,))
        self.assertEqual(a.DIRECT_CALLER_EXPECTED[0x0315FB24],(0x03071CC9,))
    def test_19_manifest_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            bad=Path(d)/'bad.txt';content=a.MANIFEST.read_text('utf8');
            bad.write_text(content.replace('03154974 ','# deleted pin 03154974 ',1),'utf8')
            with self.assertRaisesRegex(ValueError,'PIN_OR_GROUP_COUNT_DRIFT'):
                a.inventory(bad)

    def test_20_invalid_exe_fails_closed_and_never_changes_file(self):
        with tempfile.TemporaryDirectory() as d:
            fake=Path(d)/'game.exe';fake.write_bytes(b'MZ'+b'garbage'*20)
            out=Path(d)/'report.json'
            r=subprocess.run([sys.executable,str(Path(a.__file__)),'--exe',str(fake),'--out',str(out)],text=True,capture_output=True)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('EXE_SHA256_MISMATCH',r.stderr)
            self.assertFalse(out.exists())
            self.assertEqual(fake.read_bytes(),b'MZ'+b'garbage'*20)
    def test_21_summary_never_claims_runtime_cause(self):
        self.assertIn('gameplay_patch_authorized',Path(a.__file__).read_text('utf8'))
        self.assertIn('root_cause_proven=False',Path(a.__file__).read_text('utf8'))
    @unittest.skipUnless(os.getenv('WH3_20261018_EXE'),'private SHA-locked game EXE is not present in public CI')
    def test_22_full_real_exe(self):
        r=a.audit(os.getenv('WH3_20261018_EXE'))
        self.assertEqual(r['exe_sha256'],a.SHA)
        self.assertEqual((r['pinned_opcode_starts'],r['validated_direct_e8'],r['validated_jumps'],r['validated_vtable_slots']),(101,6,6,3))
        self.assertFalse(r['root_cause_proven'])
        self.assertFalse(r['gameplay_patch_authorized'])

if __name__=='__main__':unittest.main()
