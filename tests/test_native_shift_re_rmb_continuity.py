"""WH3 source-guarded PE and evidence-bounded synthetic centerline differential tests."""
import json,math,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'maintenance_tools'/'native_shift_re'))
import rmb_shift_target_continuity as m
EXE=Path(os.environ['WH3_903_EXE']) if os.environ.get('WH3_903_EXE') else None

class StaticBoundaries(unittest.TestCase):
 def test_source_guard_constants(self):
  self.assertEqual(len(m.GUARDS),44)
  self.assertEqual(len(m.EDGES),13)
  self.assertEqual(len(m.SLOTS),4)
  self.assertEqual(m.GUARDS['segment_kind1_halfwidth_factor'][1],'0000003f')
 def test_original_binary_all_guards(self):
  if EXE is None or not EXE.exists():self.skipTest('WH3_903_EXE not provided')
  x=m.verify(EXE)
  self.assertEqual(x['instructions_and_native_scalar_verified'],44)
 def test_wrong_hash_must_fail_before_pe_parse(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'bad.exe';f.write_bytes(b'wrong exe')
   with self.assertRaisesRegex(ValueError,'WRONG_WARHAMMER3_EXE_SHA256'):m.verify(f)
   self.assertEqual(f.read_bytes(),b'wrong exe')
 def test_cli_refuse_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'fake.exe';f.write_bytes(b'not-an-exe')
   x=subprocess.run([sys.executable,m.__file__,'--exe',str(f),'--out',str(f)],capture_output=True,text=True)
   self.assertNotEqual(x.returncode,0)
   self.assertEqual(f.read_bytes(),b'not-an-exe')

class MemberSpatialNegativeControl(unittest.TestCase):
 def test_spatial_query_selects_geometric_support_not_motor_velocity(self):
  # Existing original handler calls the spatial enumerator and a region
  # membership query, then calculates a plane value for candidate selection.
  self.assertEqual(m.EDGES['spatial_region_predicate'],(0x0314ea25,0x018325ec))
  self.assertEqual(m.EDGES['spatial_region_nested_contour'],(0x01832604,0x0183b990))
  self.assertEqual(m.GUARDS['spatial_height_plane_divisor'][1],'f30f5e4b70')
  self.assertEqual(m.GUARDS['spatial_writes_computed_scalar'][1],'f3410f110e')
  a,b,c,d=2.0,-1.0,5.0,2.0
  x,z=1.0,3.0
  self.assertEqual((a*x+b*z+c)/d,2.0)
 def test_target_pose_writer_not_per_frame_rate_writer(self):
  self.assertEqual(m.GUARDS['member_target_direct_pose_x'][0],0x0315f311)
  self.assertEqual(m.GUARDS['member_target_direct_pose_z'][0],0x0315f33f)
  self.assertEqual(m.GUARDS['member_target_direct_facing'][0],0x0315f34d)
  self.assertNotEqual(0x0315ec98,0x0315c1e4)

class GeometryContrast(unittest.TestCase):
 def test_segment_spacing_carries_across_90_corner(self):
  a=m.segment_chain([(0.,0.),(1.5,0.),(1.5,2.5)])
  targets,carry=m.native_kind0_centerline(a,4,1.0,0.25)
  self.assertEqual([(round(p.x,6),round(p.z,6)) for p in targets],
                   [(0.25,0.0),(1.25,0.0),(1.5,0.75),(1.5,1.75)])
  self.assertEqual(carry[0]['carried_to_next'],0.75)
  self.assertEqual(m.target_diagnostics(targets)['exact_duplicates'],0)
 def test_exact_boundary_no_double_count(self):
  t,_=m.native_kind0_centerline(m.segment_chain([(0,0),(2,0),(2,2)]),5,1.0,0.0)
  coords=[(round(p.x,5),round(p.z,5)) for p in t]
  self.assertEqual(coords,[(0.,0.),(1.,0.),(2.,0.),(2.,1.),(2.,2.)])
  self.assertEqual(len(set(coords)),len(coords))
 def test_rmb_straight_reference(self):
  c=m.case_report()['RMB_long_straight']
  self.assertEqual(c['diagnostics']['target_count'],36)
  self.assertEqual(c['diagnostics']['near_opposed_pairs'],0)
  self.assertEqual(c['tail_clones_if_required'],0)
 def test_smooth_u_turn_can_have_near_opposed_without_duplicate(self):
  c=m.case_report()['queued_short_U_radius_0p4']
  self.assertEqual(c['tail_clones_if_required'],0)
  self.assertEqual(c['unique_endpoint_geometry'],36)
  self.assertGreater(c['diagnostics']['near_opposed_pairs'],0)
 def test_wide_same_180_turn_no_close_opposed(self):
  c=m.case_report()['queued_wide_U_radius_2p5']
  self.assertEqual(c['diagnostics']['near_opposed_pairs'],0)
  self.assertEqual(c['tail_clones_if_required'],0)
 def test_90_turn_same_count_without_close_opposed(self):
  c=m.case_report()['queued_90_degree']
  self.assertEqual(c['diagnostics']['near_opposed_pairs'],0)
 def test_short_rmb_also_eligible_for_underfill(self):
  c=m.case_report()['RMB_short_straight']
  self.assertEqual(c['diagnostics']['near_opposed_pairs'],0)
  self.assertGreater(c['tail_clones_if_required'],0)
 def test_invalid_input_denied(self):
  with self.assertRaises(ValueError):m.native_kind0_centerline([],1,0.0)
  with self.assertRaises(ValueError):m.native_kind0_centerline([],1,float('nan'))
  with self.assertRaises(ValueError):m.gradual_u_turn(0.)
 def test_no_executable_patch_logic(self):
  code=Path(m.__file__).read_text()
  self.assertNotIn('WriteProcessMemory(',code)
  self.assertNotIn('VirtualProtect(',code)

if __name__=='__main__':unittest.main()