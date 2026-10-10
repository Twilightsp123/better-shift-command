"""Synthetic contracts only; exact game executable is never committed."""
import mmap
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"maintenance_tools"/"native_shift_re"))
from audit_903_member_layers import GUARDS, CALLS, verify
from audit_903_formation_entry import pe_sections,read_executable,e8_target
from test_native_shift_re_formation import fixture

class MemberLayerContracts(unittest.TestCase):
 def test_pinned_structure_checks(self):
  self.assertEqual(len(GUARDS),23)
  self.assertEqual(len(CALLS),4)

 def test_distinct_root_vectors(self):
  self.assertEqual(GUARDS["same_root_A_count"][0],0x0303D6B3)
  self.assertEqual(GUARDS["same_root_B_count"][0],0x0303D73D)
  self.assertNotEqual(GUARDS["same_root_A_ptr"][1],GUARDS["same_root_B_ptr"][1])

 def test_nested_type_not_asserted(self):
  self.assertEqual(GUARDS["A_entry_virtual_58"][1],"ff5058")
  self.assertEqual(GUARDS["child_count"][1],"8b80e40b0000")
  self.assertEqual(GUARDS["child_array"][1],"4c8bb0e80b0000")

 def test_early_member_calls_before_queue_processing(self):
  self.assertLess(CALLS["unit_to_position_aggregate"][0],CALLS["unit_to_queue"][0])
  self.assertLess(CALLS["unit_to_group_coordinate"][0],CALLS["unit_to_queue"][0])
  self.assertGreater(CALLS["unit_to_post_order_callbacks"][0],CALLS["unit_to_queue"][0])

 def test_wrong_digest_fails_closed(self):
  with tempfile.TemporaryDirectory() as tmp:
   exe=Path(tmp)/"Warhammer3.exe"
   data=fixture()
   exe.write_bytes(data)
   with self.assertRaisesRegex(ValueError,"EXE_SHA256_MISMATCH"):
    verify(exe)
   self.assertEqual(exe.read_bytes(),data)

 def test_e8_decoding(self):
  self.assertEqual(e8_target(0x1000,bytes.fromhex("e805000000")),0x100A)
  with self.assertRaises(ValueError):
   e8_target(0x1000,bytes.fromhex("9000000000"))

if __name__=="__main__":
 unittest.main()
