"""Typed ordinary-B fast-route/no-double-send and slow-node fallback contracts."""
import os,sys,tempfile,subprocess,unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'/'audit_b_release_packet_paths_20261015.py'
sys.path.insert(0,str(SRC.parent))
import audit_b_release_packet_paths_20261015 as a

class BRouteTests(unittest.TestCase):
 def test_manifest(self):self.assertEqual(len(a.inventory()),72)
 def test_edges(self):
  self.assertEqual((len(a.E8),len(a.JCC),len(a.VTABLE)),(11,4,2))
  self.assertEqual(a.E8[0x02F4F617],0x03263F64)
  self.assertEqual(a.E8[0x03279F71],0x03263EC4)
 def test_direct_no_double(self):
  self.assertEqual(a.ordinary_b_schedule(True,False),('direct_packet_set_done','skip'))
 def test_node_fallback(self):
  self.assertEqual(a.ordinary_b_schedule(False,True),('build_node','node_packet_set_done'))
 def test_node_invalid(self):
  self.assertEqual(a.ordinary_b_schedule(False,False),('build_node','defer_no_valid_node'))
 def test_already_finished(self):
  self.assertEqual(a.ordinary_b_schedule(True,True,True),('skip','skip'))
 def test_unique_typed_vtable(self):
  self.assertEqual(a.VTABLE[(0x03AE00E8,0x08)],0x03271B0C)
  self.assertEqual(a.VTABLE[(0x03AE00E8,0x10)],0x03281520)
 def test_wrong_exe_rejected_even_optimized(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'bad.exe';f.write_bytes(b'MZ'+bytes(100))
   for opts in ([],['-O']):
    p=subprocess.run([sys.executable,*opts,str(SRC),'--exe',str(f)],capture_output=True,text=True)
    self.assertNotEqual(p.returncode,0)
    self.assertIn('SHA_MISMATCH',p.stderr)
 def test_exe_not_overwritten(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'bad.exe';f.write_bytes(b'untouched')
   p=subprocess.run([sys.executable,str(SRC),'--exe',str(f),'--out',str(f)],capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0)
   self.assertIn('CANNOT_OVERWRITE_EXE',p.stderr)
   self.assertEqual(f.read_bytes(),b'untouched')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Original EXE must remain private')
 def test_private_actual_exe(self):
  r=a.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((r['opcode_starts'],r['E8_edges'],r['JCC_targets'],r['typed_B_vtable_slots']),
                   (72,11,4,2))
  self.assertFalse(r['native_patch_authorized'])
if __name__=='__main__':unittest.main()
