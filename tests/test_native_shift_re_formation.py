"""Synthetic-only tests for exact-SHA 9.0.3 formation-entry evidence reader."""
import mmap
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"maintenance_tools"/"native_shift_re"/"audit_903_formation_entry.py"
sys.path.insert(0,str(SCRIPT.parent))
from audit_903_formation_entry import (BASE,TARGET_SHA256,INSTRUCTIONS,DIRECT_CALLS,
                                      pe_sections,read_executable,e8_target,verify)

def fixture():
 m=bytearray(0x900);m[:2]=b"MZ";struct.pack_into("<I",m,0x3c,0x80)
 m[0x80:0x84]=b"PE\0\0"
 struct.pack_into("<HH",m,0x84,0x8664,2)
 struct.pack_into("<H",m,0x94,0xf0)
 opt=0x98
 struct.pack_into("<H",m,opt,0x20b)
 struct.pack_into("<Q",m,opt+24,BASE)
 p=opt+0xf0
 m[p:p+8]=b".text\0\0\0"
 struct.pack_into("<IIII",m,p+8,0x200,0x1000,0x200,0x400)
 struct.pack_into("<I",m,p+36,0x60000020)
 p+=40
 m[p:p+8]=b".rdata\0\0"
 struct.pack_into("<IIII",m,p+8,0x200,0x2000,0x200,0x600)
 struct.pack_into("<I",m,p+36,0x40000040)
 m[0x400:0x405]=bytes.fromhex("e805000000")
 m[0x600:0x605]=bytes.fromhex("e805000000")
 return bytes(m)

class FormationEntryContracts(unittest.TestCase):
 def test_exact_sha_and_code_guards(self):
  self.assertEqual(len(TARGET_SHA256),64)
  self.assertEqual(len(INSTRUCTIONS),23)
  self.assertEqual(len(DIRECT_CALLS),6)

 def test_ordered_call_locations_in_one_unit_update(self):
  a=DIRECT_CALLS
  self.assertLess(a["unit_tick_to_member_aggregate"][0],a["unit_tick_to_group_target"][0])
  self.assertLess(a["unit_tick_to_group_target"][0],a["unit_tick_to_queue_processing"][0])

 def test_executable_only(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"fixture.exe";p.write_bytes(fixture())
   with p.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
    sections=pe_sections(mm)
    self.assertEqual(read_executable(mm,sections,0x1000,5),bytes.fromhex("e805000000"))
    with self.assertRaisesRegex(ValueError,"NON_EXECUTABLE_SECTION"):
     read_executable(mm,sections,0x2000,5)

 def test_e8_target_and_reject_noncall(self):
  self.assertEqual(e8_target(0x1000,b"\xe8\x05\x00\x00\x00"),0x100a)
  self.assertEqual(e8_target(0x1000,b"\xe8\xfb\xff\xff\xff"),0x1000)
  with self.assertRaisesRegex(ValueError,"NOT_AN_E8_CALL"):
   e8_target(0x1000,b"\x90\0\0\0\0")

 def test_wrong_sha_fail_closed_unchanged(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"fixture.exe";raw=fixture();p.write_bytes(raw)
   with self.assertRaisesRegex(ValueError,"EXE_SHA256_MISMATCH"):verify(p)
   self.assertEqual(p.read_bytes(),raw)

 def test_report_cannot_overwrite_executable(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"fixture.exe";p.write_bytes(fixture())
   r=subprocess.run([sys.executable,str(SCRIPT),"--exe",str(p),"--report",str(p)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
   self.assertEqual(p.read_bytes(),fixture())

 def test_invalid_pe_and_unmapped_section(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"fixture.exe";p.write_bytes(fixture())
   with p.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
    with self.assertRaisesRegex(ValueError,"RVA_NOT_MAPPED"):
     read_executable(mm,pe_sections(mm),0x500000,5)
   p.write_bytes(b"MZ")
   with p.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
    with self.assertRaises(ValueError):pe_sections(mm)

 def test_never_patches_and_denies_runtime_approval(self):
  source=SCRIPT.read_text(encoding="utf-8")
  self.assertIn('"runtime_patch_authorized":False',source)
  self.assertNotIn("WriteProcessMemory(",source)
  self.assertNotIn("VirtualProtect(",source)

if __name__=="__main__":
 unittest.main()
