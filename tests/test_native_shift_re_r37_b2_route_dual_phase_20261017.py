#!/usr/bin/env python3
"""R37 new-WH3-EXE read-only regression tests; synthetic cases are not gameplay traces."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AUDITS=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(AUDITS))
import audit_r37_b2_route_dual_phase_20261017 as a

class B2RouteDualPhase(unittest.TestCase):
    def test_manifest_inventory(self):
        groups=a.read_manifest()
        self.assertEqual(len(groups),12)
        self.assertEqual(sum(len(pins) for (_,pins) in groups.values()),183)
    def test_calls_and_controls(self):
        self.assertEqual((len(a.EXPECTED_CALLS),len(a.EXPECTED_JUMPS)),(23,9))
    def test_B2_virtual_methods_typed(self):
        self.assertEqual((a.B2_TABLE,a.B2_UPDATE,a.B2_TICK),
                         (0x03AE5800,0x03276970,0x032863A0))
    def test_converter_route_pointer_to_ctor(self):
        self.assertEqual(a.EXPECTED_CALLS[0x02F545DA],a.NODE_BUILDER)
        self.assertEqual(a.EXPECTED_CALLS[0x02F54613],0x03268DD4)
        self.assertEqual(a.EXACT_ASM[0x03268E20], 'mov    QWORD PTR [rcx+0x28],rdx')
        self.assertEqual(a.EXACT_ASM[0x03268D80], 'mov    QWORD PTR [rbx+0x60],rax')
    def test_volatile_r11_helper_scope(self):
        self.assertEqual(a.EXACT_ASM[0x030C861C], 'mov    r10,rcx')
        self.assertEqual(a.EXPECTED_CALLS[0x03268D40],0x030C861C)
    def test_node_ref_publication_before_B2_ctor(self):
        self.assertEqual(a.EXPECTED_CALLS[0x02F545EB],0x02F3BB44)
        self.assertEqual(a.EXACT_ASM[0x02F3BBB8], 'inc    DWORD PTR [rdx+0x4]')
        self.assertEqual(a.EXACT_ASM[0x02F3BBBF], 'mov    QWORD PTR [rax+0x270],rcx')
        self.assertEqual(a.EXACT_ASM[0x0301E8A2], 'dec    DWORD PTR [rax+0x4]')
    def test_both_routes_share_one_sender(self):
        self.assertEqual(a.EXPECTED_CALLS[0x032769F2],a.SENDER)
        self.assertEqual(a.EXPECTED_CALLS[0x03286445],a.SENDER)
    def test_direct_route_phase_eligible(self):
        self.assertEqual(a.phase_case(True,False,False), 'VIRTUAL_08_DIRECT_PACKET_CANDIDATE')
    def test_direct_route_does_not_imply_duplicate(self):
        self.assertEqual(a.phase_case(True,True,True,already_sent=True), 'SKIP_SECOND_CALL_ALREADY_SENT')
    def test_initial_route_absent_no_node(self):
        self.assertEqual(a.phase_case(False,False,False),'NO_ROUTE_NODE_YET')
    def test_node_unready_does_not_fanout(self):
        self.assertEqual(a.phase_case(False,True,False),'NODE_NOT_READY')
    def test_deferred_route_eligible_only_with_ready_node(self):
        self.assertEqual(a.phase_case(False,True,True),'VIRTUAL_10_DEFERRED_PACKET_CANDIDATE')
    def test_member_receiver_has_further_individual_gates(self):
        self.assertEqual(a.EXACT_ASM[0x03070A87],'test   BYTE PTR [rdx+0x50],0x20')
        self.assertEqual(a.EXACT_ASM[0x03070B2F],'mov    eax,DWORD PTR [rdi+0x104]')
    def test_wrong_exe_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'wrong.exe'; f.write_bytes(b'NO_GAME_EXE')
            for flags in ([],['-O']):
                r=subprocess.run([sys.executable,*flags,str(a.__file__),'--exe',str(f)],
                    capture_output=True,text=True,timeout=20)
                self.assertNotEqual(r.returncode,0)
            self.assertEqual(f.read_bytes(),b'NO_GAME_EXE')
    def test_game_exe_overwrite_refused(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'original.exe';f.write_bytes(b'do-not-touch')
            r=subprocess.run([sys.executable,str(a.__file__),'--exe',str(f),'--out',str(f)],
                capture_output=True,text=True,timeout=20)
            self.assertNotEqual(r.returncode,0)
            self.assertEqual(f.read_bytes(),b'do-not-touch')
    @unittest.skipUnless(os.getenv('WH3_CURRENT_EXE'), 'private new EXE absent in public CI')
    def test_real_updated_game_exe(self):
        r=a.audit(Path(os.environ['WH3_CURRENT_EXE']))
        self.assertEqual(r['sha256'],a.SHA)
        self.assertEqual((r['full_pinned_instruction_starts'],r['direct_e8_target_checks'],
                r['control_transfer_target_checks'],r['B2_vtable_slots_checked']), (183,23,9,2))
        self.assertFalse(r['route_pointer_conflict_between_same_shift_members_observed'])
        self.assertFalse(r['shift_crowding_root_cause_proven'])
        self.assertFalse(r['gameplay_patch_authorized'])

if __name__=='__main__':unittest.main()
