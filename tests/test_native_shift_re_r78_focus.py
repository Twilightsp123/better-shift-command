"""R78 public tests. Original commercial EXE is intentionally optional."""
import importlib.util,json,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
spec=importlib.util.spec_from_file_location('a78',ROOT/'audit_r78_focus.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
M=json.loads((ROOT/'r78_focus_pins.json').read_text())
class R78(unittest.TestCase):
 def test_pin_count(self):self.assertEqual(len(M['pins']),39)
 def test_e8_count(self):self.assertEqual(len(M['e8']),12)
 def test_function_count(self):self.assertEqual(len(M['functions']),10)
 def test_member_methods(self):self.assertEqual(len(M['methods']),3)
 def test_ctor_edge(self):self.assertEqual(M['e8']['030da588'],'02f64870')
 def test_fifth_arg(self):self.assertEqual(M['pins']['030da577']['hex'],'c644242001')
 def test_flags50(self):self.assertEqual(M['pins']['02f648c5']['hex'],'c6435026')
 def test_reset_then_set51(self):
  self.assertEqual(M['pins']['02f648a5']['hex'],'24fd')
  self.assertEqual(M['pins']['02f775b2']['hex'],'80495102')
 def test_modifier_edge(self):self.assertEqual(M['e8']['02f648d5'],'02f775ac')
 def test_heading_edge(self):self.assertEqual(M['e8']['02f775ce'],'030844c8')
 def test_local_position_edge(self):self.assertEqual(M['e8']['03070acd'],'03084618')
 def test_frame_convert(self):self.assertEqual(M['e8']['03122160'],'02f3d668')
 def test_physical_simple(self):self.assertEqual(M['e8']['030785b5'],'0316460c')
 def test_physical_complex(self):self.assertEqual(M['e8']['030782cf'],'03163dc4')
 def test_simple_xyz(self):self.assertEqual(M['pins']['03164658']['hex'],'f20f118788000000')
 def test_complex_xyz(self):self.assertEqual(M['pins']['0316443d']['hex'],'f20f118e88000000')
 def test_model_mode1(self):self.assertEqual(a.model(1)['vslot'],'100')
 def test_model_mode0(self):self.assertEqual(a.model(0)['vslot'],'e8')
 def test_model_fifth0(self):self.assertFalse(a.model(2,0)['member_adjust'])
 def test_no_unproved_nav_link(self):self.assertFalse(a.model(2)['final_nav_goal_proven'])
 def test_wrong_sha(self):
  with self.assertRaisesRegex(a.EvidenceDrift,'SHA_FAIL'):a.verify(b'MZ'+bytes(100),M)
 def test_private_exact_exe(self):
  f=os.environ.get('BSC_EXE')
  if not f:self.skipTest('Licensed WH3 EXE excluded from public CI')
  self.assertFalse(a.verify(Path(f).read_bytes(),M)['gameplay_patch_authorized'])
