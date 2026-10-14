"""Original WH3 B node geometry & B-family task subclasses (static contract only)."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'))
import audit_b_node_route_identity_gate as a

class BNodeIdentityGate(unittest.TestCase):
 def test_typed_B_task_is_third_nearby_vtable(self):
  self.assertEqual(a.TYPED_TASK_SLOTS[0x03AE0138],0x03281408)
  self.assertEqual(a.TYPED_TASK_SLOTS[0x03AE00F8],0x03281520)
  self.assertEqual(a.TYPED_TASK_SLOTS[0x03AE0118],0x03281600)
  self.assertEqual(len(set(a.TYPED_TASK_SLOTS.values())),3)
 def test_manager_uses_different_task_and_node_lists(self):
  self.assertEqual(a.PINS[0x03128EA8].hex(),'488bbbf0010000')
  self.assertEqual(a.PINS[0x03129031].hex(),'488bbbd0020000')
  self.assertEqual(a.PINS[0x031290C0].hex(),'488bbb88020000')
  self.assertEqual(a.PINS[0x03109DEF].hex(),'483991f8020000')
 def test_node_converter_receives_embedded_subobject(self):
  self.assertEqual(a.PINS[0x0312907E].hex(),'488d5720')
  self.assertEqual(a.PINS[0x03129082].hex(),'488bca')
  self.assertEqual(a.CALLS[0x03129085],0x0311BE18)
  self.assertEqual(a.CALLS[0x03129092],0x030FDA9C)
  self.assertEqual(a.PINS[0x030FDAC7].hex(),'488b0a')
 def test_rdx_survival_is_not_assumed_from_the_ABI(self):
  self.assertTrue(a._assert_rdx_survival(['mov eax,[rcx]','call 0x3037a48'],
                                          ['mov eax,[rcx]','ret'],['test eax,eax','je 0x31290a2','lea rcx,[rbx+0x18]']))
  with self.assertRaisesRegex(ValueError,'RDX_PROPAGATION_UNPROVEN'):
   a._assert_rdx_survival(['call 0x3037a48'],['xor edx,edx','ret'],[])
  with self.assertRaisesRegex(ValueError,'TYPE_VALIDATION_LEAF_NOT_LEAF'):
   a._assert_rdx_survival(['call 0x3037a48'],['call 0x123456','ret'],[])
  with self.assertRaisesRegex(ValueError,'VALIDATOR_GAINED_CALL'):
   a._assert_rdx_survival(['ret'],['ret'],[])
 def test_task_aware_node_starts_valid_generic_can_recompute(self):
  self.assertEqual(a.PINS[0x030ECB2E].hex(),'66c741080100')
  self.assertEqual(a.PINS[0x03121A25].hex(),'6683630800')
  self.assertEqual(a.PINS[0x03129078].hex(),'44386708')
  self.assertEqual(a.BRANCHES[0x0312907C],0x031290A2)
 def test_invalid_B_node_checks_route_reference_not_motor(self):
  self.assertEqual(a.PINS[0x03281469].hex(),'488b4970')
  self.assertEqual(a.CALLS[0x0328146D],0x030DEA20)
  self.assertEqual(a.PINS[0x030DEA5F].hex(),'483b4378')
  self.assertEqual(a.PINS[0x030DEA55].hex(),'488b9060010000') # vtable+160, not bigTask+160
 def test_mismatch_releases_both_old_node_and_big_task(self):
  self.assertEqual(a.PINS[0x03281480].hex(),'4883635800')
  self.assertEqual(a.PINS[0x0328148C].hex(),'4883632000')
  self.assertEqual(a.CALLS[0x032814FB],0x03121ABC)
  self.assertEqual(a.CALLS[0x0328150A],0x031219B0)
 def test_synthetic_branch_ref_matches_and_keeps_node(self):
  self.assertEqual(a.synthetic_branch(big_task_ref=True,existing_node=True,old_subtask=True,reference_changed=False),'RETAIN_EXISTING_NODE')
 def test_synthetic_branch_ref_mismatch_can_switch_to_generic(self):
  self.assertEqual(a.synthetic_branch(big_task_ref=True,existing_node=True,old_subtask=True,reference_changed=True),'CREATE_GENERIC_NODE')
 def test_synthetic_branch_waits_for_missing_old_subtask(self):
  self.assertEqual(a.synthetic_branch(big_task_ref=True,existing_node=False,old_subtask=False,reference_changed=False),'WAIT_FOR_OLD_SUBTASK')
 def test_synthetic_branch_task_aware_if_initially_eligible(self):
  self.assertEqual(a.synthetic_branch(big_task_ref=True,existing_node=False,old_subtask=True,reference_changed=False),'CREATE_TASK_AWARE_NODE')
 def test_reference_check_not_repeated_when_already_marked(self):
  self.assertEqual(a.synthetic_branch(big_task_ref=True,existing_node=True,old_subtask=True,reference_changed=True,checkpoint_checked=True),'RETAIN_EXISTING_NODE')
 def test_writer_and_checker_share_route_object_reference_field(self):
  self.assertEqual(a.CALLS[0x030FE272],0x030C1FDC)
  self.assertEqual(a.PINS[0x030FE277].hex(),'488bf8') # rdi = created geometry
  self.assertEqual(a.PINS[0x030FE284].hex(),'488bcf') # rcx = same route object
  self.assertEqual(a.CALLS[0x030FE287],0x030C7858)
  self.assertEqual(a.PINS[0x030C786F].hex(),'488bd9') # rbx = route object
  self.assertEqual(a.PINS[0x030C78D0].hex(),'48894378') # route+78 reference
  self.assertEqual(a.PINS[0x030FE29A].hex(),'488bc7') # returned same object
  self.assertEqual(a.CALLS[0x030ECB98],0x030FE1E4)
  self.assertEqual(a.PINS[0x030ECBA2].hex(),'48894370') # node+70 = route
  self.assertEqual(a.PINS[0x030DEA5F].hex(),'483b4378') # later route+78 read
 def test_reference_writer_and_node_segment_walk_are_conditional(self):
  self.assertEqual(a.PINS[0x030C78C8].hex(),'3c01')
  self.assertEqual(a.BRANCHES[0x030C78CA],0x030C78D4)
  self.assertEqual(a.CALLS[0x030C78B1],0x0312D088)
  self.assertEqual(a.PINS[0x030FE28C].hex(),'488b5b08')
  self.assertEqual(a.BRANCHES[0x030FE293],0x030FE280)
 def test_bounded_original_coverage(self):
  self.assertEqual(len(a.PINS),140)
  self.assertEqual(len(a.CALLS),17)
  self.assertEqual(len(a.BRANCHES),8)
 def test_wrong_exe_fail_closed(self):
  class Wrong:
   sha='incorrect-sha'
   closed=False
   def close(self):self.closed=True
  wrong=Wrong()
  with patch.object(a,'StrictPE',return_value=wrong):
   with self.assertRaisesRegex(ValueError,'EXE_SHA256_MISMATCH'):
    a.audit(Path('invalid.exe'))
  self.assertTrue(wrong.closed)
 @unittest.skipUnless(os.environ.get('WH3_903_EXE'),'Original EXE excluded from public GitHub CI')
 def test_original_unmodified_wh3_exe(self):
  report=a.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(report['opcode_instruction_starts'],140)
  self.assertEqual(report['direct_calls'],17)
  self.assertTrue(report['rdx_retained_after_validator_on_checked_path'])
  self.assertFalse(report['B_node70_to_motor_goal_proven'])
  self.assertFalse(report['native_patch_authorized'])

if __name__=='__main__':unittest.main()
