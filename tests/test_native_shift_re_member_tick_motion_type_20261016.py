"""BSC N1 exact member Tick split and typed component store regression."""
import os,sys,tempfile,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_member_tick_motion_type_20261016 as m

class NativeMemberTickType(unittest.TestCase):
 def test_exact_instruction_count(self):self.assertEqual(len(m.pins()),66)
 def test_edge_counts(self):self.assertEqual((len(m.CALLS),len(m.BRANCHES)),(8,8))
 def test_inline_action_state_four(self):
  self.assertEqual(m.tick_state(4,4),'inline_action_tick_no_neighbor')
 def test_inline_action_state_sixteen(self):
  self.assertEqual(m.tick_state(4,16),'inline_action_tick_no_neighbor')
 def test_special_bit_eight(self):self.assertEqual(m.tick_state(12,4),'other_virtual_498')
 def test_other_action_branch(self):self.assertEqual(m.tick_state(4,3),'another_state_branch')
 def test_neighbor_branch(self):
  self.assertEqual(m.tick_state(0,0,True),'neighbor_tick_then_special_state_check')
 def test_reference_b20_skip(self):self.assertEqual(m.tick_state(0,0,False),'other_virtual_490')
 def test_real_target_addresses(self):
  self.assertEqual(m.CALLS[0x030822D2],0x03080F4C)
  self.assertEqual(m.CALLS[0x030822F9],0x03054B84)
  self.assertEqual(m.CALLS[0x03082301],0x03088808)
  self.assertEqual(m.CALLS[0x03082E40],m.CALLS[0x03082E6D])
 def test_all_jump_targets(self):
  d=m.pins()
  for at,dest in m.BRANCHES.items():self.assertEqual(m.jump(at,d[at]),dest)
 def test_typed_component_field_ownership(self):
  d=m.pins()
  self.assertEqual(d[0x03085AD2].hex(),'448a81e4000000')
  self.assertEqual(d[0x03085D06].hex(),'488b4308')
  self.assertEqual(d[0x03085D89].hex(),'f30f1183e00000')
 def test_ctor_vtable_sites(self):
  self.assertEqual(m.COMP_TABLE,0x03ACD0D8)
  self.assertEqual(m.COMP_METHOD,0x03082CD4)
  self.assertEqual(m.pins()[0x0304E83B].hex(),'488906')
 def test_wrong_exe_fails_even_optimized(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'bad.exe';f.write_bytes(b'MZ'+bytes(100))
   for options in ([],['-O']):
    r=subprocess.run([sys.executable,*options,str(ROOT/'audit_member_tick_motion_type_20261016.py'),'--exe',str(f)],capture_output=True,text=True)
    self.assertNotEqual(r.returncode,0)
    self.assertIn('SHA_MISMATCH',r.stderr)
 def test_no_overwrite_game_binary(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'game.exe';f.write_bytes(b'unmodified')
   r=subprocess.run([sys.executable,str(ROOT/'audit_member_tick_motion_type_20261016.py'),'--exe',str(f),'--out',str(f)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertIn('EXE_OVERWRITE_FORBIDDEN',r.stderr)
   self.assertEqual(f.read_bytes(),b'unmodified')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'original game executable is not in public GitHub')
 def test_real_original_exe(self):
  d=m.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((d['guarded_instruction_starts'],d['e8_edges'],d['branch_targets'],d['component_vtable_slots']),(66,8,8,1))
  self.assertFalse(d['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
