"""RMB/queued-MOVE conditional branch contracts plus private exact-EXE test."""
import os,sys,tempfile,subprocess,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SRC=HERE/'audit_rmb_shift_lifecycle.py'
if not SRC.exists():SRC=HERE.parent/'maintenance_tools'/'native_shift_re'/'audit_rmb_shift_lifecycle.py'
sys.path.insert(0,str(SRC.parent))
import audit_rmb_shift_lifecycle as m

class ShiftDiffLifecycle(unittest.TestCase):
 def test_exact_inventory(self):
  pins=m.manifests()
  self.assertEqual([len(pins['queue']),len(pins['state'])],[72,69])
  self.assertEqual([len(m.CALLS),len(m.BRANCHES),len(m.MOVEVT)],[8,6,4])
 def test_move_implicit_append_not_keyboard_equivalence(self):
  p=m.manifests()['queue']
  self.assertEqual(p[0x030444B8].hex(),'458ac8')
  self.assertEqual(p[0x03044528].hex(),'458ac8')
  self.assertEqual(p[0x030326BB].hex(),'418ad6')
 def test_generator_is_shared_and_reuses_typed_task(self):
  p=m.manifests()
  self.assertEqual(p['queue'][0x0311E772].hex(),'e895000000')
  self.assertEqual(p['state'][0x0311E636].hex(),'e8d1010000')
  self.assertEqual(p['state'][0x0311E84F].hex(),'488bf2')
 def test_state_graph_symbolic_counterexamples(self):
  self.assertEqual(m.branch_history(False,True,True),[1,4])
  self.assertEqual(m.branch_history(True,False,True),[1,2])
  self.assertEqual(m.branch_history(True,True,False),[1,2,3])
  self.assertEqual(m.branch_history(True,True,True),[1,2,3,4])
  self.assertTrue(m.shorttask_b_gate(4,0,3))
  for state,flag,stage in ((4,0,1),(4,0,2),(4,1,3),(3,0,3)):
   self.assertFalse(m.shorttask_b_gate(state,flag,stage))
 def test_true_conditional_jump_byte_targets(self):
  p=m.manifests()['state']
  for site,target in m.BRANCHES.items():
   self.assertEqual(m.branch_target(site,p[site]),target)
 def test_wrong_sha_is_rejected_even_optimized(self):
  with tempfile.TemporaryDirectory() as temp:
   inp=Path(temp)/'wrong.exe';inp.write_bytes(b'MZ'+bytes(100))
   for modes in ([],['-O']):
    result=subprocess.run([sys.executable,*modes,str(SRC),'--exe',str(inp)],capture_output=True,text=True)
    self.assertNotEqual(result.returncode,0)
    self.assertIn('SHA_MISMATCH',result.stderr)
 def test_exe_cannot_be_overwritten(self):
  with tempfile.TemporaryDirectory() as temp:
   inp=Path(temp)/'game.exe';inp.write_bytes(b'unchanged')
   result=subprocess.run([sys.executable,str(SRC),'--exe',str(inp),'--out',str(inp)],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0)
   self.assertIn('EXE_OVERWRITE_FORBIDDEN',result.stderr)
   self.assertEqual(inp.read_bytes(),b'unchanged')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original EXE not distributed via GitHub')
 def test_real_exe(self):
  d=m.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual([d['queue_instruction_starts'],d['state_instruction_starts'],d['native_move_direct_calls']],[72,69,64])
  self.assertFalse(d['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
