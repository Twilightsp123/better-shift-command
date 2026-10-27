"""R80 public contracts, original commercial EXE deliberately optional."""
import importlib.util,json,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
spec=importlib.util.spec_from_file_location('r80',ROOT/'audit_r80_focus.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
M=json.loads((ROOT/'r80_focus_pins.json').read_text())
class R80(unittest.TestCase):
 def test_pin_count(self):self.assertEqual(len(M['pins']),58)
 def test_edges(self):self.assertEqual(len(M['e8']),6)
 def test_unwind(self):self.assertEqual(len(M['function_ranges']),5)
 def test_member_control(self):self.assertEqual(M['pins']['03076f7e']['hex'],'488db918070000')
 def test_member_record(self):self.assertEqual(M['pins']['030771ec']['hex'],'4c8d8b10090000')
 def test_builder_edge(self):self.assertEqual(M['e8']['0307722b'],'0311f34c')
 def test_goal_staging(self):self.assertEqual(M['pins']['03077243']['hex'],'0f1101')
 def test_manager_selector(self):self.assertEqual(M['e8']['0311f417'],'03132178')
 def test_manager_mode_value(self):self.assertEqual(M['pins']['0311f410']['hex'],'448b88a0000000')
 def test_context_chain(self):self.assertEqual(M['pins']['0311f409']['hex'],'488b8960010000')
 def test_member_cursor_read(self):self.assertEqual(M['pins']['0311f41c']['hex'],'488b5728')
 def test_selected_pointer_eq(self):self.assertEqual(M['pins']['0311f43e']['hex'],'4c3bf0')
 def test_cursor_movement(self):self.assertEqual(M['pins']['0311f530']['hex'],'4c894728')
 def test_cursor_save(self):self.assertEqual(M['pins']['0311f54f']['hex'],'4c896730')
 def test_selector_value3(self):self.assertEqual(r.choose(3,'S','R','F'),('manager_special','S'))
 def test_value3_missing_special(self):self.assertEqual(r.choose(3,None,'R','F'),('reference_plus_0x80','R'))
 def test_ref(self):self.assertEqual(r.choose(1,'S','R','F'),('reference_plus_0x80','R'))
 def test_fallback(self):self.assertEqual(r.choose(1,'S',None,'F'),('manager_fallback','F'))
 def test_not_formation_mode3(self):self.assertFalse(M['same_queued_shift_task_instance_proven'])
 def test_exact_cursor(self):self.assertEqual(r.scan_exact([dict(candidate='X',next=1),dict(candidate='Y',next=None)],0,'Y'),(True,1))
 def test_no_exact_match_not_route_failure(self):self.assertEqual(r.scan_exact([dict(candidate='X',next=None)],0,'Y'),(False,None))
 def test_cycle_rejected(self):
  with self.assertRaisesRegex(ValueError,'CYCLE'):r.scan_exact([dict(candidate='X',next=0)],0,'Y')
 def test_pointer_fields_not_logged(self):self.assertFalse(M['gameplay_patch_authorized'])
 def test_wrong_exe(self):
  with self.assertRaisesRegex(r.EvidenceDrift,'SHA_FAIL_CLOSED'):r.verify(b'MZ'+bytes(500),M)
 def test_original_exe_optional(self):
  path=os.environ.get('BSC_EXE')
  if not path:self.skipTest('Licensed WH3 exe unavailable in public GitHub CI')
  self.assertFalse(r.verify(Path(path).read_bytes(),M)['queued_shift_identity_proven'])
