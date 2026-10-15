"""B route node mode/flag gate; fixed original EXE optional in CI."""
import os,sys,unittest,tempfile,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_b_node_initialization_gates_20261015 as a
class NodeGate(unittest.TestCase):
 def test_guard_count(self):self.assertEqual((len(a.PINS),len(a.E8)),(17,5))
 def test_initial_forced_conversion(self):
  for mode in (0,1,2,3,5):self.assertTrue(a.convert_attempt(mode,1))
 def test_fallback_not_forced_conversion(self):
  for mode in (0,2,3,5):self.assertFalse(a.convert_attempt(mode,0))
  self.assertTrue(a.convert_attempt(1,0))
 def test_record_stack_alias(self):self.assertEqual(0x50+0x4c,0x9c)
 def test_wrong_sha_under_optimization(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.exe';p.write_bytes(b'MZ'+bytes(50))
   for flags in ([],['-O']):
    r=subprocess.run([sys.executable,*flags,str(ROOT/'audit_b_node_initialization_gates_20261015.py'),'--exe',str(p)],capture_output=True,text=True)
    self.assertNotEqual(r.returncode,0);self.assertIn('SHA_MISMATCH',r.stderr)
 def test_output_overwrite_guard(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.exe';p.write_bytes(b'keep')
   r=subprocess.run([sys.executable,str(ROOT/'audit_b_node_initialization_gates_20261015.py'),'--exe',str(p),'--out',str(p)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertIn('EXE_OVERWRITE_FORBIDDEN',r.stderr)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private game binary absent')
 def test_real_original_exe(self):
  r=a.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((r['pin_instruction_starts'],r['E8_guards']),(17,5))
  self.assertFalse(r['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
