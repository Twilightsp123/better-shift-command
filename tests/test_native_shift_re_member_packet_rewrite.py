"""Native original member packet constructor/post-ctor mutation contracts."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
SRC=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(SRC))
import audit_member_packet_post_ctor_rewrite as m

class NativePacketRewrittenAfterConstructor(unittest.TestCase):
    def test_strict_original_byte_sites_not_a_guess(self):
        self.assertEqual(len(m.PINS),41)
        self.assertEqual(len(m.CALLS),8)
        self.assertEqual(m.PINS['packet_plus50_clear_bit2'],(0x03284B65,'24fb'))
        self.assertEqual(m.PINS['packet_plus44_zero_low32'],(0x03284B75,'894d24'))
        self.assertEqual(m.PINS['packet_local'],(0x03284B31,'488d4de0'))
        self.assertEqual(m.PINS['member_packet_v368'],(0x03284B7B,'ff9068030000'))

    def test_this_group_task_is_not_B_cached_subtype(self):
        self.assertEqual(m.VTABLES,{0x03ADD618:0x03282E48})
        self.assertNotEqual(0x03ADD608,0x03AE00E8)
        self.assertEqual(m.CALLS[0x03265B0A],0x03284304)
        self.assertEqual(m.CALLS[0x03282F0F],0x03284304)

    def test_06_constructor_can_legitimately_leave_02_byte(self):
        self.assertEqual(m.rewritten_flag(0x06,0),0x02)
        self.assertEqual(m.rewritten_flag(0x07,0),0x03)
        self.assertEqual(m.rewritten_flag(0x16,0),0x12)
        self.assertEqual(m.rewritten_flag(0x06,1),0x03)

    def test_exact_group_tick_reissues_are_conditional_not_shift_specific(self):
        self.assertEqual(len(m.PERIOD_CONSTANTS),3)
        self.assertEqual(m.PINS['tick_group_clock'][1],'8b8198000000')
        self.assertEqual(m.PINS['tick_global_rate'][1],'8b059a43a800')
        self.assertEqual(m.PINS['tick_not_due_branch'][1],'760f')
        self.assertEqual(m.PINS['tick_store_elapsed'][1],'f30f114b58')
        self.assertFalse(m.periodic_sender_due(10,100,0))
        self.assertTrue(m.periodic_sender_due(11,100,0))
        self.assertFalse(m.periodic_sender_due(11,100,1.1))
        with self.assertRaisesRegex(ValueError,'BAD_GLOBAL_RATE'):
            m.periodic_sender_due(11,0,0)
    def test_missing_flag_or_bad_input_rejected(self):
        with self.assertRaisesRegex(ValueError,'NOT_KNOWN_CONSTRUCTOR'):
            m.rewritten_flag(0x02,0)
        with self.assertRaisesRegex(ValueError,'NOT_BYTE'):
            m.rewritten_flag(0x06,-1)

    def test_original_EXE_guard_and_user_trace_if_attached(self):
        exe=os.getenv('WH3_903_EXE')
        if not exe:self.skipTest('Original EXE not included in public CI')
        evidence=m.audit(Path(exe),Path(os.getenv('BSC_REAL_TRACE_JSONL'))
                         if os.getenv('BSC_REAL_TRACE_JSONL') else None)
        self.assertEqual(evidence['opcode_guards'],len(m.PINS))
        self.assertEqual(evidence['e8_edges'],8)
        self.assertTrue(evidence['old_claim_that_flag02_proves_no_02F5F8DC_source_is_invalid'])
        self.assertFalse(evidence['safe_native_patch_authorized'])

    def test_private_trace_fingerprint_optional(self):
        trace=os.getenv('BSC_REAL_TRACE_JSONL')
        if not trace:self.skipTest('Private trace not supplied to CI')
        stats=m.inspect_trace(Path(trace))
        self.assertEqual(stats['recorded_deferred_receives'],28)
        for count in stats['field_matches'].values():self.assertEqual(count,28)
        self.assertFalse(stats['original_sender_return_address_recorded'])

    def test_wrong_executable_fails_before_any_rva_read_or_write(self):
        from audit_wh3_full_native_chain import StrictPE
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'wrong.exe';old=b'MZ'+b'OTHER_GAME'*100
            p.write_bytes(old)
            with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
                StrictPE(p)
            self.assertEqual(p.read_bytes(),old)

    def test_patch_is_not_enabled_by_static_compatibility(self):
        t=(SRC/'audit_member_packet_post_ctor_rewrite.py').read_text()
        self.assertIn("'safe_native_patch_authorized':False",t)
        self.assertIn("'historical_sender_identity':None",t)
        self.assertNotIn('WriteProcessMemory',t)

if __name__=='__main__':unittest.main()
