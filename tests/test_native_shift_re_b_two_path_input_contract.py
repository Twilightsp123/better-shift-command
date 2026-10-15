"""Typed ordinary-B sender record contrast and original-EXE guards."""
import os,sys,unittest,tempfile,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(HERE))
import audit_b_two_path_input_contract_20261015 as a
class BTwoPathInputs(unittest.TestCase):
 def test_inventory(self):self.assertEqual((len(a.pins()),len(a.E8),len(a.VTABLE)),(82,7,2))
 def test_same_packet_builder_and_allocator(self):
  self.assertEqual(a.E8[0x03271b8e],a.E8[0x032815c5])
  self.assertEqual(a.E8[0x03271b71],a.E8[0x032815a7])
 def test_distinct_vtable_slots(self):
  self.assertEqual(a.VTABLE[(0x03ae00e8,0x08)],0x03271b0c)
  self.assertEqual(a.VTABLE[(0x03ae00e8,0x10)],0x03281520)
 def test_fast_and_deferred_same_initialized_fields_if_inputs_equal(self):
  fast=a.parameter_fields(10,1.0,[0,1,2,3,4,5],11)
  later=a.parameter_fields(10,1.0,[0,1,2,3,4,5],11)
  self.assertEqual(fast,later)
  self.assertEqual(sorted(fast),[0,8,12,13,14,15,16,20,24,28])
 def test_route_is_only_difference_if_other_values_same(self):
  f=a.parameter_fields(100,1.,[0,1,2,3,4,5],11)
  s=a.parameter_fields(200,1.,[0,1,2,3,4,5],11)
  self.assertEqual([o for o in f if f[o]!=s[o]],[0])
 def test_time_dependent_scale_flags_can_change(self):
  f=a.parameter_fields(10,1.,[0,1,2,3,4,5],11)
  s=a.parameter_fields(10,2.,[9,1,2,3,4,5],11)
  self.assertEqual([o for o in f if f[o]!=s[o]],[8,12])
 def test_uninitialized_padding_not_proven(self):
  self.assertNotIn(17,a.parameter_fields(10,1.,[0]*6,0))
  self.assertNotIn(29,a.parameter_fields(10,1.,[0]*6,0))
 def test_six_flags_required_even_python_optimized(self):
  with self.assertRaises(ValueError):a.parameter_fields(10,1.,[0]*5,0)
 def test_wrong_hash_fail_closed_normal_and_opt(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'wrong.exe';p.write_bytes(b'MZ'+bytes(100))
   for opts in ([],['-O']):
    proc=subprocess.run([sys.executable,*opts,str(HERE/'audit_b_two_path_input_contract_20261015.py'),'--exe',str(p)],capture_output=True,text=True)
    self.assertNotEqual(proc.returncode,0);self.assertIn('SHA_MISMATCH',proc.stderr)
 def test_output_must_not_override_exe(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'wrong.exe';p.write_bytes(b'keep')
   proc=subprocess.run([sys.executable,str(HERE/'audit_b_two_path_input_contract_20261015.py'),'--exe',str(p),'--out',str(p)],capture_output=True,text=True)
   self.assertNotEqual(proc.returncode,0);self.assertIn('EXE_OVERWRITE_FORBIDDEN',proc.stderr)
   self.assertEqual(p.read_bytes(),b'keep')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original EXE not in GitHub CI')
 def test_original_exe(self):
  d=a.audit(os.getenv('WH3_903_EXE'))
  self.assertEqual((d['decoded_instructions'],d['direct_e8'],d['vtable_slots']),(82,7,2))
  self.assertFalse(d['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
