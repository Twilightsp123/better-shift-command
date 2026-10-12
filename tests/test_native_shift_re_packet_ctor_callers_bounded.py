"""Bounded original native packet constructor direct-call source negative controls."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"maintenance_tools"/"native_shift_re"
sys.path.insert(0,str(SRC))
import audit_packet_ctor_callers_bounded as a
from audit_wh3_full_native_chain import StrictPE

class NativePacketConstructorSourceAudit(unittest.TestCase):
    def test_ordered_exact_native_signature(self):
        fragment=(
          b"\xe8\x82\xad\xcd\xff" +
          b"\x8a\x45\x30\x48\x8d\x55\xe0"+
          bytes.fromhex("806531fe") +
          bytes.fromhex("24fb") +
          bytes.fromhex("410ac633c98845304533c0488b03") +
          bytes.fromhex("894d24") +
          bytes.fromhex("488bcbff9068030000")
        )
        ok,off=a.bounded_signature_offsets(fragment)
        self.assertTrue(ok)
        self.assertEqual(off["clear_packet50_bit2"],16)
        self.assertEqual(off["member_v368_dispatch"],38)

    def test_nearby_but_absent_no_positive_fingerprint(self):
        ok,off=a.bounded_signature_offsets(bytes.fromhex("24fb894d24"))
        self.assertFalse(ok)
        self.assertIsNone(off["member_v368_dispatch"])

    def test_out_of_order_no_positive_fingerprint(self):
        reordered=b"".join(reversed([part for _,part in a.SIGNATURE]))
        self.assertFalse(a.bounded_signature_offsets(reordered)[0])

    def test_wrong_exe_denied_before_scan(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"wrong.exe";raw=b"MZ"+b"x"*512;f.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,"SHA_MISMATCH"):StrictPE(f)
            self.assertEqual(f.read_bytes(),raw)

    @unittest.skipUnless(os.getenv("WH3_903_EXE"),"Public CI lacks original EXE")
    def test_entire_original_binary_direct_call_census(self):
        result=a.audit(Path(os.environ["WH3_903_EXE"]))
        self.assertEqual(result["verified_all_native_constructor_E8"],43)
        self.assertEqual(result["constructor_groups"]["0x2f5f8dc"],20)
        self.assertEqual(result["constructor_groups"]["0x2f5f868"],8)
        self.assertEqual(result["constructor_groups"]["0x2f5f964"],15)
        self.assertEqual(result["generic_ctor_post_rewrite_4_stage_signature_count"],1)
        self.assertEqual(result["signature_matches"][0]["site"],"0x3284b55")
        self.assertIsNone(result["runtime_caller_in_historical_trace"])
        self.assertFalse(result["safe_native_patch_authorized"])

if __name__=="__main__":unittest.main()
