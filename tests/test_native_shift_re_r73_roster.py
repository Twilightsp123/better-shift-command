"""R73 public synthetic tests. Private original EXE absent in GitHub Actions."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_r73_roster as r
M=json.loads((ROOT/'r73_roster_pins.json').read_text())
class Tests(unittest.TestCase):
 def test_pins(self):self.assertEqual(len(M['pins']),40)
 def test_calls(self):self.assertEqual(len(M['e8_edges']),7)
 def test_stored_root(self):self.assertEqual(M['pins']['02f31791'],'48895108')
 def test_current_group(self):self.assertEqual(M['pins']['02f54621'],'488b89f8320000')
 def test_b2_dispatch(self):self.assertEqual(M['e8_edges']['0327edd5'],'03268d34')
 def test_direct_sender(self):self.assertEqual(M['e8_edges']['032769f2'],'0326a994')
 def test_fallback_sender(self):self.assertEqual(M['e8_edges']['03286445'],'0326a994')
 def test_group_argument(self):self.assertEqual(M['pins']['0326a9c4'],'488bf2')
 def test_array_reread(self):self.assertEqual(M['pins']['0326aa44'],'488b4628')
 def test_count_reread(self):self.assertEqual(M['pins']['0326abbd'],'443b6624')
 def test_member_dispatch(self):self.assertEqual(M['pins']['0326abaf'],'ff9068030000')
 def test_static_roster(self):self.assertEqual(r.simulate([([11,22],2)]*2),[11,22])
 def test_synthetic_mutation_possible(self):
  self.assertEqual(r.simulate([([11,22],2),([11,99],2)]),[11,99])
 def test_mutation_reject(self):
  with self.assertRaisesRegex(ValueError,'CROSS_GENERATION'):
   r.simulate([([11,22],2),([11,99],2)],epochs=[1,2],fail_closed=True)
 def test_no_shift_claim(self):self.assertFalse(M['shift_instance_proven'])
 def test_wrong_exe(self):
  with self.assertRaisesRegex(r.EvidenceError,'EXE_SHA_SIZE'):
   r.verify(b'MZ'+bytes(100),M)
 def test_private_exe(self):
  if not os.getenv('BSC_EXE'):self.skipTest('Licensed WH3 EXE absent from public CI')
  result=r.verify(Path(os.environ['BSC_EXE']).read_bytes(),M)
  self.assertFalse(result['game_hook_authorized'])
