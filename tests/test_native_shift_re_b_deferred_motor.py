"""Synthetic branching and original-EXE-pin tests. NEVER a gameplay fix claim."""
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

SRC=Path(__file__).resolve().parents[1]/"maintenance_tools"/"native_shift_re"
sys.path.insert(0,str(SRC))
import audit_b_deferred_motor as b

def member_code(group_record_enabled,local_mode,record,packet_flag=False):
    """Limited 0x3265BEB-0x3265C3F state model, NOT engine emulation."""
    code=local_mode
    if group_record_enabled:
        if record in (5,7):code=record+0x62
        elif record==6:code=0x68
        elif record==8:code=5
        elif record==9:code=6
    if packet_flag and code in (0x67,0x68,0x69):code=0
    return code

def member_task_dispatch(code,flag_0x10=False,local_gate=0):
    if code not in (0x67,0x68,0x69) or flag_0x10:return "member_v568"
    return "member_v580" if local_gate==0 else "member_v568"

class DeferredMotorContracts(unittest.TestCase):
    def test_native_guarded_sites_count(self):
        self.assertEqual(len(b.PINS),46)
        self.assertEqual(len(b.VTABLES),3)
        self.assertEqual(len(b.DIRECT),8)
    def test_per_member_action_codes_67_69(self):
        self.assertEqual(member_code(True,0,5),0x67)
        self.assertEqual(member_code(True,0,6),0x68)
        self.assertEqual(member_code(True,0,7),0x69)
    def test_packet_gate_can_change_action_code(self):
        self.assertEqual(member_code(True,5,5,True),0)
        self.assertEqual(member_code(True,5,5,False),0x67)
    def test_two_members_can_take_different_action_classes(self):
        a=member_code(False,0x67,7)
        c=member_code(False,0x05,7)
        self.assertEqual(member_task_dispatch(a),"member_v580")
        self.assertEqual(member_task_dispatch(c),"member_v568")
    def test_distance_and_mode_gate_negative_controls(self):
        self.assertEqual(member_task_dispatch(0x68,local_gate=1),"member_v568")
        self.assertEqual(member_task_dispatch(0x69,flag_0x10=True),"member_v568")
        self.assertEqual(member_task_dispatch(0x69),"member_v580")
    def test_task_74_is_packet_34_after_copy_to_40(self):
        self.assertEqual(b.PINS["packet_copy_source_34"][1],"8b4234")
        self.assertEqual(b.PINS["packet_copy_dest_34"][1],"894134")
        self.assertEqual(b.PINS["task_action_74_read"][1],"8b4174")
    def test_member_subaction_uses_distinct_vtables(self):
        self.assertEqual(b.VTABLES[0x03913808+0x10],0x0325e294)
        self.assertEqual(b.VTABLES[0x03add278+0x10],0x0325d9e0)
    def test_common_tick_calls_embedded_action_without_forcing_both_modes(self):
        self.assertEqual(b.PINS["member_tick_subaction_owner"][1],"488d8f28030000")
        self.assertEqual(b.DIRECT[0x30822d2],0x3080f4c)
        self.assertEqual(b.PINS["subaction_owner_flag_gate"][1],"80b95401000001")
        self.assertEqual(b.PINS["subaction_v10_update"][1],"ff5010")
    def test_native_goal_writer_is_conditional_not_immediate(self):
        self.assertEqual(b.DIRECT[0x0325ea85],0x03071e04)
        self.assertEqual(b.DIRECT[0x03071e86],0x03071f20)
        self.assertEqual(b.DIRECT[0x03119687],0x03102ca4)
    def test_wrong_executable_is_refused_without_writes(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"fake.exe";data=b"MZ"+b"bad binary"*100
            p.write_bytes(data)
            with self.assertRaisesRegex(ValueError,"SHA_MISMATCH"):
                b.verify(p)
            self.assertEqual(p.read_bytes(),data)
    def test_static_only_no_patch_enabled(self):
        s=(SRC/"audit_b_deferred_motor.py").read_text(encoding="utf8")
        self.assertNotIn("WriteProcessMemory",s)
        self.assertNotIn("VirtualProtect(",s)
        self.assertIn('"patch_authorized":False',s)
    @unittest.skipUnless(os.environ.get("WH3_903_EXE"),"original EXE absent in GitHub CI")
    def test_exact_original_exe(self):
        r=b.verify(Path(os.environ["WH3_903_EXE"]))
        self.assertEqual(r["member_class_census"],38)
        self.assertEqual(r["pinned_opcode_instructions"],46)
        self.assertFalse(r["patch_authorized"])

if __name__=="__main__":unittest.main()
