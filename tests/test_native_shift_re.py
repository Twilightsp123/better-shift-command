"""Offline, synthetic-only contracts; NOT WH3 native behavior validation."""
import hashlib
import json
import mmap
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from maintenance_tools.native_shift_re import scout_pe as scout


def make_pe(executable=b"", data=b"", machine=0x8664):
    """Minimal synthetic PE32+ with one .text and one non-exec .rdata section."""
    b = bytearray(0xA00)
    b[:2] = b"MZ"
    struct.pack_into("<I", b, 0x3C, 0x80)
    b[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HH", b, 0x84, machine, 2)
    struct.pack_into("<H", b, 0x80+20, 0xF0)
    optional = 0x80+24
    struct.pack_into("<H", b, optional, 0x20B)
    struct.pack_into("<Q", b, optional+24, 0x140000000)
    struct.pack_into("<I", b, optional+56, 0x4000)
    sec = optional + 0xF0
    b[sec:sec+8] = b".text\0\0\0"
    struct.pack_into("<IIII", b, sec+8, 0x200, 0x1000, 0x200, 0x400)
    struct.pack_into("<I", b, sec+36, 0x60000020)
    sec += 40
    b[sec:sec+8] = b".rdata\0\0"
    struct.pack_into("<IIII", b, sec+8, 0x200, 0x2000, 0x200, 0x600)
    struct.pack_into("<I", b, sec+36, 0x40000040)
    if len(executable) > 0x200 or len(data) > 0x200:
        raise ValueError("fixture region too long")
    b[0x400 : 0x400 + len(executable)] = executable
    b[0x600 : 0x600 + len(data)] = data
    return b


def make_map(sha, guard="488b0511223344488b", masks=None):
    d = {"game": {"version": "9.0.2", "sha256": sha}, "core": {
        "move": {"rva": "0x030351AC", "guard": guard, "role": "order_core", "required": True}
    }}
    if masks:
        d["core"]["move"]["normalization"] = {"mask_ranges": masks}
    return d


class PeContracts(unittest.TestCase):
    def test_readonly_scan_finds_executable_and_ignores_data(self):
        # Mask changes bytes 3:7; second occurrence in .rdata MUST be ignored.
        guard = bytes.fromhex("488b0511223344488b11223344556677")
        patched = bytes.fromhex("488b05aabbccdd488b11223344556677")
        binary = make_pe(b"\x90" * 20 + patched + b"\x90" * 5, guard)
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "Warhammer3.exe"
            exe.write_bytes(binary)
            old = make_map("0" * 64, guard=guard.hex(), masks=[[3,7]])
            before = hashlib.sha256(exe.read_bytes()).hexdigest()
            report = scout.inspect(exe, old, expected_sha256=before)
            after = hashlib.sha256(exe.read_bytes()).hexdigest()
            self.assertEqual(before, after)
            self.assertTrue(report["expected_hash_matches"])
            self.assertEqual(report["status"], "SHA_VERIFIED_BINARY_RESEARCH_ONLY")
            item = report["legacy_byte_similarity"]["move"]
            self.assertEqual(item["match_count"], 1)
            self.assertEqual(item["historical_similarity_matches"], [{"rva": "0x1014", "section": ".text"}])
            self.assertFalse(report["runtime_patch_authorized"])
            self.assertFalse(report["game_version_proven"])
            self.assertIsNone(report["queue_head_writer_function"])

    def test_unverified_build_never_authorizes_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "Warhammer3.exe"
            exe.write_bytes(make_pe(bytes.fromhex("488b0511223344488b")))
            r = scout.inspect(exe, make_map("1"*64))
            self.assertEqual(r["status"], "UNVERIFIED_BUILD_SHA_DISCOVERY_ONLY")
            self.assertFalse(r["runtime_patch_authorized"])
            self.assertFalse(r["expected_hash_matches"])
            self.assertEqual(r["legacy_byte_similarity"]["move"]["match_count"], 1)

    def test_historical_902_sha_rejected_even_if_expected_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "Warhammer3.exe"
            exe.write_bytes(make_pe())
            sha = hashlib.sha256(exe.read_bytes()).hexdigest()
            r = scout.inspect(exe, make_map(sha), expected_sha256=sha)
            self.assertEqual(r["status"], "REJECTED_HISTORICAL_9_0_2_BINARY")
            self.assertFalse(r["runtime_patch_authorized"])

    def test_expected_sha_mismatch_is_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "Warhammer3.exe"
            exe.write_bytes(make_pe())
            r = scout.inspect(exe, make_map("1"*64), expected_sha256="2"*64)
            self.assertEqual(r["status"], "REJECTED_EXPECTED_SHA_MISMATCH")

    def test_invalid_pe_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "Warhammer3.exe"
            cases = [b"hello", make_pe(machine=0x014c), bytearray(make_pe())]
            cases[2][0x80:0x84] = b"oops"
            for raw in cases:
                exe.write_bytes(raw)
                with self.assertRaises(scout.InvalidPE):
                    scout.inspect(exe, make_map("1"*64))

    def test_mask_cannot_consume_whole_guard_or_range_outside(self):
        for mask in ([[0, 9]], [[0, 10]], [[-1, 1]]):
            with self.assertRaises(ValueError):
                scout._guard_pattern({"guard": "488b0511223344488b", "normalization": {"mask_ranges": mask}})

    def test_cli_report_json_is_diagnostic_only_and_failure_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            exe = td / "Warhammer3.exe"
            exe.write_bytes(make_pe(bytes.fromhex("488b0511223344488b")))
            m = td / "legacy.json"
            m.write_text(json.dumps(make_map("f"*64)), encoding="utf-8")
            rpt = td / "reports" / "scan.json"
            cmd = [sys.executable, str(ROOT / "maintenance_tools/native_shift_re/scout_pe.py"),
                   "--exe", str(exe), "--legacy-map", str(m), "--report", str(rpt)]
            run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertFalse(json.loads(rpt.read_text(encoding="utf-8"))["runtime_patch_authorized"])
            cmd.extend(["--expected-sha256", "0"*64])
            run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(run.returncode, 3, run.stderr)
            self.assertEqual(json.loads(rpt.read_text(encoding="utf-8"))["status"], "REJECTED_EXPECTED_SHA_MISMATCH")

    def test_output_alias_exe_is_refused_and_binary_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            exe = td / "Warhammer3.exe"
            exe.write_bytes(make_pe())
            m = td / "legacy.json"
            m.write_text(json.dumps(make_map("f"*64)), encoding="utf-8")
            old = exe.read_bytes()
            cmd = [sys.executable, str(ROOT / "maintenance_tools/native_shift_re/scout_pe.py"),
                   "--exe", str(exe), "--legacy-map", str(m), "--report", str(exe)]
            run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(exe.read_bytes(), old)
            self.assertIn("may not overwrite", run.stderr)

    def test_ghidra_script_is_valid_python_source_and_readonly_contract(self):
        code = (ROOT / "maintenance_tools/native_shift_re/ghidra_order_xrefs.py").read_text(encoding="utf-8")
        compile(code, "ghidra_order_xrefs.py", "exec")
        self.assertIn("getExecutableMD5", code)
        self.assertIn("getParsedBytes", code)
        self.assertIn("patch_authorized\": False", code)
        self.assertNotIn("setBytes(", code)
        self.assertNotIn("patchInstruction(", code)


if __name__ == "__main__":
    unittest.main()
