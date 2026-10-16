"""Original WH3 pair-response data provenance; no gameplay patch."""
import os,sys,tempfile,subprocess,unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'/'audit_pair_response_context_20261016.py'
sys.path.insert(0,str(SRC.parent))
import audit_pair_response_context_20261016 as m

class PairResponseContext(unittest.TestCase):
 def test_inventory(self):self.assertEqual(len(m.pins()),31)
 def test_five_callers(self):
  self.assertEqual([x[2] for x in m.TRIPLES],
   [0x030557bc,0x0307b219,0x0307b3dd,0x0324f503,0x03260d11])
 def test_all_use_same_context_field_offsets(self):
  d=m.pins()
  for a,b,_ in m.TRIPLES:
   self.assertEqual(d[a],bytes.fromhex('488b9040040000'))
   self.assertEqual(d[b],bytes.fromhex('488b92f0000000'))
 def test_member_case_root_is_verified(self):
  self.assertEqual(m.pins()[0x03054c86].hex(),'4c8d6f58')
  self.assertEqual(m.pins()[0x03055771].hex(),'498b4500')
 def test_receiver_is_embedded_virtual(self):
  d=m.pins()
  self.assertEqual(d[0x030800f7].hex(),'4c8bea')
  self.assertEqual(d[0x0308024d].hex(),'498d8dd8010000')
  self.assertEqual(d[0x03080257].hex(),'ff5010')
 def test_response_is_pair_priority_record(self):
  self.assertEqual(m.pins()[0x030800e3].hex(),'418b7874')
  self.assertEqual(m.pins()[0x030800ea].hex(),'2b7974')
 def test_exe_overwrite_rejected(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'game.exe';p.write_bytes(b'untouched')
   t=subprocess.run([sys.executable,str(SRC),'--exe',str(p),'--out',str(p)],capture_output=True,text=True)
   self.assertNotEqual(t.returncode,0);self.assertIn('EXE_OVERWRITE_FORBIDDEN',t.stderr)
   self.assertEqual(p.read_bytes(),b'untouched')
 def test_wrong_sha_rejected_under_python_o(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'bad.exe';p.write_bytes(b'MZ'+bytes(100))
   for options in ([],['-O']):
    t=subprocess.run([sys.executable,*options,str(SRC),'--exe',str(p)],capture_output=True,text=True)
    self.assertNotEqual(t.returncode,0);self.assertIn('SHA_MISMATCH',t.stderr)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'original game EXE never shipped to CI')
 def test_true_original_game_exe(self):
  result=m.audit(os.environ['WH3_903_EXE'])
  self.assertEqual(result['guarded_instruction_starts'],31)
  self.assertEqual(result['verified_direct_calls'],5)
  self.assertFalse(result['virtual_concrete_implementation_known'])
  self.assertFalse(result['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
