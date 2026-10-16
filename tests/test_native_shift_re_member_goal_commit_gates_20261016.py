"""Test the original WH3 goal-commit gates, with optional private binary."""
import os,sys,subprocess,tempfile,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_member_goal_commit_gates_20261016 as a
class MemberGoalCommit(unittest.TestCase):
 def test_inventory(self):
  self.assertEqual((len(a.pins()),len(a.E8),len(a.JCC)),(60,5,8))
 def test_float32_epsilon(self):
  self.assertEqual(struct.pack('<f',a.EPSILON),bytes.fromhex('0ad7233c'))
 def test_same_goal_suppression(self):
  self.assertTrue(a.goal_dedup((0,0,0),(.005,0,0),True,True,0))
 def test_heading_change_requires_update(self):
  self.assertFalse(a.goal_dedup((0,0,0),(0,0,0),True,False,0))
 def test_token_change_requires_update(self):
  self.assertFalse(a.goal_dedup((0,0,0),(0,0,0),False,True,0))
 def test_more_than_epsilon_requires_update(self):
  self.assertFalse(a.goal_dedup((0,0,0),(.05,0,0),True,True,0))
 def test_bit9_bypasses_same_goal_suppression(self):
  self.assertFalse(a.goal_dedup((0,0,0),(0,0,0),True,True,0x200))
 def test_typed_action_and_route_install_link(self):
  self.assertEqual(a.E8[0x0325ea85],0x03071e04)
  self.assertEqual(a.E8[0x03071e86],0x03071f20)
  self.assertEqual(a.pins()[0x0325ea8a].hex(),'c6467d01')
 def test_per_member_local_checks(self):
  for at in (0x0325e9e8,0x0325e9f6,0x0325ea14,0x0325ea21):
   self.assertIn(at,a.pins())
 def test_wrong_exe_fails_even_under_optimization(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'fake.exe';f.write_bytes(b'MZ'+bytes(128))
   for flags in ([],['-O']):
    out=subprocess.run([sys.executable,*flags,str(Path(a.__file__)),'--exe',str(f)],capture_output=True,text=True)
    self.assertNotEqual(out.returncode,0)
    self.assertIn('SHA_MISMATCH',out.stderr)
 def test_cannot_overwrite_exe(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'fake.exe';f.write_bytes(b'preserved')
   out=subprocess.run([sys.executable,str(Path(a.__file__)),'--exe',str(f),'--out',str(f)],capture_output=True,text=True)
   self.assertNotEqual(out.returncode,0)
   self.assertIn('EXE_OVERWRITE_FORBIDDEN',out.stderr)
   self.assertEqual(f.read_bytes(),b'preserved')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Original game EXE is private')
 def test_private_original_exe(self):
  result=a.audit(os.getenv('WH3_903_EXE'))
  self.assertEqual((result['guarded_instructions'],result['guarded_e8'],result['guarded_jcc']),(60,5,8))
  self.assertEqual(len(result['motor_goal_direct_call_sites']),8)
  self.assertEqual(len(result['route_installer_direct_call_sites']),25)
  self.assertFalse(result['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
