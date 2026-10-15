"""BSC native heading-to-node/member A path regression (no game patch)."""
import os,sys,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'maintenance_tools'/'native_shift_re'/'audit_route_heading_to_member.py'
sys.path.insert(0,str(SRC.parent))
import audit_route_heading_to_member as m

class NativeHeadingToMember(unittest.TestCase):
 def test_guard_inventory(self):
  self.assertEqual((len(m.PINS),len(m.CALLS),len(m.JCC)),(83,15,5))
 def test_both_route_headings_use_same_function(self):
  self.assertEqual(m.CALLS[0x03025e91],0x0301287c)
  self.assertEqual(m.CALLS[0x03026022],0x0301287c)
  self.assertEqual(m.PINS[0x03025e76].hex(),'440fb78398000000')
  self.assertEqual(m.PINS[0x03026015].hex(),'440fb7c0')
 def test_record_seed_copied_to_node_and_descriptor(self):
  self.assertEqual(m.PINS[0x030ecafa].hex(),'6644894938')
  self.assertEqual(m.CALLS[0x03121a40],0x030ec9ec)
  self.assertEqual(m.PINS[0x030eca28].hex(),'66894138')
  self.assertEqual(m.PINS[0x0300890e].hex(),'66894744')
  self.assertEqual(0x20+0x38,0x58)
 def test_converter_is_conditional(self):
  self.assertEqual(m.CALLS[0x03121a82],0x02dc2e04)
  self.assertEqual(m.JCC[0x03121a89],0x03121a91)
  self.assertEqual(m.CALLS[0x03121a99],0x030fda9c)
 def test_immediate_uses_node_geometry(self):
  self.assertEqual(m.PINS[0x0302dbd3].hex(),'488b5018')
  self.assertEqual(m.PINS[0x0302dbd7].hex(),'488b5270')
  self.assertEqual(m.CALLS[0x0302dbdb],0x030d5490)
 def test_deferred_A_fallback_and_explicit_override(self):
  self.assertEqual(m.conditional_A_heading_source(1,0,42,99),99)
  self.assertEqual(m.conditional_A_heading_source(1,1,42,99),42)
  self.assertIsNone(m.conditional_A_heading_source(0,0,42,99))
  self.assertEqual(m.PINS[0x03279e86].hex(),'440fb74144')
 def test_original_exe_overwrite_forbidden(self):
  with tempfile.TemporaryDirectory() as folder:
   target=Path(folder)/'game.exe';target.write_bytes(b'untouched')
   p=subprocess.run([sys.executable,str(SRC),'--exe',str(target),'--out',str(target)],capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0)
   self.assertIn('NEVER_OVERWRITE_EXE',p.stderr)
   self.assertEqual(target.read_bytes(),b'untouched')
 def test_bad_exe_rejected_even_with_optimized_python(self):
  with tempfile.TemporaryDirectory() as folder:
   target=Path(folder)/'wrong.exe';target.write_bytes(b'MZ'+bytes(128))
   for opts in ([],['-O']):
    p=subprocess.run([sys.executable,*opts,str(SRC),'--exe',str(target)],capture_output=True,text=True)
    self.assertNotEqual(p.returncode,0)
    self.assertIn('SHA_MISMATCH',p.stderr)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original EXE not uploaded to public GitHub')
 def test_private_original_exe(self):
  r=m.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((r['opcodes'],r['e8_calls'],r['conditional_branches']),(83,15,5))
  self.assertFalse(r['native_patch_authorized'])
if __name__=='__main__':unittest.main()
