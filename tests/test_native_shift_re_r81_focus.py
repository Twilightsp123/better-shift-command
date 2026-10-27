"""R81 public CI. Original exact game EXE optional; no unsafe native tests."""
import importlib.util,json,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
spec=importlib.util.spec_from_file_location('a81',ROOT/'audit_r81_focus.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
M=json.loads((ROOT/'r81_focus_pins.json').read_text())
def at(s):return M['pins'][s]['hex']
class R81(unittest.TestCase):
 def test_focus_pin_count(self):self.assertEqual(len(M['pins']),71)
 def test_owned_pe_functions(self):self.assertEqual(len(M['functions']),9)
 def test_base_ctor_E8(self):self.assertEqual(M['e8']['03052ca0'],'030f31d8')
 def test_manager_select_E8(self):self.assertEqual(M['e8']['0311f417'],'03132178')
 def test_member_context_load(self):self.assertEqual(at('03052f62'),'488b4358')
 def test_controller_field0(self):self.assertEqual(at('03052f66'),'48898318070000')
 def test_controller_field8(self):self.assertEqual(at('03052f6d'),'48898320070000')
 def test_nullable_738(self):self.assertEqual(at('03052f82'),'4c89a338070000')
 def test_nullable_740_not_738(self):self.assertEqual(at('03052f89'),'4c89a340070000')
 def test_initial_goal_xyz(self):self.assertEqual(at('0305313c'),'f30f118310090000')
 def test_initial_reference_920(self):self.assertEqual(at('0305315c'),'4c89a320090000')
 def test_member_r9_goal(self):self.assertEqual(at('030771ec'),'4c8d8b10090000')
 def test_member_control_read(self):self.assertEqual(at('030770cd'),'488b8338070000')
 def test_controller_selector_lookups(self):
  self.assertEqual(at('0311f405'),'488b4720')
  self.assertEqual(at('0311f410'),'448b88a0000000')
 def test_member_shadow_reference(self):self.assertEqual(at('0308a321'),'0f108920090000')
 def test_other_object_910_is_not_typed_member_writer(self):
  self.assertEqual(at('03054b2a'),'488b8950010000')
  self.assertEqual(at('03054b3b'),'48899110090000')
 def test_cleanup_also_another_object(self):
  self.assertEqual(at('030861f5'),'488b9150010000')
  self.assertEqual(at('0308620d'),'48898a10090000')
 def test_context_alias_never_claims_shift(self):
  x=a.context_model('C','C',1,1)
  self.assertTrue(x['context_same']);self.assertFalse(x['queued_shift_same_instance_proven'])
 def test_different_root_context(self):self.assertFalse(a.context_model('C','D')['context_same'])
 def test_bad_context(self):
  with self.assertRaisesRegex(a.Drift,'MEMBER_CONTEXT'):a.context_model('',None)
 def test_reject_wrong_exe(self):
  with self.assertRaisesRegex(a.Drift,'SHA_SIZE'):a.verify(b'MZ'+bytes(100),M)
 def test_game_exe_optional(self):
  f=os.environ.get('BSC_EXE')
  if not f:self.skipTest('Licensed original EXE excluded from GitHub public CI')
  self.assertFalse(a.verify(Path(f).read_bytes(),M)['queued_shift_instance_proven'])
