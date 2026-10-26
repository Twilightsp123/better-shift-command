"""R76 public contract tests. Matching commercial EXE is not in GitHub CI."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_r76_focused as a
M=json.loads((ROOT/'r76_focused_pins.json').read_text())
class R76(unittest.TestCase):
 def test_pins(self):self.assertEqual(len(M['focused_pins']),44)
 def test_e8_count(self):self.assertEqual(len(M['e8_edges']),8)
 def test_branch_count(self):self.assertEqual(len(M['branches']),5)
 def test_member_types(self):
  self.assertEqual(M['member_vmethods'],{'18':'03086f04','20':'030592bc'})
 def test_tick_to_steering(self):self.assertEqual(M['e8_edges']['03087349'],'03059bc8')
 def test_velocity_guard(self):
  self.assertEqual(M['branches']['0305a05b'],'0305a1a5')
  self.assertEqual(M['focused_pins']['0305a058'],'0f2ff8')
 def test_stack_world_goal(self):
  self.assertEqual(M['focused_pins']['0305a061'],'488d8fe0010000')
  self.assertEqual(M['focused_pins']['0305a068'],'488d542460')
 def test_callee_returns_output_buffer(self):
  self.assertEqual(M['focused_pins']['03121f82'],'488bc2')
  self.assertEqual(M['focused_pins']['02f3d6dc'],'f30f1112')
 def test_world_goal_branch(self):
  self.assertFalse(a.synthetic_partition(1,4,False,True)['world_goal_branch'])
  self.assertTrue(a.synthetic_partition(9,4,False,True)['world_goal_branch'])
 def test_integrator_flag(self):
  self.assertEqual(M['focused_pins']['031471b5'],'f6c202')
  self.assertEqual(M['focused_pins']['031471c1'],'f6c104')
 def test_distinct_decisions(self):
  x=a.synthetic_partition(9,4,False,False)
  self.assertTrue(x['world_goal_branch'])
  self.assertEqual(x['integrator_branch'],'skip')
  self.assertFalse(x['same_shift_instance_proven'])
 def test_wrong_scalar(self):
  with self.assertRaisesRegex(ValueError,'INVALID_SYNTHETIC'):
   a.synthetic_partition(float('nan'),3,False,True)
 def test_wrong_sha(self):
  with self.assertRaisesRegex(a.StaticDrift,'SHA_OR_SIZE'):
   a.verify(b'MZ'+bytes(128),M)
 def test_original_exe_optional(self):
  fn=os.environ.get('BSC_EXE')
  if not fn:self.skipTest('Original licensed game EXE excluded from public CI')
  self.assertEqual(a.verify(Path(fn).read_bytes(),M)['pins'],44)
