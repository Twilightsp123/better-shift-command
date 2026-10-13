"""Exact native group task fork: factory-created typed vtable +0x100.

This is *not* a test proving that RMB selects one and Shift another.
"""
import os, sys, tempfile, unittest
from pathlib import Path
MODULES=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(MODULES))
import audit_two_handler_factory_origins as a
from audit_wh3_full_native_chain import StrictPE

class TwoHandlerFactoryOrigins(unittest.TestCase):
 def test_both_group_handler_slots_derive_from_actually_installed_tables(self):
  self.assertEqual(a.TABLE[0x039156F8],0x03268840)
  self.assertEqual(a.TABLE[0x039157F8],0x0327BCF8)
  self.assertEqual(a.TABLE[0x03915830],0x032688A0)
  self.assertEqual(a.TABLE[0x03915930],0x0327BD38)
  self.assertEqual(0x039157F8-0x039156F8,0x100)
  self.assertEqual(0x03915930-0x03915830,0x100)
  self.assertEqual(a.LEA_VTABLE[0x0326F0BE],0x03915830)
  self.assertEqual(a.LEA_VTABLE[0x0326F122],0x039156F8)

 def test_upstream_callback_tables_are_present_in_static_registry(self):
  self.assertEqual(a.TABLE[0x03D19A88],0x03940ED8)
  self.assertEqual(a.TABLE[0x03D19C10],0x03941400)
  self.assertEqual(a.TABLE[0x03940ED8],0x0326FFF4)
  self.assertEqual(a.TABLE[0x03941400],0x0326FF60)
  self.assertEqual(a.TABLE[0x03940F00],0x03270098)
  self.assertEqual(a.TABLE[0x03941428],0x03270C68)
  self.assertEqual(len(a.TABLE),12)
  # Static registration only, NOT RMB/Shift command-instance provenance.

 def test_native_runtime_type_checks_use_registration_identity(self):
  self.assertEqual(a.PINS[0x0327711C],'488d05e52aaa00')
  self.assertEqual(a.PINS[0x03277129],'488d05e02aaa00')
  self.assertEqual(a.PINS[0x0327714C],'488b4138')
  self.assertEqual(a.PINS[0x03277168],'488d0d1929aa00')
  self.assertEqual(a.PINS[0x03277214],'488b4138')
  self.assertEqual(a.PINS[0x03277224],'488d0d5d28aa00')
  self.assertEqual(len(a.PINS),39)

 def test_factory_variants_have_different_object_sizes_and_source_fields(self):
  self.assertEqual(a.PINS[0x0326F09B],'b960000000')
  self.assertEqual(a.PINS[0x0326F0A0],'4c8b4b60')
  self.assertEqual(a.PINS[0x0326F0C5],'4c894958')
  self.assertEqual(a.PINS[0x0326F0FB],'b968000000')
  self.assertEqual(a.PINS[0x0326F100],'4c8b4b68')
  self.assertEqual(a.PINS[0x0326F104],'4c8b5350')
  self.assertEqual(a.PINS[0x0326F12C],'4c894958')
  self.assertEqual(a.PINS[0x0326F130],'4c895160')

 def test_typed_dispatch_was_misinterpreted_as_unknown_vtable_origin(self):
  self.assertEqual(a.TABLE[0x03941408],0x0326F07C)
  self.assertEqual(a.TABLE[0x03940EE0],0x0326F0DC)
  self.assertEqual(a.PINS[0x0327BD58],'488b4958')
  self.assertEqual(a.PINS[0x0327BD5F],'ff5060')
  self.assertEqual(a.PINS[0x0327BE59],'ff5070')
  self.assertEqual(a.PINS[0x0327BD29],'ff9048030000')
  self.assertEqual(a.EDGES[0x0327BD0B],0x032638C4)
  self.assertEqual(a.EDGES[0x0327BE4B],0x0306B970)
  self.assertEqual(a.EDGES[0x0327BE86],0x0306B54C)

 def test_register_volatility_requires_explicit_callee_audit(self):
  self.assertEqual(len(a.PRESERVE_REGS),2)
  self.assertEqual(a.LEAF_BOUNDS[0x03264D88],(0x03264D88,0x03264E1D))
  self.assertEqual(a.EDGES[0x0326F0A4],0x030C4BBC)
  self.assertEqual(a.EDGES[0x0326F0B9],0x03264D88)

 def test_shas_and_original_game_must_not_be_assumed(self):
  with tempfile.TemporaryDirectory() as d:
   wrong=Path(d)/'wrong.exe';data=b'MZ'+b'not-original-exe'*50
   wrong.write_bytes(data)
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
    StrictPE(wrong)
   self.assertEqual(wrong.read_bytes(),data)

 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Real WH3 executable is excluded from public GitHub CI')
 def test_full_original_exe_exact_opcode_call_vtables_and_leaves(self):
  result=a.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(result['exact_code_guard_and_disasm_sites'],len(a.PINS))
  self.assertEqual(result['exact_E8_calls'],len(a.EDGES))
  self.assertEqual(result['typed_pointer_table_entries'],len(a.TABLE))
  self.assertEqual(result['source_register_preserving_called_leaf_bodies'],2)
  self.assertFalse(result['RMB_v_Shift_player_input_identity_proven'])
  self.assertFalse(result['native_patch_authorized'])

if __name__=='__main__':unittest.main()
