"""Synthetic contracts for native route/member dispatch; not WH3 motion evidence."""
import sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"maintenance_tools"/"native_shift_re"))
from audit_903_member_route_virtual import GUARDS,CALLS,verify

class MemberRouteDispatchTests(unittest.TestCase):
    def test_static_guard_and_call_counts(self):
        self.assertEqual(len(GUARDS),9)
        self.assertEqual(len(CALLS),2)
    def test_original_native_route_target(self):
        self.assertEqual(CALLS["member_to_unit_route"][1],0x0301287C)
    def test_member_virtual_site(self):
        self.assertEqual(GUARDS["member_virtual_0xC8"][1],"ff90c8000000")
    def test_fail_closed_without_exact_executable(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"synthetic.exe";p.write_bytes(b"MZ")
            with self.assertRaisesRegex(ValueError,"EXE_SHA256_MISMATCH"):verify(p)
            self.assertEqual(p.read_bytes(),b"MZ")

if __name__=="__main__":
    unittest.main()
