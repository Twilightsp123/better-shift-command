"""R79 synthetic and exact-code contracts. Commercial EXE stays private."""
import importlib.util,json,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
spec=importlib.util.spec_from_file_location('a79',ROOT/'audit_r79_nav_goal.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
M=json.loads((ROOT/'r79_nav_goal_pins.json').read_text())
class R79(unittest.TestCase):
 def test_pin_count(self):self.assertEqual(len(M['pins']),31)
 def test_eight_sites(self):self.assertEqual(len(M['caller_sites']),8)
 def test_seven_owner_functions(self):self.assertEqual(len(set(x['owner'] for x in M['caller_sites'])),7)
 def test_goal_setter(self):self.assertEqual(M['goal_setter'],'0311e5dc')
 def test_local_builder(self):self.assertEqual(M['pins']['0307722b'],'e81c810a00')
 def test_local_prepared_copy(self):self.assertEqual(M['pins']['03077243'],'0f1101')
 def test_local_ref_copy(self):self.assertEqual(M['pins']['0307724b'],'f20f114910')
 def test_local_submit_early(self):self.assertEqual(M['pins']['03077127'],'e8b0740a00')
 def test_local_submit_late(self):self.assertEqual(M['pins']['0307741d'],'e8ba710a00')
 def test_setter_state_skip(self):self.assertEqual(M['pins']['0311e5e6'],'80b92802000001')
 def test_bit15(self):self.assertEqual(M['pins']['0311e601'],'410fbae10f')
 def test_bit9(self):self.assertEqual(M['pins']['0311e617'],'410fbae109')
 def test_ref_identity(self):self.assertEqual(M['pins']['0311e629'],'48394210')
 def test_heading_identity(self):self.assertEqual(M['pins']['0311e636'],'6639420c')
 def test_xyz_store(self):self.assertEqual(M['pins']['0311e6ca'],'0f1187e0010000')
 def test_ref_store(self):self.assertEqual(M['pins']['0311e6e8'],'f20f118ff0010000')
 def test_equal_goal_copied(self):self.assertTrue(a.synthetic((0,0,0),(0,0,0))['copies'])
 def test_equal_goal_state_kept(self):self.assertFalse(a.synthetic((0,0,0),(0,0,0))['clears_aux'])
 def test_epsilon_small(self):self.assertFalse(a.synthetic((0,0,0),(.009,.009,.009))['clears_aux'])
 def test_epsilon_large(self):self.assertTrue(a.synthetic((0,0,0),(.02,0,0))['clears_aux'])
 def test_heading_diff(self):self.assertTrue(a.synthetic((0,0,0),(0,0,0),heading_same=False)['clears_aux'])
 def test_ref_diff(self):self.assertTrue(a.synthetic((0,0,0),(0,0,0),ref_same=False)['clears_aux'])
 def test_force_bit9(self):self.assertTrue(a.synthetic((0,0,0),(0,0,0),bit9=True)['clears_aux'])
 def test_bit15_alternate(self):self.assertFalse(a.synthetic((0,0,0),(0,0,0),bit15=True,context=True)['copies'])
 def test_skip_mode(self):self.assertEqual(a.synthetic((0,0,0),(0,0,0),mode=1)['path'],'state_skip')
 def test_wrong_sha(self):
  with self.assertRaisesRegex(a.EvidenceError,'SHA_OR_SIZE'):a.verify(b'MZ'+bytes(100),M)
 def test_optional_game_exe(self):
  fn=os.environ.get('BSC_EXE')
  if not fn:self.skipTest('Original WH3 EXE not available in public Actions')
  self.assertFalse(a.verify(Path(fn).read_bytes(),M)['gameplay_patch_authorized'])
