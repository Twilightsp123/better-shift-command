"""Offline native B distance gate controls and optional exact original binary."""
import os,sys,tempfile,unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(SRC))
import audit_member_goal_distance_split as a
class NativeDeferredDistanceGate(unittest.TestCase):
 def test_distance_less_than_five_takes_v580_if_flag1(self):
  self.assertEqual(a.select_actor_action(0x68,1,4,0),'v580')
 def test_equal_five_does_not_clear_flag(self):
  self.assertEqual(a.select_actor_action(0x68,1,5,0),'v568')
 def test_more_than_five_keeps_v568(self):
  self.assertEqual(a.select_actor_action(0x68,1,6,0),'v568')
 def test_far_with_flag_zero_remains_v580(self):
  self.assertEqual(a.select_actor_action(0x68,0,6,0),'v580')
 def test_non_special_action_is_negative_control(self):
  self.assertEqual(a.select_actor_action(0x66,1,4,0),'v568')
 def test_special_disabled_negative_control(self):
  self.assertEqual(a.select_actor_action(0x68,1,4,0,True),'v568')
 def test_same_packet_two_members_may_split(self):
  self.assertNotEqual(a.select_actor_action(0x68,1,4,0),
                      a.select_actor_action(0x68,1,6,0))
 def test_original_opcode_inventory(self):
  self.assertEqual(len(a.GUARDS),56)
  self.assertEqual(len(a.EDGES),22)
  self.assertEqual(a.THRESHOLD_RVA,0x3942d74)
  self.assertEqual(a.GUARDS['near_flag_clear'],(0x2f7a08e,'44894378'))
 def test_both_actor_action_classes_can_reach_original_goal_writer(self):
  self.assertEqual(a.EDGES[0x325ea85],0x3071e04)
  self.assertEqual(a.EDGES[0x325da69],0x3255ff0)
  self.assertEqual(a.EDGES[0x3256161],0x3071e04)
 def test_far_action_has_one_shot_goal_guard_not_permanent_stale_goal(self):
  self.assertEqual(a.GUARDS['far_action_one_shot_guard'][1],'80b99000000001')
  self.assertEqual(a.GUARDS['far_action_checks_motor_state'][1],'39b810070000')
  self.assertEqual(a.GUARDS['far_action_constructor_clears_issued'][1],'664183a29000000000')
  self.assertEqual(a.GUARDS['far_action_marks_issued'][1],'c6839000000001')
 def test_native_receiver_defers_without_old_action_disposal(self):
  self.assertEqual(a.GUARDS['RMB_packet_26_immediate'][1],'c6435026')
  self.assertEqual(a.GUARDS['receiver_packet_bit20_check'][1],'f6425020')
  self.assertEqual(a.GUARDS['deferred_returns_before_action_reset'][1],'e975010000')
  self.assertEqual(a.EDGES[0x306ba5b],0x2f5f7c8)
  self.assertEqual(a.EDGES[0x306bbae],0x2db0a10)
 def test_deferred_activation_later_resets_action(self):
  self.assertEqual(a.EDGES[0x306a9a7],0x2db0a10)
  self.assertEqual(a.EDGES[0x306a913],0x2db0a10)
  self.assertNotEqual(a.GUARDS['deferred_new_task_address'][0],
                      a.GUARDS['direct_action_reset_address'][0])
 def test_refuse_wrong_exe(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'wrong.exe'
   data=b'MZ'+b'NOT_WARHAMMER'*16
   p.write_bytes(data)
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
    a.verify_original(p)
   self.assertEqual(data,p.read_bytes())
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Public CI does not have original EXE')
 def test_original_9_0_3(self):
  r=a.verify_original(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(r['horizontal_squared_distance_gate'],25.)
  self.assertEqual(r['verified_call_edges'],22)
  self.assertFalse(r['safe_patch_authorized'])
if __name__=='__main__':unittest.main()
