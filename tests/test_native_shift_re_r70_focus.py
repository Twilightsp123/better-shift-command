"""R70 public contract tests; commercial WH3 EXE intentionally excluded."""
import importlib.util,json,os,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"maintenance_tools"/"native_shift_re"
spec=importlib.util.spec_from_file_location("r70",ROOT/"audit_r70_focus.py")
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
M=json.loads((ROOT/"r70_focus_pins.json").read_text())
class R70(unittest.TestCase):
 def test_pin_count(self):self.assertEqual(len(M["pins"]),32)
 def test_call_targets(self):
  for k,t in M["e8"].items():self.assertEqual(r.call_target(int(k,16),M["pins"][k]),int(t,16))
 def test_same_member_two_loads(self):
  self.assertEqual(M["pins"]["03072efd"],"488bcb")
  self.assertEqual(M["pins"]["030731f8"],"488bcb")
 def test_both_sites_same_parent(self):
  self.assertEqual(M["e8"]["03072f00"],"0307db60")
  self.assertEqual(M["e8"]["030731fb"],"0307e1a0")
 def test_parent_does_not_call_setter(self):self.assertNotEqual(M["e8"]["03072f00"],"0307d9c0")
 def test_fifth_args_differ(self):
  self.assertEqual(M["pins"]["03072ef3"],"c644242000")
  self.assertEqual(M["pins"]["0307d9f0"],"c644242001")
 def test_mode_reset_fields(self):
  self.assertEqual(M["pins"]["0307d9d9"],"21913c020000")
  self.assertEqual(M["pins"]["0307d9df"],"2191c8010000")
 def test_gate_branch(self):
  self.assertEqual(M["pins"]["030731d5"],"7421")
  self.assertEqual(M["pins"]["03072f27"],"0f8502030000")
 def test_gate_field(self):self.assertEqual(M["pins"]["0307e1d6"],"0f2f873c020000")
 def test_not_shift_proven(self):self.assertFalse(M["mode_reset_to_gate_proven"])
 def test_reject_wrong_sha(self):
  with self.assertRaisesRegex(r.ContractError,"EXE_SHA_OR_SIZE_MISMATCH"):r.verify(b"MZ"+bytes(100),M)
 def test_optional_private_exact_exe(self):
  f=os.getenv("BSC_EXE")
  if not f:self.skipTest("private WH3 executable is not in public CI")
  self.assertFalse(r.verify(Path(f).read_bytes(),M)["mode_reset_to_gate_proven"])
if __name__=="__main__":unittest.main()
