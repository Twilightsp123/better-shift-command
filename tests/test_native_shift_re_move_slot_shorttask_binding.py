"""Original MOVE slot -> new shortTask -> associated bigTask alias proof."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SRC=HERE/'audit_move_slot_shorttask_binding.py'
if not SRC.exists():SRC=HERE.parent/'maintenance_tools'/'native_shift_re'/'audit_move_slot_shorttask_binding.py'
sys.path.insert(0,str(SRC.parent))
import audit_move_slot_shorttask_binding as m

class SlotShortTaskIdentity(unittest.TestCase):
 def test_stack_alias_formula(self):
  for addr in (0,0x100000,0x7ffee100000):self.assertTrue(m.stack_alias_matches(addr))
 def test_slot_address_and_constructor_descriptor(self):
  self.assertEqual(m.PINS[0x03025DD7],'4c8db3a0000000')
  self.assertEqual(m.PINS[0x0302608D],'4c897590')
  self.assertEqual(m.PINS[0x0302609F],'4c8d4c2440')
  self.assertEqual(m.PINS[0x02F2C770],'498bd1')
 def test_copied_descriptor_pointer_goes_to_shorttask_plus80(self):
  self.assertEqual(m.PINS[0x02F2C758],'4c8d4130')
  self.assertEqual(m.PINS[0x02F2C8A7],'488b4250')
  self.assertEqual(m.PINS[0x02F2C8AB],'48894150')
  self.assertEqual(m.E8[0x02F2C784],0x02F2C834)
 def test_shorttask_getter_reads_slot_pointer_not_task_geometry(self):
  self.assertEqual(m.PINS[0x02F4EFE0],'488b8180000000')
  self.assertEqual(m.PINS[0x02F4EFEC],'488b00')
  self.assertEqual(m.PINS[0x02F4EFF0],'488b8198000000')
 def test_compatibility_can_invalidate_inherited_pointer(self):
  self.assertEqual(m.PINS[0x03025E39],'49893e')
  self.assertEqual(m.PINS[0x03040906],'498991a0000000')
 def test_fresh_builder_writes_back_to_slot_or_fallback(self):
  self.assertEqual(m.E8[0x02F2C81B],0x02F41644)
  self.assertEqual(m.E8[0x02F41669],0x0310ED2C)
  self.assertEqual(m.PINS[0x02F41675],'488901')
  self.assertEqual(m.PINS[0x02F4167F],'48898398000000')
 def test_negative_exe_rejected_even_under_optimization(self):
  with tempfile.TemporaryDirectory() as t:
   x=Path(t)/'bad.exe';x.write_bytes(b'MZ'+bytes(100))
   for flag in ([],['-O']):
    r=subprocess.run([sys.executable,*flag,str(SRC),'--exe',str(x)],capture_output=True,text=True)
    self.assertNotEqual(r.returncode,0);self.assertIn('SHA_MISMATCH',r.stderr)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'do not publish original game EXE')
 def test_original_exe(self):
  j=m.decoded_pins_are_exact(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(j['verified_instruction_starts'],36)
  self.assertEqual(j['verified_e8'],6)
  self.assertTrue(j['win64_stack_alias'])
  self.assertFalse(j['member_goal_generation_conflict_proven'])
if __name__=='__main__':unittest.main()
