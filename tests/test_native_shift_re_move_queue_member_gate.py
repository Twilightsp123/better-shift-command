"""Fail-closed MOVE queue-to-member geometry gates; no gameplay patch."""
import os,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'))
import audit_move_queue_member_gate as a

class NativeQueueMemberGate(unittest.TestCase):
 def test_exact_slot_arithmetic(self):
  self.assertEqual(0x278+0x10+0x18,0x2A0)
  self.assertEqual(0x278+0x2D10,0x2F88)
  self.assertEqual(0x278+0x2D14,0x2F8C)
  self.assertEqual(0x9*0x20,0x120)
 def test_queue_and_getter_structural_anchor_instructions(self):
  self.assertEqual(a.PINS[0x030326B4],'488d8b78020000')
  self.assertEqual(a.PINS[0x030326CE],'488d4b18')
  self.assertEqual(a.PINS[0x03039C9C],'488dbaa0020000')
  self.assertEqual(a.PINS[0x03039C96],'8b828c2f0000')
  self.assertEqual(a.PINS[0x03039C8D],'83ba882f000000')
 def test_MOVE_gate_not_same_as_all_native_slots(self):
  self.assertEqual(a.MOVE_VTABLE,0x0390B4F0)
  self.assertEqual(a.MOVE_B0_B8_FALSE,0x008D3330)
  self.assertEqual(a.PINS[0x03039CB4],'ff90b8000000')
  self.assertEqual(a.PINS[0x03039BF6],'ff90b0000000')
 def test_fifth_argument_world_reference_is_caller_stack_pointer(self):
  self.assertEqual(a.PINS[0x03046015],'4889442420')
  self.assertEqual(a.PINS[0x0301073F],'488da8d8feffff')
  self.assertEqual(a.PINS[0x03010840],'4c8bad50010000')
  self.assertEqual(0x150-0x128,0x28)
  self.assertEqual(a.CALL_EDGES[0x0304601A],0x03010724)
 def test_two_separate_packet_constructors_for_three_v388_cases(self):
  self.assertEqual(a.CALL_EDGES[0x03010ACD],0x02F5FCAC)
  self.assertEqual(a.CALL_EDGES[0x03010D5A],0x02F5FE28)
  self.assertEqual(a.CALL_EDGES[0x03011036],0x02F5FCAC)
  self.assertEqual(len(a.DISPATCHES_388),3)
  self.assertEqual(len(a.DISPATCHES_380),2)
 def test_all_five_calls_to_conditional_helper_covered(self):
  got={s for s,target in a.CALL_EDGES.items() if target==0x030A48A4}
  self.assertEqual(got,{0x03010AE4,0x03010BEE,0x03010D71,0x0301104D,0x030111AF})
  self.assertEqual(len(a.RESULT_GATES),3)
 def test_packet_field_is_optional_float_not_arbitrary_member_goal(self):
  self.assertEqual(a.LEAF_SITES[0x02F5FD1F],'c74158000080bf')
  self.assertEqual(a.LEAF_SITES[0x02F5FE9F],'c74158000080bf')
  self.assertEqual(a.PINS[0x03010B06],'804d6c20')
  self.assertEqual(a.PINS[0x030A4A4D],'c6855c01000001')
 def test_guard_wrong_exe_rejects(self):
  class Wrong:
   sha='not-the-original';closed=False
   def close(self):self.closed=True
  fake=Wrong()
  with patch.object(a,'StrictPE',return_value=fake):
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
    a.audit(Path('bad.exe'))
  self.assertTrue(fake.closed)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Private original WH3 binary not in public CI')
 def test_exact_original_executable(self):
  r=a.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(r['opcodes_and_objdump_instruction_starts'],94)
  self.assertEqual(r['direct_E8_edges'],17)
  self.assertEqual((r['indirect_v388_dispatches'],r['indirect_v380_dispatches']),(3,2))
  self.assertFalse(r['native_patch_authorized'])
  self.assertFalse(r['special_member_virtual388_always_executed_for_SHIFT'])
if __name__=='__main__':unittest.main()
