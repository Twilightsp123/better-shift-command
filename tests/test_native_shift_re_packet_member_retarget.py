"""Exact native per-member heading/position postprocessing, no active game hooks."""
import os, sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit_packet_member_retarget as a

class NativeMemberRetarget(unittest.TestCase):
    def test_sender_constructor_and_fifth_arg_enable_path(self):
        self.assertEqual(a.PINS[0x030D54EB], 'c644242001')
        self.assertEqual(a.PINS[0x030D54F7], '450fb74822')
        self.assertEqual(a.E8[0x030D54FC],0x02F5F868)
        self.assertEqual(a.PINS[0x02F5F8C4],'384c2450')
        self.assertEqual(a.E8[0x02F5F8CD],0x02F72520)
    def test_packet_tag_and_two_forced_branch_bits(self):
        self.assertEqual(a.PINS[0x02F5F8BD],'c6435026')
        self.assertTrue(0x26 & 0x20)
        self.assertTrue(0x26 & 0x02)
        self.assertEqual(a.PINS[0x02F72526],'80495102')
        self.assertEqual(a.PINS[0x0306BA65],'f6425102')
        self.assertEqual(a.PINS[0x0306BA2F],'f6425020')
    def test_heading_can_be_rewritten_by_member_scalars(self):
        self.assertEqual(a.PINS[0x02F5F8AD],'6644894b40')
        self.assertEqual(a.E8[0x02F72542],0x0307F478)
        self.assertEqual(a.PINS[0x02F7254A],'66890b')
        self.assertEqual(a.PINS[0x0307F494],'f30f1089840900')
        self.assertEqual(a.PINS[0x0307F49C],'8b80cc360000')
    def test_heading_offset_symbolic_counterexamples_not_gameplay(self):
        self.assertAlmostEqual(a.symbolically_angle_offset(0.15,0),-5734.4,places=3)
        self.assertAlmostEqual(a.symbolically_angle_offset(1.0,0),8192.0,places=5)
        self.assertEqual(a.symbolically_angle_offset(0.15,1),0.0)
        self.assertEqual(a.symbolically_angle_offset(1.0,1),0.0)
    def test_concrete_member_type_ctor_initializes_inputs(self):
        self.assertEqual(a.CTOR_RIP_LEA,0x0304DC70)
        self.assertEqual(a.MEMBER_VTABLE,0x0390D4F8)
        self.assertEqual(a.PINS[0x0304DDE6],'4c89b3e8020000')
        self.assertEqual(a.PINS[0x0304E20E],'f30f1183840900')
    def test_original_position_correction_is_not_bypassed(self):
        self.assertEqual(a.E8[0x0306BA75],0x0307F5C8)
        self.assertEqual(a.E8[0x0307F5E8],0x0307F690)
        self.assertEqual(a.E8[0x0307F6D6],0x0307F4E4)
        self.assertEqual(a.E8[0x0307F673],0x03107FD8)
    def test_record_validity_bit_not_directly_forwarded(self):
        self.assertEqual(a.PINS[0x030C2FB4],'c6412001')
        self.assertEqual(a.PINS[0x030C3030],'c6432000')
        self.assertEqual(a.PINS[0x02F5F88C],'498b4018')
    def test_expected_e8_count_and_guard_count(self):
        self.assertEqual(len(a.PINS),84)
        self.assertEqual(len(a.E8),11)
    def test_wrong_hash_fail_closed(self):
        class Wrong:
            sha='wrong'
            closed=False
            def close(self):self.closed=True
        inst=Wrong()
        with patch.object(a,'StrictPE',return_value=inst):
            with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
                a.audit(Path('/tmp/bad.exe'))
        self.assertTrue(inst.closed)
    @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Private original EXE not uploaded to public CI')
    def test_original_exe_same_binary_proof(self):
        result=a.audit(Path(os.getenv('WH3_903_EXE')))
        self.assertEqual(result['verified_instruction_starts'],84)
        self.assertEqual(result['verified_direct_E8'],11)
        self.assertFalse(result['native_patch_authorized'])
        self.assertTrue(result['packet_heading_overwritten_after_formation_strategy'])

if __name__=='__main__':unittest.main()
