"""R75 public CI only tests declarations/synthetic scheduling; real EXE optional."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_r75_scheduler_census as r
M=json.loads((ROOT/'r75_scheduler_caller_manifest.json').read_text())
def event(op,task,g=1,t=1):return {'op':op,'task':task,'generation':g,'thread':t}
class R75(unittest.TestCase):
 def test_counts(self):self.assertEqual(sum(len(x) for x in M['direct_e8_census'].values()),17)
 def test_build_caller_count(self):self.assertEqual(len(M['direct_e8_census']['030209ec']),4)
 def test_sender_caller_count(self):self.assertEqual(len(M['direct_e8_census']['0326a994']),4)
 def test_setup_caller_count(self):self.assertEqual(len(M['direct_e8_census']['03032c48']),9)
 def test_known_b2_not_all_sender(self):self.assertEqual(len(M['known_B2_owners']),2)
 def test_sender_other_owner(self):self.assertNotIn('032802b0',M['known_B2_owners'])
 def test_stable_order(self):
  x=r.fixture([event('begin_sender','s'),event('end_sender','s'),event('begin_rebuild','r'),event('end_rebuild','r')])
  self.assertEqual(x['interval_overlap'],0)
 def test_fixture_overlap_is_not_wh3(self):
  x=r.fixture([event('begin_sender','s'),event('begin_rebuild','r',t=2),event('end_rebuild','r',t=2),event('end_sender','s')])
  self.assertEqual(x['interval_overlap'],1);self.assertFalse(x['real_game_thread_overlap_proven'])
 def test_mismatched_generation_not_overlap(self):
  x=r.fixture([event('begin_sender','s',g=2),event('begin_rebuild','r',g=3,t=2),event('end_rebuild','r',g=3,t=2),event('end_sender','s',g=2)])
  self.assertEqual(x['interval_overlap'],0)
 def test_same_thread_nesting_is_not_proof(self):
  x=r.fixture([event('begin_sender','s'),event('begin_rebuild','r'),event('end_rebuild','r'),event('end_sender','s')])
  self.assertEqual(x['interval_overlap'],1);self.assertFalse(x['real_game_thread_overlap_proven'])
 def test_unbalanced_rejected(self):
  with self.assertRaisesRegex(r.Closed,'UNBALANCED'):r.fixture([event('begin_sender','s')])
 def test_cross_thread_end_rejected(self):
  with self.assertRaisesRegex(r.Closed,'LIFETIME'):r.fixture([event('begin_sender','s'),event('end_sender','s',t=2)])
 def test_extraneous_pointer_rejected(self):
  e=event('begin_sender','s');e['raw_ptr']=123
  with self.assertRaisesRegex(r.Closed,'SCHEMA'):r.fixture([e])
 def test_wrong_sha(self):
  with self.assertRaisesRegex(r.Closed,'SHA'):r.verify(__file__,M)
 def test_game_patch_unauthorized(self):self.assertFalse(M['native_patch_authorized'])
 def test_real_exe_if_available(self):
  exe=os.getenv('BSC_EXE')
  if not exe:self.skipTest('Original commercial game EXE is excluded from public CI')
  result=r.verify(exe,M)
  self.assertEqual(result['direct_e8_sites'],17)
  self.assertFalse(result['native_patch_authorized'])
