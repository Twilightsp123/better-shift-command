"""Exact native sender-vs-vtable-slot identity and historical trace controls."""
import os,sys,tempfile,unittest,json
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/"maintenance_tools"/"native_shift_re"
sys.path.insert(0,str(SRC))
import audit_receiver_identity as a
from audit_wh3_full_native_chain import StrictPE

class ReceiverSourceIdentityTest(unittest.TestCase):
 def test_negative_vtable_type_is_independent_of_same_slot(self):
  self.assertEqual(a.GUARDS["A_member_virtual_call"][1],
                   a.GUARDS["different_object_virtual_call"][1])
  self.assertEqual(a.GUARDS["different_object_reads_result_bool"][1],"8ad8")
 def test_wrong_exe_refuses(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"not-wh3.exe";b=b"MZ"+b"x"*100;p.write_bytes(b)
   with self.assertRaisesRegex(ValueError,"SHA_MISMATCH"):StrictPE(p)
   self.assertEqual(p.read_bytes(),b)
 @unittest.skipUnless(os.getenv("WH3_903_EXE") and os.getenv("BSC_REAL_TRACE_JSONL"),
                      "CI excludes game EXE and user's private runtime trace")
 def test_actual_machine_code_and_original_trace(self):
  r=a.audit(os.getenv("WH3_903_EXE"),os.getenv("BSC_REAL_TRACE_JSONL"))
  self.assertEqual(r["original_byte_guards"],14)
  self.assertEqual(r["receiver_calls_mislabelled_as_B"],28)
  self.assertEqual(r["original_caller_return_address_events"],0)
  self.assertEqual(r["packet_50"],{2:28})
  self.assertEqual(r["packet_44"],{0:28})
  self.assertFalse(r["native_patch_authorized"])
if __name__=="__main__":unittest.main()
