"""Read-only exact-native B task timing/gating contracts; not a WH3 repair test."""
import os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"maintenance_tools"/"native_shift_re"))
import audit_b_deferred_tick_gate as a

class BDeferredTickGateTests(unittest.TestCase):
 def test_original_B_both_branches_clear_bit4(self):
  self.assertEqual(a.b_packet_initial_flag("a")&0x10,0)
  self.assertEqual(a.b_packet_initial_flag("b")&0x10,0)
 def test_two_packet_flag_variants(self):
  self.assertEqual(a.b_packet_initial_flag("a"),0x0e)
  self.assertEqual(a.b_packet_initial_flag("b"),0x07)
 def test_invalid_branch_denied(self):
  with self.assertRaises(ValueError):a.b_packet_initial_flag("invented")
 def test_bit4_task_virtual_is_readonly_getter(self):
  self.assertEqual(a.PIN[0x8f4dd0],"0fb68190000000")
  self.assertEqual(a.PIN[0x8f4dd7],"c0e804")
  self.assertEqual(a.PIN[0x8f4dda],"2401")
 def test_tick_arm_exclusivity_with_synthetic_state(self):
  self.assertEqual(a.special_tick_arm(0x14,0x10),"old_subaction_v10")
  self.assertEqual(a.special_tick_arm(0x10,0x10),"deferred_v80_flag_QUERY_not_task_tick")
  self.assertNotEqual(a.special_tick_arm(0x14,0x10),a.special_tick_arm(0x10,0x10))
 def test_non_special_arm_not_equivalent(self):
  self.assertEqual(a.special_tick_arm(0x14,4,False),"normal_actor_update")
 def test_B_bit7_is_not_the_common_tick_bit3_gate(self):
  self.assertEqual(a.PIN[0x30820a2],"f687100b000008")
  self.assertEqual(a.PIN[0x3263c0a],"0883100b0000")
  self.assertEqual(0x80&0x08,0)
 def test_no_fixed_one_tick_delay(self):
  self.assertEqual(a.PIN[0x2f5f91a],"41894a4c")
  self.assertEqual(a.PIN[0x2f5f843],"034b4c")
  self.assertEqual(a.PIN[0x2f6b190],"724e")
 def test_wrong_binary_fails_before_reads_or_writes(self):
  from audit_wh3_full_native_chain import StrictPE
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"wrong.exe";raw=b"MZ"+b"x"*160;p.write_bytes(raw)
   with self.assertRaisesRegex(ValueError,"SHA_MISMATCH"):StrictPE(p)
   self.assertEqual(p.read_bytes(),raw)
 def test_explicit_patch_no_go(self):
  self.assertIn("patch_authorized=False",(ROOT/"maintenance_tools"/"native_shift_re"/"audit_b_deferred_tick_gate.py").read_text())
 @unittest.skipUnless(os.getenv("WH3_903_EXE"),"Public CI has no original WH3 EXE")
 def test_original_exe(self):
  proof=a.verify(Path(os.getenv("WH3_903_EXE")))
  self.assertEqual(proof["branch_targets"],7)
  self.assertFalse(proof["patch_authorized"])
if __name__=="__main__":unittest.main()
