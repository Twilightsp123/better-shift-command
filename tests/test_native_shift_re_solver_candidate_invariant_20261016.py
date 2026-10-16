"""CI-safe native solver candidate-return contract and optional original EXE."""
import os,sys,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_solver_candidate_invariant_20261016 as m

class SolverCandidateInvariant(unittest.TestCase):
 def test_inventory(self):
  self.assertEqual((len(m.guards()),len(m.E8),len(m.JUMPS)),(35,2,6))
 def test_return2_requires_nonzero_count(self):
  self.assertEqual(m.solver_classification(2),'nonzero_count_required')
 def test_return2_concurrent_writer_not_ruled_out(self):
  self.assertEqual(m.solver_classification(2,concurrent_writer=True),'unknown_race')
 def test_return1_has_unresolved_virtual_side_effect(self):
  self.assertEqual(m.solver_classification(1),'earlier_nonzero_count_but_virtual_can_mutate')
 def test_failure_is_not_this_candidate_path(self):
  self.assertEqual(m.solver_classification(0),'alternate_or_failure_path')
 def test_result2_and_container_guards(self):
  g=m.guards()
  self.assertEqual(g[0x031267bf].hex(),'41837e0400')
  self.assertEqual(g[0x0312681a].hex(),'b802000000')
  self.assertEqual(g[0x031267f9].hex(),'41ff5018')
 def test_real_native_jcc_targets(self):
  g=m.guards()
  for site,target in m.JUMPS.items():self.assertEqual(m.branch(site,g[site]),target)
 def test_sixth_argument_alias(self):
  self.assertEqual(-0x4d8+0x508,0x30)
  self.assertEqual(-8+0x30,0x28)
 def test_wrong_build_fail_closed_even_python_optimized(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'wrong.exe';p.write_bytes(b'MZ'+bytes(100))
   for opt in ([],['-O']):
    out=subprocess.run([sys.executable,*opt,str(ROOT/'audit_solver_candidate_invariant_20261016.py'),'--exe',str(p)],capture_output=True,text=True)
    self.assertNotEqual(out.returncode,0)
    self.assertIn('SHA_MISMATCH',out.stderr)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original EXE never uploaded to GitHub')
 def test_private_original(self):
  r=m.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((r['decoded_guarded_sites'],r['E8_edges'],r['JCC_edges']),(35,2,6))
  self.assertFalse(r['result1_following_count_zero_proven_impossible'])
  self.assertFalse(r['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
