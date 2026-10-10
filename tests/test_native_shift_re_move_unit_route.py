"""Synthetic-only tests for exact-SHA original MOVE-to-UnitRoot route proof."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"maintenance_tools"/"native_shift_re"
sys.path.insert(0,str(SCRIPT))
from audit_903_move_unit_route import GUARDS,CALLS,verify

class ExactMoveUnitRouteContracts(unittest.TestCase):
    def test_site_counts(self):
        self.assertEqual(len(GUARDS),23)
        self.assertEqual(len(CALLS),7)

    def test_two_original_move_entry_branches(self):
        self.assertEqual(CALLS["move_mode_a_to_config"][1],0x0301287C)
        self.assertEqual(CALLS["move_mode_b_to_config"][1],0x0301287C)

    def test_same_route_storage_across_branch_types(self):
        a=bytes.fromhex(GUARDS["config_store_heap_route"][1])
        b=bytes.fromhex(GUARDS["config_store_inline_route"][1])
        self.assertEqual(a[-4:],b[-4:])

    def test_fail_closed_on_synthetic_exe(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"synthetic.exe"
            p.write_bytes(b"MZ synthetic test")
            original=p.read_bytes()
            with self.assertRaisesRegex(ValueError,"EXE_SHA256_MISMATCH"):
                verify(p)
            self.assertEqual(p.read_bytes(),original)

    def test_code_forbids_runtime_mutation(self):
        source=(SCRIPT/"audit_903_move_unit_route.py").read_text()
        self.assertIn('"runtime_patch_authorized":False',source)
        self.assertNotIn("WriteProcessMemory(",source)

if __name__=="__main__":
    unittest.main()
