"""Prevent BSC N1 native MOVE queued-task handoff overclaims.

Public CI never contains the user's original WH3 executable; exact
PE/unwind/opcode verification is run separately on the original SHA.
"""
import os,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(HERE))
import audit_move_queue_task_handoff as a
from audit_wh3_full_native_chain import StrictPE

class MoveQueuedSlotHandoffContracts(unittest.TestCase):
 def test_actual_queued_move_vtable_methods_are_typed(self):
  self.assertEqual(len(a.PINS),35)
  self.assertEqual(len(a.EDGES),6)
  self.assertEqual(len(a.SLOT_METHODS),5)
  self.assertEqual(a.SLOT_METHODS[0x40],0x03039FB0)
  self.assertEqual(a.SLOT_METHODS[0x48],0x03040864)
  self.assertEqual(a.SLOT_METHODS[0x38],0x008D3350)

 def test_previous_task_is_not_blanket_reset(self):
  self.assertEqual(a.PINS[0x03039FC0],'837a2004')
  self.assertEqual(a.PINS[0x03039FCC],'4883ba5801000000')
  self.assertEqual(a.PINS[0x030408CF],'c7422001000000')
  self.assertEqual(a.PINS[0x03040906],'498991a0000000')
  for site in (0x030408EC,0x030408F8,0x030408FF):
   self.assertIn(site,a.PINS)

 def test_replace_vs_append_is_flag_not_separate_move_issuer(self):
  self.assertEqual(a.PINS[0x030326BB],'418ad6')
  self.assertEqual(a.PINS[0x02F50425],'84d2')
  self.assertEqual(a.EDGES[0x030326BE],0x02F50410)
  self.assertEqual(a.EDGES[0x02F50444],0x02F39F94)

 def test_queue_slot_and_B_cached_group_task_are_not_same_class(self):
  self.assertNotEqual(a.SLOT_VTABLE,0x03AE00E8)
  self.assertNotEqual(a.SLOT_METHODS[0x08],0x03281520)

 def test_wrong_exe_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'wrong.exe';b=b'MZ'+b'WRONG_SHA'*100;p.write_bytes(b)
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):StrictPE(p)
   self.assertEqual(p.read_bytes(),b)

 @unittest.skipUnless(os.getenv('WH3_903_EXE'),
  'Exact game EXE is deliberately excluded from GitHub')
 def test_actual_wh3_original_opcode_vtable_and_call_edges(self):
  x=a.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(x['exact_opcode_and_instruction_guards'],35)
  self.assertEqual(x['direct_e8_edges'],6)
  self.assertEqual(x['MOVE_slot_vtable_entries'],5)
  self.assertTrue(x['task_pointer_identity_preserved_when_eligible'])
  self.assertFalse(x['rmb_shift_key_to_r9b_confirmed'] if
                   'rmb_shift_key_to_r9b_confirmed' in x else
                   x['command_keys_confirmed'])
  self.assertFalse(x['native_patch_authorized'])

if __name__=='__main__':unittest.main()
