"""BSC Round32: queue activation vs late-bound Group strict original EXE."""
import os,sys,tempfile,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_queued_group_latebind_20261017 as a
class NativeQueuedGroupLateBinding(unittest.TestCase):
 def test_pins(self):self.assertEqual(len(a.pins()),39)
 def test_13_e8(self):self.assertEqual(len(a.E8),13)
 def test_queue_handoff(self):
  self.assertEqual(a.E8[0x030445D3],0x030433B0)
  self.assertEqual(a.E8[0x030433E3],0x03043424)
 def test_nested_direct_edge_inventory(self):
  self.assertEqual(len(a.CALLER_DIRECT),2)
  self.assertEqual(len(a.NESTED_DIRECT),3)
  self.assertNotIn(0x0301B8E4,[target for _,target in a.CALLER_DIRECT|a.NESTED_DIRECT])
 def test_virtual_subtask_slots(self):
  self.assertEqual(a.pins()[0x0304346B].hex(),'ff5008')
  self.assertEqual(a.pins()[0x0304348B].hex(),'ff5010')
 def test_separate_immediate_builder(self):
  self.assertEqual(a.E8[0x0302DB8E],0x0301B8E4)
 def test_task_carries_unit_root(self):
  self.assertEqual(a.pins()[0x02F563F4].hex(),'488b4b08')
 def test_late_group_reads(self):
  for at in (0x02F5627B,0x02F563FD,0x02F5649E):
   self.assertEqual(a.pins()[at].hex(),'488b89f8320000')
 def test_group_resolver_call(self):self.assertEqual(a.E8[0x02F56404],0x03279E40)
 def test_mode_specific_A_B(self):
  self.assertEqual(a.E8[0x03279E62],0x02DC2E04)
  self.assertEqual(a.E8[0x03279EB3],0x030D554C)
  self.assertEqual(a.E8[0x03279ED8],0x03263AB0)
 def test_sha_fail_closed_when_optimized(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'bad.exe';p.write_bytes(b'MZ'+bytes(100))
   for flags in ([],['-O']):
    r=subprocess.run([sys.executable,*flags,str(a.__file__),'--exe',str(p)],capture_output=True,text=True)
    self.assertNotEqual(r.returncode,0)
    self.assertIn('SHA_MISMATCH',r.stderr)
 def test_no_exe_overwrite(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'game.exe';p.write_bytes(b'preserved')
   r=subprocess.run([sys.executable,str(a.__file__),'--exe',str(p),'--out',str(p)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
   self.assertEqual(p.read_bytes(),b'preserved')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Private original EXE not present in public CI')
 def test_original_build(self):
  d=a.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((d['opcode_starts'],d['verified_e8']), (39,13))
  self.assertFalse(d['indirect_or_future_group_rebuild_excluded'])
  self.assertFalse(d['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
