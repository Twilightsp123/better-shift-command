"""Original command flags to successor group-heading gate: type-safe contracts."""
import os,sys,unittest,tempfile,subprocess
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'/'audit_move_slot_bit2_provenance.py'
sys.path.insert(0,str(SRC.parent))
import audit_move_slot_bit2_provenance as m
class NativeSlotFlagBit2(unittest.TestCase):
 def test_manifest_inventory(self):
  self.assertEqual([len(m.PIN),len(m.E8),len(m.JCC)],[19,2,3])
 def test_typed_source_to_slot_constructor(self):
  self.assertEqual(m.PIN[0x030323FF],'498bf8')
  self.assertEqual(m.PIN[0x030326DB],'4c8bcf')
  self.assertEqual(m.PIN[0x030090C6],'498bd9')
  self.assertEqual(m.PIN[0x030090DB],'488d4f40')
  self.assertEqual(m.PIN[0x030090DF],'488bd3')
  self.assertEqual(m.E8[0x030326E4],0x030090BC)
  self.assertEqual(m.E8[0x030090E2],0x03009100)
 def test_bit_copy_symbolic_all_128_by_128(self):
  for src in range(128):
   for dst in range(128):
    self.assertEqual(m.copy_low_seven(dst,src)&0x7f,src)
 def test_bit7_is_unaffected_by_copy(self):
  self.assertEqual(m.copy_low_seven(0x80,0),0x80)
  self.assertEqual(m.copy_low_seven(0x80,7),0x87)
 def test_geometry_normalization_always_sets_bit2(self):
  for old in range(256):
   self.assertFalse(m.samples_group_when_activated(True,old))
 def test_unnormalized_descriptor_retains_distinguishing_bit2(self):
  self.assertTrue(m.samples_group_when_activated(False,0))
  self.assertTrue(m.samples_group_when_activated(False,0x04))
  self.assertFalse(m.samples_group_when_activated(False,0x02))
 def test_two_bypass_branch_targets(self):
  self.assertEqual(m.JCC[0x0303249E],0x030326A2)
  self.assertEqual(m.JCC[0x03032577],0x030326A2)
  self.assertEqual(m.JCC[0x03025E69],0x03025F79)
 def test_wrong_sha_fails_even_in_optimized_mode(self):
  with tempfile.TemporaryDirectory() as td:
   fake=Path(td)/'wrong.exe';fake.write_bytes(b'MZ'+bytes(100))
   for opts in ([],['-O']):
    result=subprocess.run([sys.executable,*opts,str(SRC),'--exe',str(fake)],capture_output=True,text=True)
    self.assertNotEqual(result.returncode,0)
    self.assertIn('SHA_MISMATCH',result.stderr)
 def test_exe_cannot_be_output_target(self):
  with tempfile.TemporaryDirectory() as td:
   fake=Path(td)/'wrong.exe';fake.write_bytes(b'unchanged')
   result=subprocess.run([sys.executable,str(SRC),'--exe',str(fake),'--out',str(fake)],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0)
   self.assertIn('EXE_OVERWRITE_FORBIDDEN',result.stderr)
   self.assertEqual(fake.read_bytes(),b'unchanged')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original EXE must not be uploaded to CI')
 def test_private_original_exe(self):
  result=m.audit(os.getenv('WH3_903_EXE'))
  self.assertEqual([result['original_instruction_starts'],result['E8_targets'],result['JCC_targets']],[19,2,3])
  self.assertFalse(result['native_gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
