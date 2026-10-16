"""Member goal record vs dynamic affine world target (private original EXE optional)."""
import os,sys,tempfile,subprocess,unittest
from pathlib import Path
NATIVE=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(NATIVE))
import audit_member_world_goal_resolution_20261016 as m
I=((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))
FLIP=((-1.,0.,0.),(0.,1.,0.),(0.,0.,-1.))
class MemberWorldGoal(unittest.TestCase):
 def test_guards(self):self.assertEqual((len(m.pins()),len(m.CALLS),len(m.BRANCHES)),(98,7,6))
 def test_member_route_record_pointer(self):
  self.assertEqual(m.CALLS[0x030720E3],m.CALLS[0x030723D9])
  self.assertEqual(m.CALLS[0x030720E3],0x0311954C)
  self.assertEqual(m.pins()[0x030720D1].hex(),'488d9338080000')
  self.assertEqual(m.pins()[0x030723CC].hex(),'488d9338080000')
 def test_goal_commit_stores_local_and_reference(self):
  self.assertEqual(m.pins()[0x0311963A].hex(),'0f1187e0010000')
  self.assertEqual(m.pins()[0x03119658].hex(),'f20f118ff00100')
 def test_main_member_tick_calls_motion_consumer(self):
  self.assertEqual(m.CALLS[0x030822F9],0x03054B84)
  self.assertEqual(m.CALLS[0x03055029],0x0311CED4)
 def test_resolver_uses_optional_anchor(self):
  self.assertEqual(m.pins()[0x0311CEDB].hex(),'488b4910')
  self.assertEqual(m.pins()[0x0311CEE4].hex(),'4883c118')
  self.assertEqual(m.CALLS[0x0311CEE8],0x02F38640)
 def test_no_anchor_copies_xyz(self):self.assertEqual(m.resolved_goal((3.,4.,5.)),(3.,4.,5.))
 def test_identity_frame(self):self.assertEqual(m.resolved_goal((2.,3.,4.),((0.,0.,0.),I)),(2.,3.,4.))
 def test_frame_translation(self):self.assertEqual(m.resolved_goal((2.,3.,4.),((10.,20.,30.),I)),(12.,23.,34.))
 def test_same_local_opposite_world_target_counterexample(self):
  x=(2.,0.,0.)
  self.assertEqual(m.resolved_goal(x,((0.,0.,0.),I)),(2.,0.,0.))
  self.assertEqual(m.resolved_goal(x,((0.,0.,0.),FLIP)),(-2.,0.,0.))
 def test_anchor_translation_changes_world_point(self):
  x=(0.,0.,0.)
  self.assertNotEqual(m.resolved_goal(x,((1.,0.,0.),I)),m.resolved_goal(x,((10.,0.,0.),I)))
 def test_invalid_affine_shape(self):
  with self.assertRaises(ValueError):m.affine_world((1,2,3),(0,0,0),((1,0,0),))
 def test_guarded_alternative_goal_writer(self):
  self.assertEqual(m.CALLS[0x03082301],0x03088808)
  self.assertEqual(m.CALLS[0x03088A49],0x03060D74)
  self.assertEqual(m.pins()[0x03060E5A].hex(),'0f1183e0010000')
  self.assertEqual(m.pins()[0x03060E66].hex(),'f20f118bf00100')
 def test_jcc_target_inventory(self):
  for at,t in m.BRANCHES.items():self.assertEqual(m.branch_target(at,m.pins()[at]),t)
 def test_wrong_sha_fail_closed_under_optimized_python(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'wrong.exe';f.write_bytes(b'MZ'+bytes(100))
   for options in ([],['-O']):
    p=subprocess.run([sys.executable,*options,str(m.__file__),'--exe',str(f)],capture_output=True,text=True)
    self.assertNotEqual(p.returncode,0);self.assertIn('SHA_MISMATCH',p.stderr)
 def test_original_exe_not_overwritten(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'game.exe';f.write_bytes(b'preserved')
   p=subprocess.run([sys.executable,str(m.__file__),'--exe',str(f),'--out',str(f)],capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0);self.assertIn('NEVER_OVERWRITE_GAME_EXE',p.stderr)
   self.assertEqual(f.read_bytes(),b'preserved')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original game EXE excluded from public GitHub')
 def test_private_original_exe(self):
  report=m.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((report['verified_instruction_starts'],report['verified_e8'],report['verified_jcc']),(98,7,6))
  self.assertFalse(report['specific_SHIFT_instance_anchor_mismatch_observed'])
  self.assertFalse(report['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
