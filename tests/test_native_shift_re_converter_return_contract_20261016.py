"""BSC N1 route converter bounded NULL-return contracts; original EXE optional."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
DIR=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(DIR))
import audit_converter_return_contract_20261016 as m

class RouteConverterReturn(unittest.TestCase):
 def test_inventory(self):
  self.assertEqual((len(m.pins()),len(m.CALLS),len(m.BRANCHES)),(76,10,9))
 def test_empty_candidate_conditional(self):
  self.assertEqual(m.synthetic_conditional(solver_nonzero=True,candidates=0,allocator_ok=True),'skips_route_allocation_returns_zero')
 def test_nonempty_candidate_does_not_guarantee_return(self):
  self.assertEqual(m.synthetic_conditional(solver_nonzero=True,candidates=2,allocator_ok=True),'route_build_attempt_result_unknown')
 def test_failed_allocation_path(self):
  self.assertEqual(m.synthetic_conditional(solver_nonzero=True,candidates=3,allocator_ok=False),'allocator_failure_returns_zero')
 def test_other_solver_branch_is_not_same_path(self):
  self.assertEqual(m.synthetic_conditional(solver_nonzero=False,candidates=0,allocator_ok=True),'alternate_constructor_branch')
 def test_branch_targets_guarded(self):
  p=m.pins()
  for at,dest in m.BRANCHES.items():self.assertEqual(m.branch(at,p[at]),dest)
  self.assertEqual(m.CALLS[0x03129092],0x030fda9c)
  self.assertEqual(p[0x030fe0b8].hex(),'488bc3')
 def test_manager_handles_before_checking_route(self):
  p=m.pins()
  self.assertEqual(p[0x03129097].hex(),'48894770')
  self.assertEqual(p[0x0312909e].hex(),'44886f08')
 def test_wrong_original_sha_fails_even_optimized(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'bad.exe';p.write_bytes(b'MZ'+bytes(100))
   for flags in ([],['-O']):
    result=subprocess.run([sys.executable,*flags,str(DIR/'audit_converter_return_contract_20261016.py'),'--exe',str(p)],capture_output=True,text=True)
    self.assertNotEqual(result.returncode,0)
    self.assertIn('SHA_MISMATCH',result.stderr)
 def test_original_exe_not_overwritten(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'game.exe';p.write_bytes(b'untouched')
   result=subprocess.run([sys.executable,str(DIR/'audit_converter_return_contract_20261016.py'),'--exe',str(p),'--out',str(p)],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0)
   self.assertIn('EXE_OVERWRITE_FORBIDDEN',result.stderr)
   self.assertEqual(p.read_bytes(),b'untouched')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private game EXE excluded from GitHub')
 def test_private_original_exe(self):
  r=m.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((r['instruction_starts'],r['E8_edges'],r['JCC_JMP_edges']),(76,10,9))
  self.assertFalse(r['same_SHIFT_instance_observed'])
  self.assertFalse(r['native_patch_authorized'])

if __name__=='__main__':unittest.main()
