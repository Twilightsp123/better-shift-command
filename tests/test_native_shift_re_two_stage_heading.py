"""CI-safe symbolic contrast and opt-in original SHA-locked EXE regression."""
import os,sys,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'maintenance_tools'/'native_shift_re'/'audit_two_stage_heading.py'
sys.path.insert(0,str(SOURCE.parent))
import audit_two_stage_heading as a

class TypedTwoStageHeading(unittest.TestCase):
 def test_exact_manifest_and_e8_inventory(self):
  self.assertEqual((len(a.pins()),len(a.E8)),(87,13))
 def test_every_low_bit_combination_including_other_flags(self):
  for flags in range(256):
   selected=a.policy(flags,0x1245)
   self.assertEqual(selected['shortTask_plus74'],(flags>>1)&1)
   self.assertEqual(selected['shortTask_plus72'],0x1245 if flags&2 else 0)
   self.assertEqual(selected['method'],'manual' if flags&1 else 'helper')
 def test_both_constructor_variants_carry_saved_heading_flag(self):
  p=a.pins()
  self.assertEqual(p[0x03025edb].hex(),'c6458401')
  self.assertEqual(p[0x03009375].hex(),'c6414401')
 def test_both_dynamic_group_variants_clear_heading_flag(self):
  p=a.pins()
  self.assertEqual(p[0x0302605a].hex(),'40887d84')
  self.assertEqual(p[0x030092ec].hex(),'885144')
  self.assertEqual(p[0x030092d6].hex(),'66895142')
 def test_constructor_copies_descriptor_heading_and_flag(self):
  self.assertEqual(a.pins()[0x02f2c885].hex(),'0fb64244')
  self.assertEqual(a.pins()[0x02f2c889].hex(),'884144')
 def test_b_sender_uses_flag_for_later_selection(self):
  self.assertEqual(a.pins()[0x02f4f530].hex(),'80797400')
  self.assertEqual(a.pins()[0x02f4f534].hex(),'0fb74172')
  self.assertEqual(a.pins()[0x02f4f538].hex(),'7556')
 def test_task_release_precedes_b_heading_select(self):
  self.assertEqual(a.E8[0x02f4f52b],0x02f50fe4)
  self.assertLess(0x02f4f52b,0x02f4f530)
  self.assertEqual(a.pins()[0x02f50ff8].hex(),'ff4818')
  self.assertEqual(a.pins()[0x02f51002].hex(),'48832000')
 def test_independent_dynamic_group_samples_are_not_proof_of_crowding(self):
  self.assertEqual(a.policy(0,15)['later_B_heading'],'live group+0xBF0')
  self.assertEqual(a.policy(2,15)['later_B_heading'],'shortTask+0x72')
 def test_wrong_hash_still_fails_under_python_o(self):
  with tempfile.TemporaryDirectory() as d:
   fake=Path(d)/'bad.exe';fake.write_bytes(b'MZ'+bytes(100))
   for args in ([],['-O']):
    result=subprocess.run([sys.executable,*args,str(SOURCE),'--exe',str(fake)],capture_output=True,text=True)
    self.assertNotEqual(result.returncode,0)
    self.assertIn('SHA_MISMATCH',result.stderr)
 def test_never_overwrite_game_executable(self):
  with tempfile.TemporaryDirectory() as d:
   fake=Path(d)/'game.exe';fake.write_bytes(b'original')
   result=subprocess.run([sys.executable,str(SOURCE),'--exe',str(fake),'--out',str(fake)],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0)
   self.assertIn('EXE_OVERWRITE_FORBIDDEN',result.stderr)
   self.assertEqual(fake.read_bytes(),b'original')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private game executable is excluded from public CI')
 def test_private_actual_exe(self):
  result=a.audit(os.getenv('WH3_903_EXE'))
  self.assertEqual((result['instruction_starts'],result['e8_targets']),(87,13))
  self.assertFalse(result['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
