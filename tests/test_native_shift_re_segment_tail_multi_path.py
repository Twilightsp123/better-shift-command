"""BSC native segment fallback exact-build negative contracts (synthetic only in CI)."""
import mmap,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"maintenance_tools"/"native_shift_re"))
import audit_903_segment_tail_multi_path as m

def fixture():
 b=bytearray(0x700);b[:2]=b"MZ";struct.pack_into("<I",b,0x3c,0x80)
 b[0x80:0x84]=b"PE\0\0"
 struct.pack_into("<HH",b,0x84,0x8664,2);struct.pack_into("<H",b,0x94,0xf0)
 o=0x98;struct.pack_into("<H",b,o,0x20b)
 struct.pack_into("<Q",b,o+24,m.BASE)
 p=o+0xf0;b[p:p+5]=b".text";struct.pack_into("<IIII",b,p+8,0x100,0x1000,0x100,0x400)
 struct.pack_into("<I",b,p+36,0x60000020)
 p+=40;b[p:p+6]=b".rdata";struct.pack_into("<IIII",b,p+8,0x100,0x2000,0x100,0x500)
 struct.pack_into("<I",b,p+36,0x40000040)
 b[0x400:0x405]=bytes.fromhex("e805000000")
 return bytes(b)

class SegmentFallback(unittest.TestCase):
 def test_shared_tail_not_mode0_exclusive(self):
  self.assertEqual(len(m.FALLBACK_SLOTS),6)
  self.assertIn(0x03acfd68,m.FALLBACK_SLOTS)
  self.assertEqual(m.VIRTUAL["unit_v248"][1],0x030135e0)
 def test_alternative_member_issuer_independent_of_group_fanout(self):
  self.assertEqual(m.E8["unit_alt_target_generation_1"],(0x0301385e,0x030c9a64))
  self.assertEqual(m.E8["unit_alt_member_dispatch_1"][1],0x02ded114)
  self.assertEqual(m.E8["adapter_to_group_fanout"][1],0x030d5490)
 def test_executable_only_pe_mapping(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"sample.exe";path.write_bytes(fixture())
   with path.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as x:
    sec=[(0x1000,0x100,0x400,True),(0x2000,0x100,0x500,False)]
    self.assertEqual(m.read(x,sec,0x1000,5,True),bytes.fromhex("e805000000"))
    with self.assertRaises(ValueError):m.read(x,sec,0x2000,5,True)
 def test_wrong_binary_fail_closed_and_unmodified(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"fake.exe";data=fixture();path.write_bytes(data)
   with self.assertRaisesRegex(ValueError,"SHA"):m.verify(path)
   self.assertEqual(path.read_bytes(),data)
 def test_cannot_overwrite_executable_report(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"fake.exe";data=fixture();path.write_bytes(data)
   script=ROOT/"maintenance_tools"/"native_shift_re"/"audit_903_segment_tail_multi_path.py"
   p=subprocess.run([sys.executable,str(script),"--exe",str(path),"--out",str(path)],capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0);self.assertEqual(path.read_bytes(),data)
 def test_runtime_patch_denied(self):
  script=(ROOT/"maintenance_tools"/"native_shift_re"/"audit_903_segment_tail_multi_path.py").read_text()
  self.assertIn('"runtime_patch_authorized":False',script)
  self.assertNotIn("WriteProcessMemory(",script)
  self.assertNotIn("VirtualProtect(",script)
if __name__=="__main__":unittest.main()
