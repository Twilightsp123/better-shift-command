"""Bounded successful handoff clear: exact EXE optional, synthetic negative cases."""
import os,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'))
import audit_queued_handoff_manager_clear as a
class NativeHandoffClear(unittest.TestCase):
 def test_census(self):
  self.assertEqual((len(a.PINS),len(a.E8),len(a.E9),len(a.BRANCH),len(a.VTABLE)),(72,11,1,6,6))
 def test_manager_alias_depends_on_existing_exact_audit(self):
  self.assertEqual(a.prior.SHA,a.SHA)
  self.assertEqual(a.PINS[0x030445B6],bytes.fromhex('488b4b08'))
 def test_three_source_gates(self):
  self.assertEqual(a.PINS[0x03044539],bytes.fromhex('83bb102d000001'))
  self.assertEqual(a.PINS[0x03044562],bytes.fromhex('ff5040'))
  self.assertEqual(a.PINS[0x03044596],bytes.fromhex('ff5038'))
 def test_typed_big_and_short_task_objects_differ(self):
  self.assertEqual(a.VTABLE[0x0390B530],0x03039FB0)
  self.assertEqual(a.VTABLE[0x0390B538],0x03040864)
  self.assertEqual(a.VTABLE[0x03ABBE30],0x008D3280)
 def test_success_order(self):
  self.assertLess(0x030445AB,0x030445B1)
  self.assertLess(0x030445B1,0x030445BC)
  self.assertLess(0x030445BC,0x030445CB)
  self.assertLess(0x030445CB,0x030445D3)
 def test_clear_call_has_zero_target(self):
  self.assertEqual(a.PINS[0x030445BA],bytes.fromhex('33d2'))
  self.assertEqual(a.E8[0x030445BC],0x02F4FD5C)
 def test_manager_guard_must_be_stated(self):
  self.assertEqual(a.PINS[0x02F4FD70],bytes.fromhex('80b95002000000'))
  self.assertEqual(a.BRANCH[0x02F4FD7C],(0x74,0x02F4FDD9))
 def test_original_retirement_updates_count(self):
  self.assertEqual(a.PINS[0x02F4FDC4],bytes.fromhex('ff8b40020000'))
  self.assertEqual(a.BRANCH[0x02F4FDD0],(0x77,0x02F4FD94))
 def test_unit_tick_order_and_rearm(self):
  self.assertEqual(a.E8[0x03043770],0x0304433C)
  self.assertEqual(a.E8[0x0304377C],0x03043520)
  self.assertEqual(a.PINS[0x03043635],bytes.fromhex('c6835002000001'))
 def test_next_activation_conditional(self):
  self.assertEqual(a.PINS[0x0304342E],bytes.fromhex('80b91801000001'))
  self.assertEqual(a.E8[0x0304345C],0x02F4FD5C)
 def test_successful_normal_reset_no_old_task(self):
  x=a.simulate(queue_count=2,provider_returns_old=True,successor_accepts=True,manager_enabled=True,old_tasks=['old'],next_activation_adds_task=True)
  self.assertEqual(x['remaining_old_short_tasks'],[])
  self.assertFalse(x['old_task_can_resume_by_later_top_pop'])
 def test_guard_zero_preserves_old_task(self):
  x=a.simulate(queue_count=2,provider_returns_old=True,successor_accepts=True,manager_enabled=False,old_tasks=['old'],next_activation_adds_task=True)
  self.assertTrue(x['cleanup_requested'])
  self.assertFalse(x['cleanup_accepted_by_manager'])
  self.assertEqual(x['remaining_old_short_tasks'],['old'])
 def test_failure_paths_are_outside_proof(self):
  for count,old,allow in ((1,True,True),(2,False,True),(2,True,False)):
   x=a.simulate(queue_count=count,provider_returns_old=old,successor_accepts=allow,manager_enabled=True,old_tasks=['old'],next_activation_adds_task=True)
   self.assertFalse(x['handoff_success_path'])
   self.assertEqual(x['remaining_old_short_tasks'],['old'])
 def test_signed_branch_decoder(self):
  self.assertEqual(a.branch_target(0x02F4FDD0,bytes.fromhex('77c2'),0x77),0x02F4FD94)
  self.assertEqual(a.branch_target(0x03044540,bytes.fromhex('0f868a000000'),0x0f86),0x030445D0)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'The original EXE is excluded from public CI')
 def test_real_game_exe(self):
  x=a.audit(Path(os.getenv('WH3_903_EXE')))
  self.assertEqual(x['checked_opcode_instruction_starts'],72)
  self.assertFalse(x['native_patch_authorized'])
if __name__=='__main__':unittest.main()
