"""Exact-WH3 B fallback node retry and bounded synthetic negative controls."""
import os,sys,tempfile,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_b_fallback_manager_retry_20261016 as m

class BFallbackManagerRetry(unittest.TestCase):
 def test_inventory(self):
  self.assertEqual((len(m.PINS),len(m.E8),len(m.JCC),len(m.VTABLE)),(78,9,9,1))
 def test_first_unhandled_live_node_eligible(self):
  self.assertTrue(m.manager_can_attempt(linked_and_live=True,handled=False,validator_nonzero=1,prior_attempts=0))
 def test_validator_zero_blocks_retry(self):
  self.assertFalse(m.manager_can_attempt(linked_and_live=True,handled=False,validator_nonzero=0,prior_attempts=0))
 def test_processed_node_not_retried(self):
  self.assertFalse(m.manager_can_attempt(linked_and_live=True,handled=True,validator_nonzero=1,prior_attempts=0))
 def test_one_conversion_budget(self):
  self.assertFalse(m.manager_can_attempt(linked_and_live=True,handled=False,validator_nonzero=1,prior_attempts=1))
 def test_unlinked_node_not_processed(self):
  self.assertFalse(m.manager_can_attempt(linked_and_live=False,handled=False,validator_nonzero=1,prior_attempts=0))
 def test_validator_sentinel_uses_context_result(self):
  self.assertEqual(m.validator_result(0xffffffff,5),5)
  self.assertEqual(m.validator_result(0xffffffff,0),0)
 def test_validator_direct_field_is_not_context_mode(self):
  self.assertEqual(m.validator_result(0,5),0)
  self.assertEqual(m.validator_result(7,0),7)
 def test_fallback_record_sentinel_and_converter(self):
  self.assertEqual(m.PINS[0x030ecaa4],bytes.fromhex('c74148ffffffff'))
  self.assertEqual(m.E8[0x03121a99],m.E8[0x03129092])
 def test_manager_budget_pins(self):
  self.assertEqual(m.PINS[0x03128ec6],bytes.fromhex('458d6c2401'))
  self.assertEqual(m.PINS[0x03129038],bytes.fromhex('418bec'))
  self.assertEqual(m.PINS[0x0312909b],bytes.fromhex('4103ed'))
 def test_processed_flag_does_not_guarantee_nonnull_route(self):
  self.assertEqual(m.PINS[0x0312909e],bytes.fromhex('44886f08'))
  self.assertEqual(m.PINS[0x03281554],bytes.fromhex('488b4070'))
 def test_wrong_exe_fails_closed_under_python_optimized(self):
  with tempfile.TemporaryDirectory() as d:
   wrong=Path(d)/'bad.exe';wrong.write_bytes(b'MZ'+bytes(100))
   for opts in ([],['-O']):
    r=subprocess.run([sys.executable,*opts,str(ROOT/'audit_b_fallback_manager_retry_20261016.py'),'--exe',str(wrong)],capture_output=True,text=True)
    self.assertNotEqual(r.returncode,0)
    self.assertIn('SHA_MISMATCH',r.stderr)
 def test_exe_overwrite_forbidden(self):
  with tempfile.TemporaryDirectory() as d:
   wrong=Path(d)/'game.exe';wrong.write_bytes(b'unmodified')
   r=subprocess.run([sys.executable,str(ROOT/'audit_b_fallback_manager_retry_20261016.py'),'--exe',str(wrong),'--out',str(wrong)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
   self.assertIn('EXE_OVERWRITE_FORBIDDEN',r.stderr)
   self.assertEqual(wrong.read_bytes(),b'unmodified')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'original WH3 exe never shipped in CI')
 def test_original_exe(self):
  d=m.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((d['opcode_instruction_starts'],d['E8_edges'],d['JCC_edges'],d['typed_vtable_slots']),(78,9,9,1))
  self.assertFalse(d['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
