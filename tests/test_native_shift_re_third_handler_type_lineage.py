"""Third handler typed lineage: synthetic gates plus opt-in real EXE."""
import os,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'))
import audit_third_handler_type_lineage as a
class ThirdHandlerType(unittest.TestCase):
 def test_vtable_to_type_identifier(self):
  self.assertEqual(a.LEAS[0x03265852],0x03ADE428)
  self.assertEqual(a.POINTERS[0x03ADE4F8],0x008F96B0)
  self.assertEqual(a.LEAS[0x008F96B0],0x03D19BD8)
 def test_static_registered_task_callback(self):
  self.assertEqual(a.POINTERS[0x03D19BD8],0x039407A8)
  self.assertEqual(a.POINTERS[0x039407A8],0x032701C4)
 def test_geometry_callback_and_jump(self):
  self.assertEqual(a.POINTERS[0x039407B0],0x0326F16C)
  self.assertEqual(a.JUMPS[0x0326F179],0x0326EA44)
 def test_constructor_zero_and_callback_read_plus88(self):
  self.assertEqual(a.PINS[0x03265833],'4533c0')
  self.assertEqual(a.PINS[0x032658AC],'4c898388000000')
  self.assertEqual(a.PINS[0x0327020D],'488b8b88000000')
 def test_geometry_context_not_task_identity(self):
  self.assertEqual(a.PINS[0x0326EAB2],'488b4328')
  self.assertEqual(a.PINS[0x0326EAD1],'4c8b8840040000')
  self.assertEqual(a.PINS[0x0326EADB],'4d8b8960010000')
 def test_distinct_from_old_A_and_B_factories(self):
  self.assertNotEqual(a.POINTERS[0x039407A8],a.POINTERS[0x03940EE0])
  self.assertNotEqual(a.POINTERS[0x039407A8],a.POINTERS[0x03941408])
 def test_sixteen_direct_constructor_callers(self):
  self.assertEqual(len(a.CONSTRUCTOR_CALL_SITES),16)
  self.assertEqual(len(a.CALLS),18)
  self.assertTrue(all(a.CALLS[x]==0x0326581C for x in a.CONSTRUCTOR_CALL_SITES))
 def test_invalid_exe_refusal_propagates(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'bad.exe';f.write_bytes(b'MZ-not-exact')
   with mock.patch.object(a,'StrictPE',side_effect=ValueError('SHA_MISMATCH')):
    with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):a.audit(f)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Private original EXE not distributed in public CI')
 def test_original_exe(self):
  r=a.audit(Path(os.getenv('WH3_903_EXE')))
  self.assertEqual(r['opcode_instruction_starts'],45)
  self.assertEqual(r['constructor_callers'],16)
  self.assertFalse(r['move_slot_plus_a0_to_third_parent_plus88_proven'])
  self.assertFalse(r['native_patch_authorized'])
if __name__=='__main__':unittest.main()
