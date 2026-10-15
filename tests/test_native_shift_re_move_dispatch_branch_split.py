"""Synthetic branch separation and private exact original EXE validation."""
import os,sys,tempfile,subprocess,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SRC=HERE.parent/'maintenance_tools'/'native_shift_re'/'audit_move_dispatch_branch_split.py'
sys.path.insert(0,str(SRC.parent))
import audit_move_dispatch_branch_split as m

class MoveBranchSplit(unittest.TestCase):
 def test_manifest_counts(self):
  q=m.load()
  self.assertEqual(tuple(len(q[x]) for x in ('PIN','CALL','JMP')),(39,17,6))
 def test_enqueue_branch_ends_before_group_call(self):
  q=m.load()
  self.assertEqual(q['JMP'][0x030326E9],0x0303296A)
  self.assertLess(m.GROUP_E8,0x0303296A)
  self.assertEqual(q['CALL'][m.QUEUED_E8],0x02F50410)
  self.assertEqual(q['CALL'][m.GROUP_E8],0x0302DB44)
 def test_branch_code_synthetic_negative_control(self):
  code={0:('test','cond'),1:('call','0x123'),2:('jmp','0x4'),
        3:('call','0x456'),4:('ret','')}
  self.assertEqual(m.walk(code,1),{1,2,4})
  self.assertEqual(m.walk(code,3),{3,4})
 def test_immediate_path_build_route_fanout_order(self):
  q=m.load()['CALL']
  self.assertEqual(q[0x0302DB8E],0x0301B8E4)
  self.assertEqual(q[0x0302DBC4],0x0301287C)
  self.assertEqual(q[0x0302DBDB],0x030D5490)
  self.assertLess(0x0302DB8E,0x0302DBC4)
  self.assertLess(0x0302DBC4,0x0302DBDB)
 def test_mode_flags_not_equated_with_player_keys(self):
  q=m.load()['JMP']
  self.assertEqual(q[0x0303248A],m.IMMEDIATE)
  self.assertEqual(q[0x03032494],m.IMMEDIATE)
  self.assertEqual(q[0x0303249E],m.QUEUED)
 def test_activation_configures_route_before_shorttask(self):
  q=m.load()['CALL']
  self.assertEqual(q[0x03025E91],0x0301287C)
  self.assertEqual(q[0x03026022],0x0301287C)
  self.assertEqual(q[0x030260AF],0x02F2C734)
  self.assertLess(0x03026022,0x030260AF)
 def test_activated_route_uses_current_group_geometric_reference(self):
  p=m.load()['PIN'];q=m.load()['CALL']
  self.assertEqual(p[0x03025FB8].hex(),'488b89f8320000')
  self.assertEqual(p[0x03025FBF].hex(),'4881c1380b0000')
  self.assertEqual(q[0x03025FC6],0x02D4BE38)
  self.assertEqual(q[0x03025FEE],0x0118309C)
  self.assertEqual(q[0x03025FFB],0x00531E54)
 def test_group_spatial_reference_source(self):
  p=m.load()['PIN'];q=m.load()['CALL']
  self.assertEqual(p[0x02D4BE3F].hex(),'4881c1b8000000')
  self.assertEqual(q[0x02D4BE4B],0x0311D0CC)
  self.assertEqual(0xb38+0xb8,0xbf0)
 def test_group_sampling_is_gated_by_move_slot_bit2(self):
  q=m.load()
  self.assertEqual(q['PIN'][0x03025E5B].hex(),'f6839a00000002')
  self.assertEqual(q['PIN'][0x03025E69].hex(),'0f840a010000')
  self.assertEqual(q['JMP'][0x03025E69],0x03025F79)
 def test_callback_late_reads_live_root_group(self):
  p=m.load()['PIN']
  self.assertEqual(p[0x02F563F4].hex(),'488b4b08')
  self.assertEqual(p[0x02F563FD].hex(),'488b89f8320000')
  self.assertEqual(m.load()['CALL'][0x02F56404],0x03279E40)
 def test_fail_closed_under_python_optimized(self):
  with tempfile.TemporaryDirectory() as tmp:
   bad=Path(tmp)/'wrong.exe';bad.write_bytes(b'MZ'+bytes(128))
   for f in ([],['-O']):
    r=subprocess.run([sys.executable,*f,str(SRC),'--exe',str(bad)],capture_output=True,text=True)
    self.assertNotEqual(r.returncode,0)
    self.assertIn('SHA_MISMATCH',r.stderr)
 def test_output_cannot_overwrite_executable(self):
  with tempfile.TemporaryDirectory() as tmp:
   inp=Path(tmp)/'game.exe';inp.write_bytes(b'unmodified')
   r=subprocess.run([sys.executable,str(SRC),'--exe',str(inp),'--out',str(inp)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
   self.assertIn('EXE_OVERWRITE_FORBIDDEN',r.stderr)
   self.assertEqual(inp.read_bytes(),b'unmodified')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original EXE not included in GitHub CI')
 def test_private_exact_binary(self):
  result=m.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(result['opcode_instruction_starts'],39)
  self.assertEqual(result['direct_e8'],17)
  self.assertEqual(result['conditional_unconditional_jumps'],6)
  self.assertFalse(result['queue_branch_can_reach_group_rebuild_call'])
  self.assertFalse(result['native_gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
