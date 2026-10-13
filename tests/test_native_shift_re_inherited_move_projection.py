"""Static contracts for native queued MOVE's inherited state-1 projection."""
import os,sys,tempfile,unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(SRC))
import audit_inherited_move_projection as m
from audit_wh3_full_native_chain import StrictPE

class InheritedNativeProjection(unittest.TestCase):
 def test_stage1_original_object_field_operations(self):
  self.assertEqual(len(m.PINS),48)
  self.assertEqual(m.PINS[0x0311E64C],'48894320')
  self.assertEqual(m.PINS[0x0311E6EC],'4c89af58010000')
  self.assertEqual(m.PINS[0x0311DEAA],'4533ed')
  self.assertEqual(m.PINS[0x0311DEC0],'0f84b2060000')
  self.assertEqual(m.PINS[0x030EE908],'4d898258010000')
  self.assertEqual(m.PINS[0x0312058B],'49898558010000')

 def test_symmetric_old_direction_projection_math(self):
  begin,end=m.projected_endpoints(100.,200.,1.,0.,10.)
  self.assertEqual(begin,(95.,200.))
  self.assertEqual(end,(105.,200.))
  begin,end=m.projected_endpoints(-2.,3.,0.,1.,4.)
  self.assertEqual(begin,(-2.,1.))
  self.assertEqual(end,(-2.,5.))
  self.assertEqual(m.projected_endpoints(0,0,-1,0,8),((4.,0.),(-4.,0.)))

 def test_state1_old_direction_projection_requires_fresh_flag(self):
  # It resets +0x24 first, calls the SAME geometry builder as new state0,
  # then transfers old+0x158 only on a fresh positive native result.
  self.assertEqual(m.PINS[0x0311E5B3],'44886f24')
  self.assertEqual(m.PINS[0x0311E636],'e8d1010000')
  self.assertEqual(m.PINS[0x0311E63B],'807f2401')
  self.assertEqual(m.PINS[0x0311E63F],'0f859b010000')
  self.assertEqual(m.PINS[0x0311E772],'e895000000')
  self.assertEqual(m.PINS[0x0311EB10],'40887e24')
  self.assertEqual(m.PINS[0x0311EB04],'4584c0')
  self.assertEqual(m.PINS[0x0311EB09],'84d2')
  self.assertEqual(m.PINS[0x0311EB0D],'418af9')
  self.assertEqual(m.PINS[0x0311E64C],'48894320')
  self.assertEqual(m.PINS[0x0311E6EC],'4c89af58010000')

 def test_common_builder_is_not_unique_to_shift_queued_state(self):
  # One helper called from state0 AND state1. This excludes the naive
  # interpretation that the helper's presence identifies Shift.
  self.assertNotEqual(0x0311E636,0x0311E772)
  self.assertEqual(m.PINS[0x0311EB14],'413af9')
  self.assertEqual(m.PINS[0x0311EB17],'0f85bb000000')

 def test_wrong_original_exe_is_rejected_before_native_read(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'wrong.exe';data=b'MZ'+b'other-version'*100
   path.write_bytes(data)
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):StrictPE(path)
   self.assertEqual(path.read_bytes(),data)

 @unittest.skipUnless(os.getenv('WH3_903_EXE'),
                      'Private original game binary not present in GitHub CI')
 def test_original_game_rva_and_0_5_constant(self):
  proof=m.audit(os.environ['WH3_903_EXE'])
  self.assertEqual(proof['static_guard_count'],48)
  self.assertEqual(proof['constant_scale'],.5)
  self.assertEqual(proof['stage1_native_call_edges_checked'],3)
  self.assertEqual(proof['stage1_conditional_branch_edges_checked'],3)
  self.assertTrue(proof['state1_old_projection_only_if_recomputed_flag_is_one'])
  self.assertTrue(proof['state1_flag_not_one_skips_old_subtask_transfer_and_main_pointer_clear'])
  self.assertFalse(proof['every_queued_move_inherits_prior_direction'])
  self.assertTrue(proof['main_task_158_cleared_after_projection'])
  self.assertFalse(proof['native_queue_handoff_same_instance_confirmed'])
  self.assertFalse(proof['patch_authorized'])

if __name__=='__main__':unittest.main()
