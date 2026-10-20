import unittest, math, pathlib, tempfile, sys, os
# Support both standalone ZIP and checked-out repository test layouts.
for module_dir in (pathlib.Path(__file__).resolve().parent,
                   pathlib.Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'):
    if (module_dir/'audit_r56_heading_projection_init.py').is_file():
        sys.path.insert(0,str(module_dir));break
from audit_r56_heading_projection_init import pins, projected_point, projected_jump, audit, CALLS
class R56(unittest.TestCase):
 def test_pins(self):self.assertEqual(len(pins()),47)
 def test_lookup_init_and_use_both_guarded(self):
  p=pins();self.assertIn(0x604304,p);self.assertIn(0x3102be6,p)
 def test_range_init(self):self.assertEqual(pins()[0x604366],bytes.fromhex('81ff00000100'))
 def test_lut_zero_branch(self):
  self.assertEqual(pins()[0x112093f],bytes.fromhex('0f14c1'))
  self.assertEqual(pins()[0x1120942],b'\xc3')
 def test_heading_transfer(self):
  self.assertEqual(pins()[0x3017a69],bytes.fromhex('440fb7cb'))
 def test_single_route_config_commit(self):self.assertEqual(pins()[0x3017abb],bytes.fromhex('48898770020000'))
 def test_math_translation(self):self.assertEqual(projected_point(4.,9.,10.,0.),(4.,4.))
 def test_old_binding_conditional_release(self):
  p=pins()
  self.assertEqual(p[0x301e890],bytes.fromhex('80b98000000000'))
  self.assertEqual(p[0x301e8a2],bytes.fromhex('ff4804'))
  self.assertEqual(p[0x301e8a5],bytes.fromhex('c6818000000000'))
 def test_old_binding_is_distinct_from_published_root(self):
  self.assertEqual(pins()[0x3017aa8],bytes.fromhex('889180000000'))
  self.assertEqual(pins()[0x3017abb],bytes.fromhex('48898770020000'))
 def test_zero_extent(self):self.assertEqual(projected_jump(0,0,math.pi),0)
 def test_same_heading(self):self.assertAlmostEqual(projected_jump(8,1.,1.),0)
 def test_ninety_delta(self):self.assertAlmostEqual(projected_jump(16,0,math.pi/2),16/math.sqrt(2),places=10)
 def test_one_eighty(self):self.assertAlmostEqual(projected_jump(16,0,math.pi),16.,places=10)
 def test_wraparound(self):
  self.assertAlmostEqual(projected_jump(9.,0.,2*math.pi),0.,places=10)
 def test_nonfinite_refusal(self):
  with self.assertRaises(ValueError):projected_point(1.,2.,float('nan'),3.)
 def test_fail_closed_wrong_exe(self):
  with tempfile.TemporaryDirectory() as td:
   f=pathlib.Path(td)/'bad.exe';f.write_bytes(b'MZ'+b'\0'*100)
   with self.assertRaisesRegex(ValueError,'EXE_SHA_DRIFT'):audit(f)
 def test_private_real_exe(self):
  private_path=os.environ.get('WH3_R56_EXE')
  if not private_path:self.skipTest('private exe not provided')
  exe=pathlib.Path(private_path)
  if not exe.is_file():self.skipTest('private exe path missing')
  d=audit(exe)
  self.assertEqual(d['verified_pins'],47)
  self.assertEqual(d['verified_direct_e8'],6)
  self.assertEqual(d['iterations'],65536)
  self.assertFalse(d['root_cause_proven'])
if __name__=='__main__':unittest.main(verbosity=2)
