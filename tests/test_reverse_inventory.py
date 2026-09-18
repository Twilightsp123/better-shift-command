import importlib.util,struct,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'tools/inspect_exe.py'
spec=importlib.util.spec_from_file_location('bsc_pe',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def pe():
 b=bytearray(1024);b[:2]=b'MZ';struct.pack_into('<I',b,0x3c,0x80);b[0x80:0x84]=b'PE\0\0';struct.pack_into('<HHIIIHH',b,0x84,0x8664,1,123,0,0,0xf0,0)
 o=0x98;struct.pack_into('<H',b,o,0x20b);struct.pack_into('<Q',b,o+24,0x140000000);struct.pack_into('<II',b,o+56,0x3000,0x200)
 t=o+0xf0;b[t:t+8]=b'.rdata\0\0';struct.pack_into('<IIII',b,t+8,0x400,0x1000,0x200,0x200)
 b[0x220:0x220+len(b'current_target\0')]=b'current_target\0';return b
class TestPE(unittest.TestCase):
 def test_roundtrip(self):
  p=m.PE(pe());self.assertEqual(p.file_to_rva(0x220),0x1020);self.assertEqual(p.rva_to_file(0x1020,15),0x220)
 def test_string_rva(self):self.assertEqual(m.PE(pe()).occurrences('current_target')[0]['rva'],'0x1020')
 def test_virtual_tail_not_file_backed(self):self.assertIsNone(m.PE(pe()).rva_to_file(0x1300))
 def test_reject_truncated(self):
  with self.assertRaises(ValueError):m.PE(pe()[:300])
 def test_reject_non_x64(self):
  b=pe();struct.pack_into('<H',b,0x84,0x14c)
  with self.assertRaises(ValueError):m.PE(b)
 def test_read_does_not_modify_input(self):
  b=pe();before=bytes(b);m.PE(b).occurrences('is_in_melee');self.assertEqual(before,bytes(b))
if __name__=='__main__':unittest.main(verbosity=2)
