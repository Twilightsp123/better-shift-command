"""Compact GitHub CI tests for original MOVE->ordinary B->member goal proof."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
h=Path(__file__).resolve().parent
for directory in (h,h.parent/'maintenance_tools'/'native_shift_re'):
 if (directory/'audit_move_to_motor_goal_bridge.py').exists():sys.path.insert(0,str(directory));break
import audit_move_to_motor_goal_bridge as m
class NativeMoveGoalBridge(unittest.TestCase):
 def test_machine_code_manifest_exact_inventory(self):
  manifest=m.load_manifest()
  self.assertEqual([len(manifest[i]) for i in ('PIN','E8','VT')],[218,28,10])
  self.assertEqual(manifest['E8'][0x02F56479],0x02F4F514)
  self.assertEqual(manifest['E8'][0x02F4F62C],0x03279EE8)
  self.assertEqual(manifest['E8'][0x03279F71],0x03263EC4)
 def test_constructor_types_not_aliased(self):
  vt=m.load_manifest()['VT']
  self.assertEqual(vt[(0x03ABBE18,0x10)],0x02F561E8)
  self.assertEqual(vt[(0x03AE00E8,0x10)],0x03281520)
  self.assertEqual(vt[(0x03AE0128,0x10)],0x03281408)
  self.assertEqual(vt[(0x03913808,0x10)],0x0325E294)
 def test_move_callback_special_branch_excludes_state1(self):
  self.assertTrue(m.shorttask_update_enters_b(4,0,3))
  for s,p,t in ((1,0,3),(4,1,3),(4,0,2),(4,0,4)):
   self.assertFalse(m.shorttask_update_enters_b(s,p,t))
 def test_member_record_kind_flags_are_contextual(self):
  self.assertEqual([m.record_kind(i,99) for i in (5,6,7,8,9)],[0x67,0x68,0x69,5,6])
  self.assertEqual(m.record_kind(5,99,False),0)
  self.assertEqual(m.record_kind(5,99,True,True),0)
 def test_receiver_mode_and_0x20_both_needed(self):
  self.assertTrue(m.receiver_creates_inline_task(0,0x07))
  self.assertTrue(m.receiver_creates_inline_task(0,0x0e))
  self.assertFalse(m.receiver_creates_inline_task(1,0x07))
  self.assertFalse(m.receiver_creates_inline_task(0,0x26))
 def test_guard_rejects_wrong_build_even_optimized(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'bad.exe';f.write_bytes(b'MZ'+bytes(128))
   for flags in ([],['-O']):
    p=subprocess.run([sys.executable,*flags,str(Path(m.__file__)),'--exe',str(f)],capture_output=True,text=True)
    self.assertNotEqual(p.returncode,0)
    self.assertIn('SHA_MISMATCH',p.stderr)
 def test_exe_overwrite_is_forbidden(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'game.exe';f.write_bytes(b'unmodified')
   p=subprocess.run([sys.executable,str(Path(m.__file__)),'--exe',str(f),'--out',str(f)],capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0)
   self.assertIn('CANNOT_OVERWRITE_EXE',p.stderr)
   self.assertEqual(f.read_bytes(),b'unmodified')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'original game EXE must not be uploaded to GitHub')
 def test_private_original_exe(self):
  a=m.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(a['unique_instruction_guards'],218)
  self.assertEqual(a['direct_e8_guards'],28)
  self.assertEqual(a['typed_vtable_guards'],10)
  self.assertFalse(a['limits']['causal_crowding_root_cause_found'])
  self.assertFalse(a['limits']['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
