"""Native member-neighbor screening and pair-response regression."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_member_neighbor_response_20261016 as m
class PairwiseMovementResponse(unittest.TestCase):
 def test_exact_inventory(self):self.assertEqual((len(m.pins()),len(m.E8),len(m.JCC)),(122,18,8))
 def test_member_tick_calls_candidate_screen(self):
  self.assertEqual(m.E8[0x030822F9],0x03054B84)
  self.assertEqual(m.E8[0x03054DB3],0x03062988)
 def test_collector_branches_both_feed_type_filter(self):
  self.assertEqual(m.E8[0x03062A90],m.E8[0x03062AFF])
  self.assertEqual(m.E8[0x03062850],m.E8[0x03054DF7])
 def test_same_affiliation_mask(self):
  self.assertTrue(m.affiliation_gate(True,True,3,1))
  self.assertFalse(m.affiliation_gate(True,True,2,2))
 def test_other_affiliation_mask(self):
  self.assertTrue(m.affiliation_gate(True,False,3,2))
  self.assertFalse(m.affiliation_gate(True,False,1,1))
 def test_affiliation_filter_optional(self):
  self.assertTrue(m.affiliation_gate(False,False,0,0))
 def test_neighbour_selection_persists_candidate(self):
  self.assertEqual(m.pins()[0x03054F26].hex(),'488bf3')
  self.assertEqual(m.pins()[0x03054E17].hex(),'48398b80000000')
 def test_self_and_neighbour_positions_are_both_loaded(self):
  p=m.pins()
  self.assertEqual(p[0x03054E93].hex(),'f30f5c8b900000')
  self.assertEqual(p[0x03054E9B].hex(),'f30f1097880000')
 def test_group_filter_applies_different_rules_even_if_goal_same(self):
  a=m.affiliation_gate(True,True,1,1)
  b=m.affiliation_gate(True,False,1,1)
  self.assertNotEqual(a,b)
 def test_pair_response_dispatch_not_assumed_velocity_write(self):
  self.assertEqual(m.E8[0x030557BC],0x030800C4)
  self.assertEqual(m.pins()[0x03080257].hex(),'ff5010')
  self.assertEqual(m.RESPONSES[0x03055647],0x0324EB24)
  self.assertEqual(m.RESPONSES[0x030556A1],0x0324EE00)
 def test_original_jcc_edges(self):
  p=m.pins()
  for site,dest in m.JCC.items():self.assertEqual(m.jump_target(site,p[site]),dest)
 def test_wrong_sha_under_python_o(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'wrong.exe';f.write_bytes(b'MZ'+bytes(99))
   for flags in ([],['-O']):
    r=subprocess.run([sys.executable,*flags,str(m.__file__),'--exe',str(f)],capture_output=True,text=True)
    self.assertNotEqual(r.returncode,0)
    self.assertIn('SHA_MISMATCH',r.stderr)
 def test_no_exe_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'game.exe';f.write_bytes(b'keep')
   r=subprocess.run([sys.executable,str(m.__file__),'--exe',str(f),'--out',str(f)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
   self.assertIn('EXE_OVERWRITE_FORBIDDEN',r.stderr)
   self.assertEqual(f.read_bytes(),b'keep')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original WH3 EXE never uploaded to GitHub')
 def test_true_original_exe(self):
  d=m.audit(os.getenv('WH3_903_EXE'))
  self.assertEqual((d['verified_instruction_starts'],d['verified_e8'],d['verified_jcc']),(122,18,8))
  self.assertFalse(d['pair_response_virtual_target_typed_proven'])
  self.assertFalse(d['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
