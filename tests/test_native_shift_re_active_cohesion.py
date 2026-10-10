"""Isolated read-only/decoded E8 tests; never represents WH3 gameplay."""
import mmap
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RE = ROOT / "maintenance_tools" / "native_shift_re"
sys.path.insert(0,str(RE))
from audit_903_active_cohesion_links import (KNOWN, TARGET_SHA, WINDOWS, direct_target,
    parse_objdump, disassemble, pe_bytes, analyze)
from scout_pe import parse_pe


def fixture():
 b=bytearray(0x800); b[:2]=b"MZ"
 struct.pack_into('<I',b,0x3c,0x80);b[0x80:0x84]=b'PE\0\0'
 struct.pack_into('<HH',b,0x84,0x8664,1)
 struct.pack_into('<H',b,0x94,0xf0)
 opt=0x98;struct.pack_into('<H',b,opt,0x20b)
 struct.pack_into('<Q',b,opt+24,0x140000000)
 struct.pack_into('<I',b,opt+56,0x4000)
 sec=opt+0xf0;b[sec:sec+5]=b'.text'
 struct.pack_into('<IIII',b,sec+8,0x400,0x1000,0x400,0x400)
 struct.pack_into('<I',b,sec+36,0x60000020)
 b[0x400:0x407]=bytes.fromhex('e805000000ff10')
 return bytes(b)


class ActiveCohesionLinks(unittest.TestCase):
 def test_known_anchor_scope(self):
  self.assertEqual(len(TARGET_SHA),64)
  self.assertEqual(len(KNOWN),9)
  self.assertIn('v3_move_work',WINDOWS)
  self.assertIn('mode0_delegate',WINDOWS)
  self.assertIn('group_distance',WINDOWS)
  self.assertIn('member_pose_tick',WINDOWS)

 def test_e8_forward_backward(self):
  self.assertEqual(direct_target(0x1000,bytes.fromhex('e805000000')),0x100a)
  self.assertEqual(direct_target(0x1000,bytes.fromhex('e8fbffffff')),0x1000)
  with self.assertRaisesRegex(ValueError,'NOT_E8'):
   direct_target(0x1000,b'\x90'*5)

 def test_disasm_parse_avoids_immediate_false_positives(self):
  text='''1000: e8 05 00 00 00  call   0x100a
 1005: ff 10  call   QWORD PTR [rax]
 1007: b8 e8 00 00 00  mov eax,0xe8
 100c: 90  nop'''
  edges,indirect=parse_objdump(text)
  self.assertEqual(edges,[{'site':0x1000,'target':0x100a}])
  self.assertEqual(indirect,[0x1005])

 def test_real_objdump_for_synthetic_fragment(self):
  import shutil
  if not shutil.which('objdump'):self.skipTest('GNU objdump unavailable')
  edges,indirect=disassemble(bytes.fromhex('e805000000ff1090'),0x1000,'objdump')
  self.assertEqual(edges,[{'site':0x1000,'target':0x100a}])
  self.assertEqual(indirect,[0x1005])

 def test_pe_section_mapping(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'f.exe';p.write_bytes(fixture())
   with p.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
    pe=parse_pe(mm)
    self.assertEqual(pe_bytes(mm,pe,0x1000,5),bytes.fromhex('e805000000'))
    with self.assertRaisesRegex(ValueError,'NOT_FILE_BACKED_EXECUTABLE_RVA'):
     pe_bytes(mm,pe,0x2000,5)

 def test_exact_build_gate_fail_closed_no_write(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'f.exe';raw=fixture();p.write_bytes(raw)
   with self.assertRaisesRegex(ValueError,'EXE_SHA256_MISMATCH'):
    analyze(p)
   self.assertEqual(p.read_bytes(),raw)

 def test_cli_rejects_report_overwrite(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'f.exe';p.write_bytes(fixture())
   s=RE/'audit_903_active_cohesion_links.py'
   x=subprocess.run([sys.executable,str(s),'--exe',str(p),'--report',str(p)],capture_output=True,text=True)
   self.assertNotEqual(x.returncode,0)
   self.assertEqual(p.read_bytes(),fixture())

 def test_no_runtime_modification_logic(self):
  text=(RE/'audit_903_active_cohesion_links.py').read_text()
  self.assertIn('"runtime_patch_authorized":False',text)
  self.assertNotIn('WriteProcessMemory(',text)
  self.assertNotIn('VirtualProtect(',text)


if __name__=='__main__':unittest.main()
