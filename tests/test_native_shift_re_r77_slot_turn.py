"""R77 original-index and emergent crowding negative controls. CI has no game EXE."""
import json,math,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"maintenance_tools"/"native_shift_re"
sys.path.insert(0,str(ROOT))
import r77_geometry as g
import audit_r77_slot as s
M=json.loads((ROOT/"r77_slot_pins.json").read_text())
class R77(unittest.TestCase):
 def setUp(self):self.p=g.grid()
 def test_original_sha(self):self.assertEqual(len(M["sha256"]),64)
 def test_code_pins(self):self.assertEqual(len(M["pins"]),66)
 def test_e8_calls(self):self.assertEqual(len(M["e8"]),9)
 def test_unwind_names(self):self.assertEqual(len(M["function_ranges"]),3)
 def test_strategy_virtual(self):self.assertEqual(M["pins"]["030da556"]["hex"],"41ff5248")
 def test_record_48_stride(self):
  self.assertEqual(M["pins"]["030da565"]["hex"],"4c8d0476")
  self.assertEqual(M["pins"]["030da569"]["hex"],"49c1e004")
 def test_record_index(self):self.assertEqual(M["pins"]["030da572"]["hex"],"4c03442440")
 def test_member_index(self):self.assertEqual(M["pins"]["030da57c"]["hex"],"488b1cf0")
 def test_member_packet(self):self.assertEqual(M["pins"]["030da59b"]["hex"],"ff9068030000")
 def test_conditional_A(self):
  self.assertEqual(M["e8"]["0327ed17"],"030da5d8")
  self.assertEqual(M["e8"]["0327ed3c"],"03268920")
 def test_A_fanout(self):self.assertEqual(M["e8"]["030da68f"],"030da51c")
 def test_initial_distance(self):self.assertAlmostEqual(g.gap(self.p),3.)
 def test_flat_180_collapses(self):self.assertLess(g.gap(g.lerp(self.p,[g.rot(x,180) for x in self.p],.5)),1e-12)
 def test_linear_90_shrinks_not_zero(self):
  self.assertAlmostEqual(g.gap(g.lerp(self.p,[g.rot(x,90) for x in self.p],.5)),3/math.sqrt(2))
 def test_staged_90_plus_90(self):self.assertAlmostEqual(g.gap(g.staged(self.p,.25)),3/math.sqrt(2))
 def test_staged_endpoint(self):
  for x,y in zip(g.staged(self.p,1),[g.rot(p,180) for p in self.p]):
   self.assertLess(math.dist(x,y),1e-12)
 def test_smooth_rigid_does_not_crowd(self):
  for i in range(101):self.assertAlmostEqual(g.gap(g.rigid(self.p,180,i/100)),3.)
 def test_member_lag_can_reduce_clearance(self):
  self.assertLess(min(g.gap(g.phase_lag(self.p,i/100)) for i in range(101)),2.)
 def test_zero_lag_rigid(self):self.assertAlmostEqual(g.gap(g.rigid(self.p,180,.5)),3.)
 def test_tight_radius(self):self.assertLess(g.curvature(2,3)["inner"],0)
 def test_wide_radius(self):self.assertGreater(g.curvature(12,3)["inner"],0)
 def test_exact_threshold(self):self.assertEqual(g.curvature(3,3)["inner"],0)
 def test_bad_radius(self):
  with self.assertRaises(ValueError):g.curvature(0,3)
 def test_bad_nan(self):
  with self.assertRaises(ValueError):g.curvature(float("nan"),3)
 def test_no_gameproof(self):self.assertFalse(g.evaluate()["cause_proven"])
 def test_no_naive_slot_permutation(self):
  end={tuple(round(a,6) for a in g.rot(p,180)) for p in self.p}
  start={tuple(round(a,6) for a in p) for p in self.p}
  self.assertEqual(end,start) # minimum-distance remapping can make a turn stand still
 def test_wrong_exe_rejected(self):
  with self.assertRaisesRegex(s.Drift,"EXACT_SHA"):s.verify(__file__,M)
 def test_matching_exe_optional(self):
  f=os.getenv("BSC_EXE")
  if not f:self.skipTest("Licensed matching EXE not in GitHub CI")
  self.assertEqual(s.verify(f,M)["opcode_sites"],66)
 def test_matching_real_disassembly_optional(self):
  f=os.getenv("BSC_EXE")
  if not f:self.skipTest("Licensed matching EXE not in GitHub CI")
  self.assertEqual(s.verify(f,M,check_disassembly=True)["e8"],9)
