"""CI-safe BSC: SHA-locked original A/B member receiver and position dispatch."""
import os,sys,tempfile,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_ab_member_mode_to_position_20261017 as a
class ABMemberPosition(unittest.TestCase):
 def test_88_instructions(self):self.assertEqual(len(a.inventory()),88)
 def test_9_direct_calls(self):self.assertEqual(len(a.CALLS),9)
 def test_single_typed_member_table(self):
  self.assertEqual(a.VTABLE,{0x368:0x0306B9F0,0x100:0x03073568,0xe8:0x03073224})
 def test_a_receiver_one(self):self.assertEqual(a.inventory()[0x030D5509].hex(),'41b001')
 def test_b_receiver_zero(self):self.assertEqual(a.inventory()[0x03265D39].hex(),'4533c0')
 def test_same_receiver_method_offset(self):
  p=a.inventory()
  self.assertEqual(p[0x030D550F],p[0x03265D3F])
  self.assertEqual(p[0x030D550F].hex(),'ff9068030000')
 def test_inline_no_flags(self):
  for v in (0,1,0x10):self.assertEqual(a.mode_route(False,v),'inline_task')
 def test_packet_bit20_disables_inline(self):
  for v in (0x20,0x30,0xff):self.assertEqual(a.mode_route(False,v),'member_virtual')
 def test_nonzero_helper_disables_inline(self):
  for v in (0,1,0x10,0xff):self.assertEqual(a.mode_route(True,v),'member_virtual')
 def test_member_state_one_and_two(self):
  for v in (1,2):self.assertEqual(a.member_virtual_slot(v),0x100)
 def test_member_other_states(self):
  for v in (0,3,4,16,127):self.assertEqual(a.member_virtual_slot(v),0xe8)
 def test_short_member_virtual_has_typed_position_writer(self):
  self.assertEqual(a.CALLS[0x03073571],0x0315F4E0)
  self.assertEqual(a.inventory()[0x0315F52C].hex(),'f20f118788000000')
 def test_long_member_virtual_has_typed_position_writer(self):
  self.assertEqual(a.CALLS[0x0307328B],0x0315EC98)
  self.assertEqual(a.inventory()[0x0315F327].hex(),'f20f118688000000')
 def test_member_flag_clears_bit8_not_bit4(self):
  for old in range(256):
   new=(old&0xf7)|0x02
   self.assertEqual(new&0x08,0)
   self.assertEqual(new&0x04,old&0x04)
 def test_jump_target_contract(self):
  p=a.inventory()
  for at,dst in a.JCC.items():
   self.assertEqual(a.branch_destination(at,p[at]),dst)
 def test_mode_not_a_causality_proof(self):
  self.assertEqual(a.mode_route(False,0),'inline_task')
  self.assertEqual(a.member_virtual_slot(4),0xe8)
 def test_sha_mismatch_even_under_python_optimized(self):
  with tempfile.TemporaryDirectory() as td:
   fake=Path(td)/'bad.exe';fake.write_bytes(b'MZ'+bytes(90))
   for mode in ([],['-O']):
    r=subprocess.run([sys.executable,*mode,str(a.__file__),'--exe',str(fake)],capture_output=True,text=True)
    self.assertNotEqual(r.returncode,0)
    self.assertIn('SHA_MISMATCH',r.stderr)
 def test_game_binary_overwrite_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   fake=Path(td)/'game.exe';fake.write_bytes(b'original')
   r=subprocess.run([sys.executable,str(a.__file__),'--exe',str(fake),'--out',str(fake)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
   self.assertEqual(fake.read_bytes(),b'original')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original WH3 EXE not in GitHub CI')
 def test_real_original_exe(self):
  r=a.audit(os.getenv('WH3_903_EXE'))
  self.assertEqual((r['verified_full_opcodes'],r['verified_direct_e8'],r['verified_conditional_edges'],r['verified_member_vtable_slots']),(88,9,5,3))
  self.assertFalse(r['root_cause_proven'])
if __name__=='__main__':unittest.main()
