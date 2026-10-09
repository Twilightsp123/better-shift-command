"""Synthetic-only contracts for the exact-file MOVE state verifier.

No Warhammer3.exe needed in CI; only real user-owned EXE can pass the pinned
SHA and machine-code gate when run separately.
"""
import mmap
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "maintenance_tools" / "native_shift_re"
sys.path.insert(0, str(SCRIPTS))
from verify_903_move_state_origin import GUARDS, FLOATS, TARGET_SHA, pe_read, verify
from test_native_shift_re import make_pe
from scout_pe import parse_pe


class MoveStateOriginToolContracts(unittest.TestCase):
    def test_exact_build_pinning_not_legacy(self):
        self.assertEqual(len(TARGET_SHA), 64)
        self.assertEqual(TARGET_SHA, "518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a")

    def test_25_selected_machine_instruction_guards(self):
        self.assertEqual(len(GUARDS), 25)
        self.assertEqual(len(FLOATS), 2)
        self.assertTrue(all(len(bytes.fromhex(hx)) >= 3 for _, hx in GUARDS.values()))

    def test_frame_writeback_alias_arithmetic(self):
        # r14 = &MOVE+0xA0; address in task-init +0x50
        self.assertEqual(-0xB8 - 0x70, -0x1B8 + 0x40 + 0x50)

    def test_unpinned_synthetic_executable_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "Warhammer3.exe"
            p.write_bytes(make_pe(executable=b"\x90\x90\xc3"))
            before = p.read_bytes()
            with self.assertRaisesRegex(ValueError, "wrong EXE SHA256"):
                verify(p)
            self.assertEqual(before, p.read_bytes())

    def test_byte_reader_honors_section_execute_flags(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "fixture.exe"
            p.write_bytes(make_pe(executable=b"\xcc\xc3", data=b"\x11\x22"))
            with p.open("rb") as fd, mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                sections = parse_pe(mm)["sections"]
                self.assertEqual(pe_read(mm, sections, 0x1000, 2, True), b"\xcc\xc3")
                with self.assertRaisesRegex(ValueError, "not executable"):
                    pe_read(mm, sections, 0x2000, 2, True)
                self.assertEqual(pe_read(mm, sections, 0x2000, 2, False), b"\x11\x22")

    def test_out_of_range_reader_rejects(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "fixture.exe"
            p.write_bytes(make_pe())
            with p.open("rb") as fd, mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                sections = parse_pe(mm)["sections"]
                with self.assertRaisesRegex(ValueError, "not mapped"):
                    pe_read(mm, sections, 0x500000, 16, True)


if __name__ == "__main__":
    unittest.main()
