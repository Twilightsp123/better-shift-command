"""Real stack packet vs MOVE task, exact WH3 9.0.3 private EXE optional."""
import os,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'))
import audit_virtual388_stack_packet as a
class StackPacketProvenance(unittest.TestCase):
 def test_bounded_three_calls_same_frame(self):
  self.assertEqual(a.OWNER,(0x03010724,0x0301120E))
  self.assertEqual(tuple(a.PACKETS),(0x03010B0F,0x03010DAE,0x03011078))
 def test_immediate_RDX_is_stack_address_not_task_offset(self):
  for call,seq in a.PACKETS.items():
   self.assertEqual(a.PINS[seq[0]],'488d5500')
   self.assertEqual(a.PINS[call],'ff9088030000')
 def test_flags_and_float_written_on_caller_frame(self):
  for call,seq in a.PACKETS.items():
   self.assertEqual(a.PINS[seq[3]],'804d6c20')
   self.assertEqual(a.PINS[seq[4]],'f30f114558')
 def test_object_receiver_from_rdi_not_local_record(self):
  for call,seq in a.PACKETS.items():
   self.assertEqual((a.PINS[seq[1]],a.PINS[seq[2]]),('488b07','488bcf'))
 def test_all_three_upstream_calls_same_helper(self):
  self.assertEqual(len(a.SOURCES),3)
  self.assertEqual(set(a.SOURCES.values()),{0x030A48A4})
 def test_wrong_SHA_rejected(self):
  class Wrong:
   sha='bad'
   def close(self):pass
  with patch.object(a,'StrictPE',return_value=Wrong()):
   with self.assertRaisesRegex(ValueError,'WRONG_EXE'):
    a.audit(Path('fake.exe'))
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Private WH3 EXE not in GitHub CI')
 def test_exact_original_exe(self):
  r=a.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual((r['exact_instructions'],r['bounded_virtual388_stack_dispatches']),(24,3))
  self.assertFalse(r['direct_input_is_MOVE_task_plus160'])
  self.assertFalse(r['native_patch_authorized'])
if __name__=='__main__':unittest.main()
