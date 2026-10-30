"""R86 public CI: actual algorithms + exact SHA-pinned native instruction contracts."""
import json,os,sys,unittest,math
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"maintenance_tools"/"native_shift_re"
sys.path.insert(0,str(P))
import r86_spatial as s
import audit_r86_spatial as a
M=json.loads((P/"r86_motion_pins.json").read_text())
class R86(unittest.TestCase):
 def test_native_pins(self):self.assertEqual(len(M["pins"]),28)
 def test_native_calls(self):self.assertEqual(len(M["e8"]),4)
 def test_native_branches(self):self.assertEqual(len(M["jcc"]),4)
 def test_native_functions(self):self.assertEqual(len(M["functions"]),5)
 def test_actual_position_writer(self):self.assertEqual(M["pins"]["0314720b"]["hex"],"f30f118388000000")
 def test_conditional_steering(self):self.assertEqual(M["pins"]["0305a05b"]["hex"],"0f8644010000")
 def test_world_transform(self):self.assertEqual(M["e8"]["03121f68"],"02f3d668")
 def test_goal_ref(self):self.assertEqual(M["pins"]["03121f5b"]["hex"],"488b4910")
 def test_goal_commit(self):self.assertEqual(M["pins"]["0311e6e8"]["hex"],"f20f118ff0010000")
 def test_tick_to_steer(self):self.assertEqual(M["e8"]["03087349"],"03059bc8")
 def test_line_cross_but_temporally_safe(self):
  first=s.crossing_fixtures()[0]
  self.assertAlmostEqual(s.closest_same_time(*first)[0],2)
  self.assertAlmostEqual(abs(s.transverse_crossings(*first)[0][0]-s.transverse_crossings(*first)[0][1]),.5)
 def test_line_cross_same_time(self):self.assertAlmostEqual(s.closest_same_time(*s.crossing_fixtures()[1])[0],0)
 def test_parallel_close_without_cross(self):
  pair=s.crossing_fixtures()[2]
  self.assertEqual(len(s.transverse_crossings(*pair)),0)
  self.assertAlmostEqual(s.closest_same_time(*pair)[0],.7)
 def test_direct180_collapse(self):self.assertAlmostEqual(s.closest_group(s.grid_tracks("straight180",20)),0)
 def test_rigid_turn_spacing(self):self.assertGreater(s.closest_group(s.grid_tracks("rigid",100)),2.999)
 def test_phase_lag_clearance(self):self.assertLess(s.closest_group(s.grid_tracks("lagged",100)),1.5)
 def test_90_plus_90(self):self.assertAlmostEqual(s.closest_group(s.grid_tracks("two90",100)),3/math.sqrt(2),places=5)
 def test_radius_narrow(self):self.assertLess(s.radius(2,3)[0],0)
 def test_radius_wide(self):self.assertGreater(s.radius(12,3)[0],0)
 def test_world_ref_rotation(self):self.assertEqual(s.world_xyz((2,0,0),((-1,0,0),(0,1,0),(0,0,-1)),(0,0,0)),(-2,0,0))
 def test_wrong_sha_refused(self):
  with self.assertRaisesRegex(a.Drift,"SHA_FAIL_CLOSED"):a.verify(b"MZ"+bytes(20),M)
 def test_actual_matching_exe_optional(self):
  p=os.environ.get("BSC_EXE")
  if not p:self.skipTest("Commercial matching WH3 EXE excluded from public CI")
  self.assertFalse(a.verify(Path(p).read_bytes(),M)["gameplay_patch_authorized"])
