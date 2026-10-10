"""Offline guards for 9.0.3 group layout-vs-waypoint forensic verifier."""
import mmap,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"maintenance_tools"/"native_shift_re"))
from audit_903_layout_vs_arrival import (BASE,GUARDS,STRATEGIES,GROUP_AFTER_FANOUT,
                                         read_any,verify)
from audit_903_formation_entry import pe_sections
from test_native_shift_re_formation import fixture

class LayoutNotArrivalTests(unittest.TestCase):
 def test_machine_byte_guards_are_pinned(self):
  self.assertEqual(len(GUARDS.strip().splitlines()),26)
 def test_eight_real_strategy_types(self):
  self.assertEqual(len(STRATEGIES),8)
  self.assertEqual(len({x[1] for x in STRATEGIES}),8)
 def test_post_fanout_group_method_is_different_type(self):
  self.assertNotIn(GROUP_AFTER_FANOUT,[r[2] for r in STRATEGIES])
 def test_sqrt_layout_not_member_arrival(self):
  self.assertEqual(STRATEGIES[2][2],0x8f7750)
 def test_bounded_group_cardinality_branch_not_waypoint(self):
  self.assertEqual(STRATEGIES[6][2],0x30d1a08)
  self.assertIn("b80d000000443bc0410f46c0c3",GUARDS)
 def test_executable_data_section_separation(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"fixture.exe";p.write_bytes(fixture())
   with p.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
    self.assertEqual(len(read_any(mm,pe_sections(mm),0x2000,4)),4)
 def test_wrong_hash_never_produces_original_proof(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"fixture.exe";data=fixture();p.write_bytes(data)
   with self.assertRaisesRegex(ValueError,"EXE_SHA256_MISMATCH"):verify(p)
   self.assertEqual(p.read_bytes(),data)
 def test_never_promotes_runtime_patch(self):
  s=(ROOT/"maintenance_tools"/"native_shift_re"/"audit_903_layout_vs_arrival.py").read_text()
  self.assertIn('"patch_authorized":False',s)
  self.assertNotIn('WriteProcessMemory(',s)

if __name__=="__main__":unittest.main()
