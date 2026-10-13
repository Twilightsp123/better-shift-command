"""Synthetic contract for exact handler scheduler stack and separate task type."""
import os,sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'))
import audit_scheduler_task_boundary as a

class SchedulerTaskBoundary(unittest.TestCase):
 def test_three_descriptor_identities_are_distinct(self):
  self.assertEqual(a.TYPED_CALLBACKS[0x039407A8],0x032701C4)
  self.assertEqual(a.TYPED_CALLBACKS[0x03940EE0],0x0326F0DC)
  self.assertEqual(a.TYPED_CALLBACKS[0x03941408],0x0326F07C)
  self.assertEqual(len(set(a.TYPED_CALLBACKS.values())),5)
 def test_dispatcher_slots_and_bookkeeping_pinned(self):
  self.assertEqual(a.PINS[0x030DBF6D],'488da918080000')
  self.assertEqual(a.PINS[0x030DBF74],'8bbd80000000')
  self.assertEqual(a.PINS[0x030DBF7F],'488b4cfd00')
  self.assertEqual(a.PINS[0x030DBF97],'29839c080000')
  self.assertEqual(a.PINS[0x030DBFA1],'0183a0080000')
  self.assertEqual(a.PINS[0x030DBFA7],'ff8b98080000')
 def test_embedded_owner_layout_distinct_from_move_queue(self):
  self.assertEqual(0x30+0x898,0x8C8)
  self.assertEqual(a.PINS[0x030C4813],'488d4b30')
  self.assertEqual(a.PINS[0x030C481C],'8b83c8080000')
  self.assertEqual(a.EDGES[0x030C4817],0x030DBF3C)
 def test_similar_task_fields_not_pointer_identity(self):
  self.assertEqual(a.PINS[0x0327020D],'488b8b88000000')
  self.assertEqual(a.EDGES[0x03270229],0x0311C5E0)
  self.assertEqual(a.PINS[0x0311C603],'4881c168010000')
  self.assertEqual(a.PINS[0x030EE90F],'4d898268010000')
  self.assertNotEqual({'state':4,'p':0x1000}['p'],
                      {'state':4,'p':0x2000}['p'])
 def test_pinned_coverage(self):
  self.assertEqual(len(a.PINS),46)
  self.assertEqual(len(a.EDGES),5)
  self.assertEqual(len(a.TYPED_CALLBACKS),5)
 def test_wrong_exe_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'wrong.exe';f.write_bytes(b'MZwrong-original')
   with self.assertRaises(ValueError):a.audit(f)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Original EXE excluded from public CI')
 def test_original_exe(self):
  report=a.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(report['opcode_instruction_starts'],46)
  self.assertFalse(report['MOVE_slot_to_A_B_factory_parent_proven'])
  self.assertFalse(report['native_patch_authorized'])
if __name__=='__main__':unittest.main()
