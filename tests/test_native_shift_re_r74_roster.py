"""R74 public CI: synthetic tests, private matching game EXE optional."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_r74_roster_writers as r
M=json.loads((ROOT/'r74_roster_writer_pins.json').read_text())
class R74(unittest.TestCase):
 def test_pins(self):self.assertEqual(len(M['pins']),45)
 def test_edges(self):self.assertEqual(len(M['edges']),12)
 def test_group_remove_vtable(self):self.assertEqual(M['group_vmethods']['08'],'030e2480')
 def test_member_getter(self):self.assertEqual(M['member_vtables']['03912950']['3f8'],'008f41e0')
 def test_derived_member_getter(self):self.assertEqual(M['member_vtables']['03ad3360']['3f8'],'008f41e0')
 def test_getter_reads_member_group(self):self.assertEqual(M['pins']['008f41e0'],'488b8100030000')
 def test_old_group_remove_dispatch(self):self.assertEqual(M['pins']['030e5532'],'41ff5008')
 def test_group_vector_header(self):self.assertEqual(M['pins']['030cc4ca'],'4883c120')
 def test_vector_append_edge(self):self.assertEqual(M['edges']['030cc4d1'],'01325da4')
 def test_vector_array_swap(self):self.assertEqual(M['pins']['01325de5'],'48894308')
 def test_count_update(self):
  self.assertEqual(M['pins']['01325e2c'],'ff4304')
  self.assertEqual(M['pins']['030e24f9'],'ff4b24')
 def test_late_root_group_bind(self):self.assertEqual(M['pins']['03020a75'],'48899ef8320000')
 def test_b2_reread(self):
  self.assertEqual(M['pins']['0326aa44'],'488b4628')
  self.assertEqual(M['pins']['0326abbd'],'443b6624')
 def test_synthetic_interleave(self):
  x=r.interleave()
  self.assertEqual(x['possible_sent'],['A','C'])
  self.assertFalse(x['actual_concurrent_executions_proven'])
 def test_invalid_synthetic_roster(self):
  with self.assertRaisesRegex(ValueError,'INVALID'):r.interleave(('A','A'),'A')
 def test_wrong_sha_fails_closed(self):
  with self.assertRaisesRegex(r.Drift,'SHA'):r.verify(b'MZ'+bytes(100),M)
 def test_original_exe_optional(self):
  path=os.environ.get('BSC_EXE')
  if not path:self.skipTest('Original WH3 EXE not distributed in public CI')
  result=r.verify(Path(path).read_bytes(),M)
  self.assertFalse(result['actor_overlap_proven'])
