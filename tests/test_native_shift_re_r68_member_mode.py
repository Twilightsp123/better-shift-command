"""R68 synthetic-only CI; exact private EXE is not distributed in CI."""
import importlib.util,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
spec=importlib.util.spec_from_file_location('r68',ROOT/'audit_r68_member_mode.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
m=json.loads((ROOT/'r68_member_mode_pins.json').read_text())
class R68(unittest.TestCase):
 def test_pin_count(self):self.assertEqual(len(m['pins']),56)
 def test_same_member_setter(self):self.assertEqual(m['vtables']['03912950']['e0'],m['vtables']['03ad3360']['e0'])
 def test_other_methods_diverge(self):self.assertNotEqual(m['vtables']['03912950']['e8'],m['vtables']['03ad3360']['e8'])
 def test_mode_read(self):self.assertEqual(m['pins']['0307d9c4'],'8b8104010000')
 def test_mode_write(self):self.assertEqual(m['pins']['0307d9e5'],'899104010000')
 def test_old1_to0(self):self.assertEqual(r.model(1,0),(0,0,0,True))
 def test_old2_to0(self):self.assertEqual(r.model(2,0),(0,0,0,True))
 def test_other_to0_no_clear(self):self.assertEqual(r.model(3,0),(0,7,11,True))
 def test_mode2_to1_no_clear(self):self.assertEqual(r.model(2,1),(1,7,11,True))
 def test_noop(self):self.assertEqual(r.model(2,2),(2,7,11,False))
 def test_mode3_call(self):self.assertEqual(m['pins']['03071ec7'],'ba03000000')
 def test_mode2_call(self):self.assertEqual(m['pins']['0307fac4'],'ba02000000')
 def test_mode0_gate(self):self.assertEqual(m['pins']['031647a2'],'33d2')
 def test_private_exe(self):
  path=os.environ.get('BSC_EXE')
  if not path:self.skipTest('private original EXE absent from public GitHub CI')
  self.assertFalse(r.verify(Path(path).read_bytes(),m)['shift_hit_proven'])
 def test_wrong_sha(self):
  with self.assertRaisesRegex(r.EvidenceMismatch,'EXE_SHA_OR_SIZE_DRIFT'):r.verify(b'MZ'+bytes(1024),m)
if __name__=='__main__':unittest.main()
