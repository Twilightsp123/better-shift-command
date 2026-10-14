"""BSC 9.0.3 original static group-generation proof and isolated counterexamples.

The simulation has synthetic epoch IDs; this is not a WH3 scheduler emulator.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'maintenance_tools'/'native_shift_re'))
import audit_move_group_generation_latebind as a

class MoveGroupLateBinding(unittest.TestCase):
 def test_exact_machine_code_pins_and_direct_calls_coverage(self):
  self.assertEqual(len(a.PINS),91)
  self.assertEqual(len(a.DIRECT_E8),19)
  self.assertEqual(len(a.TYPED_METHODS),3)
  self.assertEqual(a.DIRECT_E8[0x0302DB8E],0x0301B8E4)
  self.assertEqual(a.DIRECT_E8[0x0301B902],0x030197A8)
  self.assertEqual(a.DIRECT_E8[0x0301B91F],0x0301B834)

 def test_group_teardown_returns_old_object_to_pool(self):
  self.assertEqual(a.PINS[0x030197CB],bytes.fromhex('488b13'))
  self.assertEqual(a.PINS[0x030197D5],bytes.fromhex('488b8950010000'))
  self.assertEqual(a.PINS[0x030197DC],bytes.fromhex('4883c158'))
  self.assertEqual(a.DIRECT_E8[0x030197E0],0x0302C2D4)
  self.assertEqual(a.PINS[0x0302C2EC],bytes.fromhex('ff5010'))
  self.assertEqual(a.PINS[0x0302C2F2],bytes.fromhex('488907'))
  self.assertEqual(a.PINS[0x0302C2F5],bytes.fromhex('48893b'))

 def test_pooled_group_destructor_skips_deallocation_on_zero_flag(self):
  self.assertEqual(a.PINS[0x0302C2E7],bytes.fromhex('33d2'))
  self.assertEqual(a.DIRECT_E8[0x030C61E3],0x030C4748)
  self.assertEqual(a.PINS[0x030C61E8],bytes.fromhex('f6c301'))
  self.assertEqual(a.PINS[0x030C61EB],bytes.fromhex('740d'))
  self.assertEqual(a.DIRECT_E8[0x030C61F5],0x04EA934)

 def test_new_group_pops_the_same_pool_and_reinitializes_type(self):
  self.assertEqual(a.PINS[0x0301B86D],bytes.fromhex('488bba50010000'))
  self.assertEqual(a.PINS[0x0301B874],bytes.fromhex('488b5f58'))
  self.assertEqual(a.PINS[0x0301B8B0],bytes.fromhex('48894f58'))
  self.assertEqual(a.DIRECT_E8[0x0301B8B7],0x030C2C3C)
  self.assertEqual(a.PINS[0x030C2C6F],bytes.fromhex('48890b'))
  self.assertEqual(a.PINS[0x0301B96D],bytes.fromhex('48899ef8320000'))
  self.assertEqual(a.TYPED_METHODS[0x0390F5F0+0x10],0x030C61D4)

 def test_short_task_late_reads_current_group(self):
  self.assertEqual(a.PINS[0x02F2C74D],bytes.fromhex('48895108'))
  self.assertEqual(a.PINS[0x02F563F4],bytes.fromhex('488b4b08'))
  self.assertEqual(a.PINS[0x02F563FD],bytes.fromhex('488b89f8320000'))
  self.assertEqual(a.DIRECT_E8[0x02F56404],0x03279E40)
  self.assertEqual(a.TYPED_METHODS[0x03ABBE18+0x10],0x02F561E8)

 def test_short_task_has_own_descriptor_inputs_separate_from_group_pointer(self):
  self.assertEqual(a.DIRECT_E8[0x02F56358],0x03263D68)
  self.assertEqual(a.PINS[0x02F56371],bytes.fromhex('f3410f104328'))
  self.assertEqual(a.PINS[0x02F56377],bytes.fromhex('f3410f104b2c'))
  self.assertEqual(a.PINS[0x02F56389],bytes.fromhex('498b4338'))
  self.assertEqual(a.PINS[0x02F56394],bytes.fromhex('498b4340'))

 def test_dispatch_precedes_conditional_group_cleanup(self):
  self.assertLess(0x02F56404,0x02F564B7)
  self.assertLess(0x02F564B7,0x02F5652D)
  self.assertEqual(a.PINS[0x02F564C4],bytes.fromhex('4038b3a1000000'))
  self.assertEqual(a.PINS[0x02F5652D],bytes.fromhex('493988f8320000'))
  self.assertEqual(a.DIRECT_E8[0x02F56536],0x030CFAC4)

 def test_offline_counterexample_pointer_ABA(self):
  out=a.simulate_hypothetical_sequence(refresh_before_tick=True,recycle_same_address=True,old_tick_enabled=True)
  self.assertTrue(out['fanout'])
  self.assertTrue(out['cross_epoch'])
  self.assertTrue(out['same_address_as_creation'])
  self.assertNotEqual(out['task_epoch'],out['current_group_epoch'])

 def test_offline_counterexample_new_pointer(self):
  out=a.simulate_hypothetical_sequence(refresh_before_tick=True,recycle_same_address=False,old_tick_enabled=True)
  self.assertTrue(out['cross_epoch'])
  self.assertFalse(out['same_address_as_creation'])

 def test_offline_control_same_group_no_refresh(self):
  out=a.simulate_hypothetical_sequence(refresh_before_tick=False,recycle_same_address=True,old_tick_enabled=True)
  self.assertTrue(out['fanout'])
  self.assertFalse(out['cross_epoch'])

 def test_offline_control_old_task_retired(self):
  out=a.simulate_hypothetical_sequence(refresh_before_tick=True,recycle_same_address=True,old_tick_enabled=False)
  self.assertFalse(out['fanout'])
  self.assertFalse(out['cross_epoch'])

 def test_wrong_binary_fails_closed_without_reading_bytes(self):
  class Wrong:
   sha='wrong'
   closed=False
   def close(self):self.closed=True
  fake=Wrong()
  with patch.object(a,'StrictPE',return_value=fake):
   with self.assertRaisesRegex(ValueError,'WRONG_EXE_SHA'):
    a.audit(Path('not-a-game.exe'))
  self.assertTrue(fake.closed)

 @unittest.skipUnless(os.environ.get('WH3_903_EXE'),'Original EXE not stored in public GitHub CI')
 def test_real_original_executable(self):
  result=a.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual((result['code_opcode_and_objdump_starts'],result['direct_E8_edges'],result['typed_vtable_slots']),(91,19,3))
  self.assertFalse(result['old_task_survives_group_rebuild_in_actual_shift_proven'])
  self.assertFalse(result['native_patch_authorized'])

if __name__=='__main__':unittest.main()
