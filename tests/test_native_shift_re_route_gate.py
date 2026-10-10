"""Synthetic-only invariants for the 9.0.3 route gate forensic verifier."""
import mmap
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "maintenance_tools" / "native_shift_re"))
from verify_903_route_gate import (
    PINNED_EXE_SHA256, ORIGINAL_GUARDS, CALL_EDGES, decode_e8_target,
    branch_flag_result, read_executable_rva, verify,
)
from test_native_shift_re import make_pe
from scout_pe import parse_pe


class RouteGateVerifierTests(unittest.TestCase):
    def test_exact_hash_contract(self):
        self.assertEqual(PINNED_EXE_SHA256,
            "518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a")

    def test_46_machine_guard_sites_and_six_edges(self):
        self.assertEqual(len(ORIGINAL_GUARDS.strip().splitlines()), 46)
        self.assertEqual(len(CALL_EDGES), 6)
        self.assertTrue(all(":" in line for line in ORIGINAL_GUARDS.strip().splitlines()))

    def test_route_return_and_mode_gate(self):
        for route_al in (0, 1):
            for mode in (0, 1, 2, 3, 100):
                self.assertEqual(branch_flag_result(route_al, mode),
                                 int(bool(route_al) and mode >= 2))

    def test_e8_target_decode_and_bad_opcode(self):
        self.assertEqual(decode_e8_target(0x1000, b"\xe8\x0b\x00\x00\x00"), 0x1010)
        with self.assertRaisesRegex(ValueError, "NOT_A_DIRECT_E8_CALL"):
            decode_e8_target(0x1000, b"\x90\x00\x00\x00\x00")

    def test_executable_section_only(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "synthetic.exe"
            p.write_bytes(make_pe(executable=b"\x90\xc3", data=b"\x01\x02"))
            with p.open("rb") as fd, mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                sections = parse_pe(mm)["sections"]
                self.assertEqual(read_executable_rva(mm, sections, 0x1000, 2), b"\x90\xc3")
                with self.assertRaisesRegex(ValueError, "RVA_NOT_EXECUTABLE"):
                    read_executable_rva(mm, sections, 0x2000, 2)

    def test_wrong_sha_fails_closed_and_preserves_input(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "synthetic.exe"
            original = make_pe()
            p.write_bytes(original)
            with self.assertRaisesRegex(ValueError, "EXE_SHA256_MISMATCH"):
                verify(p)
            self.assertEqual(p.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
