"""Synthetic-only safety tests; no WH3 executable required in CI."""
import mmap,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"maintenance_tools"/"native_shift_re"))
from audit_903_member_status_spatial import SHA,GUARDS,EDGES,sha256,verify
from audit_903_formation_entry import pe_sections,read_executable,e8_target
from test_native_shift_re_formation import fixture

class MemberStatusSpatialContracts(unittest.TestCase):
 def test_build_hash(self):
  self.assertEqual(len(SHA),64)
 def test_guard_count(self):
  self.assertEqual(len(GUARDS.strip().splitlines()),38)
 def test_edge_count(self):
  self.assertEqual(len(EDGES),13)
 def test_task_bulk_clear(self):
  self.assertEqual(EDGES[0x301c0ee],0x302bc30)
  self.assertIn("302bdf1 83606cfe",GUARDS)
 def test_broadcast_not_arrival(self):
  self.assertIn("3033a83 834a6c01",GUARDS)
  self.assertIn("3033c0a 4183486c03",GUARDS)
 def test_group_spatial_predicate(self):
  self.assertIn("3057ba3 f6426c02",GUARDS)
  self.assertEqual(EDGES[0x3058f40],0x3057b68)
 def test_executable_section_protection(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"fixture.exe";p.write_bytes(fixture())
   with p.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
    sec=pe_sections(mm)
    self.assertEqual(read_executable(mm,sec,0x1000,5),b"\xe8\x05\x00\x00\x00")
    with self.assertRaisesRegex(ValueError,"NON_EXECUTABLE_SECTION"):
     read_executable(mm,sec,0x2000,5)
 def test_fail_closed_wrong_sha(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"wrong.exe";raw=fixture();p.write_bytes(raw)
   with self.assertRaisesRegex(ValueError,"EXE_SHA256_MISMATCH"):
    verify(p)
   self.assertEqual(p.read_bytes(),raw)
 def test_not_a_runtime_patcher(self):
  source=(ROOT/"maintenance_tools"/"native_shift_re"/"audit_903_member_status_spatial.py").read_text()
  self.assertIn('"runtime_patch_authorized":False',source)
  self.assertNotIn("WriteProcessMemory(",source)

if __name__=="__main__":unittest.main()
