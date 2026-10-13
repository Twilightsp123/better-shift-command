"""Native v+0x348 member task factory and explicit mode lineage contracts."""
import os,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(HERE))
import audit_member_timer_mode_lineage as m
from audit_wh3_full_native_chain import StrictPE

class NativeMemberTimerModeLineage(unittest.TestCase):
 def test_exact_new_original_opcode_count_and_caller_edges(self):
  self.assertEqual(len(m.PINS),35)
  self.assertEqual(len(m.EDGES),9)
  self.assertEqual(len(m.VTABLES),18)
  self.assertEqual(m.PINS[0x02d99e64],'0fb64202')
  self.assertEqual(m.PINS[0x02d99e68],'884102')
  self.assertEqual(m.PINS[0x032638d7],'c6410200')
  self.assertEqual(m.EDGES[0x02f5f20e],0x02d99e58)
  self.assertEqual(m.EDGES[0x0306b53b],0x02f5f1e8)
 def test_both_native_member_types_include_same_timer_and_all_action_slots(self):
  for vtbl in (0x038fd658,0x03910500):
   self.assertEqual(m.VTABLES[vtbl+0x348],0x0306b510)
   self.assertEqual(m.VTABLES[vtbl+0x368],0x0306b9f0)
   self.assertEqual(m.VTABLES[vtbl+0x4b0],0x03069844)
   self.assertEqual(m.VTABLES[vtbl+0x580],0x0306a990)
   self.assertEqual(m.VTABLES[vtbl+0x5b8],0x0306a8c0)
   self.assertEqual(m.VTABLES[vtbl+0x5f0],0x0306b0f8)
 def test_task_callbacks_are_one_typed_vtable_not_different_player_buttons(self):
  self.assertEqual(m.VTABLES[0x03906c88],0x02f63b38)
  self.assertEqual(m.VTABLES[0x03906c90],0x02f7301c)
  self.assertEqual(m.VTABLES[0x03906c98],0x02f83868)
  self.assertEqual(m.PINS[0x02f73061],'e8526b0000')
  self.assertEqual(m.PINS[0x02f838b6],'e8fd62ffff')
  self.assertEqual(m.EDGES[0x02f73061],0x02f79bb8)
  self.assertEqual(m.EDGES[0x02f838b6],0x02f79bb8)
 def test_task_mode_routes_to_two_different_member_calls(self):
  self.assertEqual(m.PINS[0x02f79bcd],'385142')
  self.assertEqual(m.PINS[0x02f79bd0],'7473')
  self.assertEqual(m.PINS[0x02f79c3d],'ff9080050000')
  self.assertEqual(m.PINS[0x02f79cb6],'ff90b0040000')
  self.assertEqual(m.PINS[0x02f79e5c],'ff90f0050000')
 def test_member_4b0_reads_timer_before_replacing_action(self):
  self.assertEqual(m.PINS[0x030698b7],'80bbc005000001')
  self.assertEqual(m.PINS[0x030698c0],'488d8ba8040000')
  self.assertEqual(m.PINS[0x030698ca],'ff9080000000')
  self.assertEqual(m.EDGES[0x03069910],0x02db0a10)
  self.assertEqual(m.EDGES[0x03069924],0x0304e5d4)
 def test_zero_descriptor_selects_a_third_not_RMB_specific_action_subclass(self):
  self.assertEqual(m.PINS[0x032638d7],'c6410200')
  self.assertEqual(m.PINS[0x02d99e64],'0fb64202')
  self.assertEqual(m.PINS[0x02d99e68],'884102')
  self.assertEqual(m.PINS[0x0304e5e9],'488d0518eca700')
  self.assertEqual(m.PINS[0x0304e5f0],'488903')
  self.assertEqual(m.VTABLES[0x03acd208],0x03052f30)
  self.assertEqual(m.VTABLES[0x03acd210],0x0307c388)
  self.assertEqual(m.VTABLES[0x03acd218],0x0308279c)
  self.assertNotEqual(m.VTABLES[0x03acd210],0x032599c8)
  self.assertNotEqual(m.VTABLES[0x03acd210],0x03259950)

 def test_wrong_binary_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'wrong.exe';old=b'MZ'+b'NOT_WH3'*100;p.write_bytes(old)
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):StrictPE(p)
   self.assertEqual(p.read_bytes(),old)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Exact original EXE excluded from public CI')
 def test_actual_original_exe_mode_lineage(self):
  result=m.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(result['guarded_x64_instruction_starts'],35)
  self.assertEqual(result['verified_E8_edges'],9)
  self.assertEqual(result['typed_vtable_entries'],18)
  self.assertFalse(result['queued_shift_or_RMB_identity_proven'])
  self.assertFalse(result['native_crowding_fix_authorized'])
if __name__=='__main__':unittest.main()
