"""Synthetic-only contracts for the 9.0.3 member VTable receiver resolver."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"maintenance_tools"/"native_shift_re"))
from audit_903_member_virtual_receivers import GUARDS, GETTER, RECEIVERS, SHA, verify

class MemberReceiverContracts(unittest.TestCase):
    def test_three_resolved_native_handlers(self):
        self.assertEqual(RECEIVERS,{0x0306B9F0,0x0306B9CC,0x03117CE0})
        self.assertEqual(GETTER,0x008F37B0)

    def test_exact_instruction_guard_coverage(self):
        self.assertEqual(len(GUARDS),16)
        self.assertEqual(GUARDS["member_virtual_fanout"][0],0x030D550F)

    def test_both_secondary_virtuals(self):
        self.assertEqual(GUARDS["member_virtual_100"][1],"41ff9300010000")
        self.assertEqual(GUARDS["member_virtual_e8"][1],"41ff93e8000000")

    def test_member_coordinate_writer_is_not_an_arrival_predicate(self):
        self.assertEqual(GUARDS["member_coordinate_pair_write"][0],0x0315F52C)
        self.assertEqual(GUARDS["member_angle_like_write"][0],0x0315F54C)

    def test_wrong_binary_fails_closed_without_writing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.exe";data=b"MZ synthetic"
            p.write_bytes(data)
            with self.assertRaisesRegex(ValueError,"EXE_SHA256_MISMATCH"):
                verify(p)
            self.assertEqual(p.read_bytes(),data)

    def test_static_only_contract(self):
        script=(ROOT/"maintenance_tools"/"native_shift_re"/"audit_903_member_virtual_receivers.py").read_text(encoding="utf-8")
        self.assertIn('"runtime_patch_authorized":False',script)
        self.assertNotIn("WriteProcessMemory(",script)
        self.assertEqual(len(SHA),64)

if __name__=="__main__":unittest.main()
