"""Typed member state flag/phase transition and exact game EXE guards."""
import os,sys,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_member_state_phase_20261016 as a
class MemberStatePhase(unittest.TestCase):
 def test_inventory(self):self.assertEqual((len(a.pins()),len(a.E8),len(a.JUMPS),len(a.SLOTS)),(142,15,14,5))
 def test_same_member_vtable(self):self.assertEqual(a.TABLE,0x0390D4F8)
 def test_member_flag_set_and_clear_methods(self):
  self.assertEqual((a.SLOTS[0x128],a.SLOTS[0x130],a.SLOTS[0x138]),
                   (0x0307FB0C,0x0307FC3C,0x0307FB50))
 def test_member_state_writers_are_other_methods(self):
  self.assertEqual((a.SLOTS[0x538],a.SLOTS[0x550]),(0x0306A100,0x0306A53C))
 def test_action_entry_sets_bit4(self):
  for f in range(256):self.assertTrue(a.native_flags(f)['set_action']&4)
 def test_both_exits_clear_bit4(self):
  for f in range(256):
   self.assertFalse(a.native_flags(f)['exit_a']&4)
   self.assertFalse(a.native_flags(f)['exit_b']&4)
 def test_exit_b_keeps_bit8(self):
  self.assertEqual(a.native_flags(0)['exit_b'],0x0a)
  self.assertEqual(a.tick_branch(0x0a,0),'other_virtual_0x498')
 def test_zero_state_with_bit4_is_not_neighbour_branch(self):
  self.assertEqual(a.tick_branch(0x06,0),'other_state_dispatch_no_claim')
 def test_neighbor_branch_needs_B20_null(self):
  self.assertEqual(a.tick_branch(0x02,0,True),'neighbor_then_optional_reset')
  self.assertEqual(a.tick_branch(0x02,0,False),'other_virtual_0x490')
 def test_action_states_four_and_sixteen(self):
  for i in (4,16):self.assertEqual(a.tick_branch(0x04,i),'inline_action_no_neighbor_this_tick')
 def test_other_state_is_not_silently_neighbour(self):
  self.assertEqual(a.tick_branch(0x04,12),'other_state_dispatch_no_claim')
 def test_real_native_action_state_stores(self):
  d=a.pins()
  self.assertEqual(d[0x0306A111].hex(),'c7812403000004000000')
  self.assertEqual(d[0x0306A6BA].hex(),'c7832403000010000000')
 def test_reset_four_conditional_sites(self):
  d=a.pins()
  for at in (0x03068235,0x0306826B,0x03068293,0x030682AF):
   self.assertEqual(d[at].hex(),'83a32403000000')
 def test_late_reset_not_prior_tick_branch_selector(self):
  self.assertEqual(a.E8[0x03082399],0x03068154)
  self.assertEqual(a.E8[0x030822F9],0x03054B84)
  self.assertEqual(a.E8[0x03082301],0x03088808)
  self.assertLess(0x030822F9,0x03082399)
 def test_inline_branch_bypasses_late_reset(self):
  self.assertEqual(a.branch(0x030822E4,a.pins()[0x030822E4]),0x030823A9)
 def test_every_explicit_direct_jump_matches(self):
  d=a.pins()
  for at,dest in a.JUMPS.items():self.assertEqual(a.branch(at,d[at]),dest)
 def test_wrong_build_fail_closed_in_optimized_python(self):
  with tempfile.TemporaryDirectory() as directory:
   x=Path(directory)/'wrong.exe';x.write_bytes(b'MZ'+bytes(100))
   for args in ([],['-O']):
    run=subprocess.run([sys.executable,*args,str(Path(a.__file__)),'--exe',str(x)],capture_output=True,text=True)
    self.assertNotEqual(run.returncode,0)
    self.assertIn('SHA_MISMATCH',run.stderr)
 def test_exe_overwrite_forbidden(self):
  with tempfile.TemporaryDirectory() as directory:
   x=Path(directory)/'game.exe';x.write_bytes(b'preserved')
   run=subprocess.run([sys.executable,str(Path(a.__file__)),'--exe',str(x),'--out',str(x)],capture_output=True,text=True)
   self.assertNotEqual(run.returncode,0)
   self.assertIn('NEVER_OVERWRITE_EXE',run.stderr)
   self.assertEqual(x.read_bytes(),b'preserved')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Original EXE is not in public GitHub CI')
 def test_actual_original_exe(self):
  result=a.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((result['opcode_starts'],result['e8_edges'],result['branch_targets'],result['member_vtable_slots']),(142,15,14,5))
  self.assertFalse(result['native_patch_authorized'])
if __name__=='__main__':unittest.main()
