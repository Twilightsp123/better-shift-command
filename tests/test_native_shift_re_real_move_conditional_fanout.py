"""Synthetic-only contracts for exact-build conditional MOVE->member fanout audit."""
import importlib.util
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"maintenance_tools"/"native_shift_re"/"audit_903_real_move_conditional_fanout.py"
spec=importlib.util.spec_from_file_location("audit_903_real_move_conditional_fanout",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
 b=bytearray(0x800);b[:2]=b"MZ"
 struct.pack_into("<I",b,0x3c,0x80)
 b[0x80:0x84]=b"PE\0\0"
 struct.pack_into("<HH",b,0x84,0x8664,2)
 struct.pack_into("<H",b,0x94,0xf0)
 opt=0x98
 struct.pack_into("<H",b,opt,0x20b)
 struct.pack_into("<Q",b,opt+24,m.IMAGE_BASE)
 struct.pack_into("<II",b,opt+112+3*8,0x2000,24)
 q=opt+0xf0
 b[q:q+8]=b".text\0\0\0"
 struct.pack_into("<IIII",b,q+8,0x200,0x1000,0x200,0x400)
 struct.pack_into("<I",b,q+36,0x60000020)
 q+=40
 b[q:q+8]=b".pdata\0\0"
 struct.pack_into("<IIII",b,q+8,0x200,0x2000,0x200,0x600)
 struct.pack_into("<I",b,q+36,0x40000040)
 b[0x400:0x407]=bytes.fromhex("e805000000ff10")
 struct.pack_into("<III",b,0x600,0x1000,0x1010,0x2018)
 struct.pack_into("<III",b,0x60c,0x1010,0x1020,0x2024)
 return bytes(b)

class ExactFanoutContracts(unittest.TestCase):
 def test_two_move_branch_anchors(self):
  self.assertEqual(m.E8["move_construct_task"],(0x030260af,0x02f2c734))
  self.assertEqual(m.E8["task_conditional_group_dispatch"],(0x02f56404,0x03279e40))
  self.assertEqual(m.E8["adapter_to_record_fanout"],(0x030d5603,0x030d5490))
 def test_pe_exception_metadata_and_edges(self):
  pe=m.OriginalPE(fixture())
  self.assertEqual(pe.exrva,0x2000)
  rs=pe.exceptions()
  self.assertEqual(len(rs),2)
  self.assertEqual(m.get_owner(rs,[r[0] for r in rs],0x1005),rs[0])
  self.assertIsNone(m.get_owner(rs,[r[0] for r in rs],0x1020))
 def test_valid_signed_e8(self):
  self.assertEqual(m.e8_target(0x1000,bytes.fromhex("e805000000")),0x100a)
  self.assertEqual(m.e8_target(0x1000,bytes.fromhex("e8fbffffff")),0x1000)
  with self.assertRaisesRegex(ValueError,"NOT_E8"):
   m.e8_target(0x1000,bytes.fromhex("ff10000000"))
 def test_reject_nonexec_read(self):
  pe=m.OriginalPE(fixture())
  with self.assertRaisesRegex(ValueError,"NOT_EXEC"):
   pe.read(0x2000,8,True)
  self.assertEqual(pe.read(0x1000,5,True),bytes.fromhex("e805000000"))
 def test_reject_bad_exception_sort(self):
  b=bytearray(fixture());struct.pack_into("<I",b,0x60c,0x1000)
  with self.assertRaisesRegex(ValueError,"UNSORTED_FUNCTION_TABLE"):
   m.OriginalPE(b).exceptions()
 def test_reject_untrusted_wrong_build_no_change(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"fake.exe";raw=fixture();p.write_bytes(raw)
   with self.assertRaisesRegex(ValueError,"SHA256_MISMATCH"):
    m.inspect(p)
   self.assertEqual(p.read_bytes(),raw)
 def test_original_predicate_not_global_waypoint(self):
  self.assertEqual([n for n in range(6) if (0x29>>n)&1],[0,3,5])
  self.assertEqual(len(m.BYTES),8)
  self.assertEqual(len(m.E8),12)
 def test_no_native_hook_or_patch(self):
  s=SCRIPT.read_text(encoding="utf8")
  self.assertIn("runtime_patch_authorized=False",s)
  self.assertNotIn("WriteProcessMemory(",s)
  self.assertNotIn("VirtualProtect(",s)

if __name__=="__main__":unittest.main()
