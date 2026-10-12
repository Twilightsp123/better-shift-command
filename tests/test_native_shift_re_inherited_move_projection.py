"""Static contracts for native queued MOVE's inherited state-1 projection."""
import os,sys,tempfile,unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(SRC))
import audit_inherited_move_projection as m
from audit_wh3_full_native_chain import StrictPE

class InheritedNativeProjection(unittest.TestCase):
 def test_stage1_original_object_field_operations(self):
  self.assertEqual(len(m.PINS),27)
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
  self.assertEqual(proof['static_guard_count'],27)
  self.assertEqual(proof['constant_scale'],.5)
  self.assertTrue(proof['main_task_158_cleared_after_projection'])
  self.assertFalse(proof['native_queue_handoff_same_instance_confirmed'])
  self.assertFalse(proof['patch_authorized'])

if __name__=='__main__':unittest.main()
