"""Offline, deterministic contract checks for targeted native object xrefs.

These tests do NOT establish that any native code ran in a WH3 battle.
"""
import importlib.util
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "maintenance_tools" / "native_shift_re"
sys.path.insert(0, str(SOURCE))
import audit_b_native_object_xrefs as xrefs


class NativeBObjectXrefsTests(unittest.TestCase):
    def test_lea_rip_selects_exact_vtable(self):
        site = 0x01000000
        target = 0x03905D98
        blob = b"\x48\x8d\x05" + struct.pack("<i", target-site-7)
        result = xrefs.scan_blob(blob, site, {target}, set())
        self.assertEqual(len(result), 1)
        self.assertEqual((result[0]["site"], result[0]["target"],
                          result[0]["kind"]), (site, target, "rip_lea"))

    def test_e8_resolves_original_constructor(self):
        site = 0x200000
        target = 0x02F6EF4C
        blob = b"\xe8" + struct.pack("<i", target-site-5)
        result = xrefs.scan_blob(blob, site, set(), {target})
        self.assertEqual(result[0]["kind"], "direct_call")
        self.assertEqual(result[0]["target"], target)

    def test_offset_70_alone_is_not_a_typed_xref(self):
        # No claim that an arbitrary object+0x70 is a B route cache.
        blob = b"\x48\x8b\x41\x70\x48\x89\x43\x70"
        self.assertEqual(xrefs.scan_blob(
            blob, 0x1000, set(xrefs.VTABLE_ROOTS),
            set(xrefs.DIRECT_TARGETS)), [])

    def test_nested_random_bytes_are_only_candidates(self):
        # The scanner deliberately requires a separate objdump
        # instruction-boundary check on the genuine PE.
        embedded = b"\x90\x48\x8d\x05\x00\x00\x00\x00"
        hit = xrefs.scan_blob(embedded, 0x1000, {0x1008}, set())
        self.assertEqual(len(hit), 1)
        self.assertNotIn("evidence_level", hit[0])

    def test_vtable_negative_control_not_shared(self):
        self.assertNotEqual(xrefs.VTABLE_ROOTS[0x03905D98],
                            xrefs.VTABLE_ROOTS[0x03905D18])
        self.assertIn(0x03905E18, xrefs.VTABLE_ROOTS)

    def test_anchor_identity_separates_owners(self):
        self.assertNotEqual(xrefs.TYPED_ANCHORS["node_geometry_write"],
                            xrefs.TYPED_ANCHORS["member_goal_writer_commit"])

    def test_wrong_exe_sha_rejected_before_scan(self):
        from audit_wh3_full_native_chain import StrictPE
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "fake.exe"
            data = b"MZ" + b"x" * 512
            exe.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "SHA_MISMATCH"):
                StrictPE(exe)
            self.assertEqual(exe.read_bytes(), data)

    def test_no_executable_writes_in_source(self):
        source = (SOURCE / "audit_b_native_object_xrefs.py").read_text()
        self.assertNotIn("ACCESS_WRITE", source)
        self.assertNotIn("VirtualProtect", source)
        self.assertNotIn("WriteProcessMemory", source)
        self.assertIn("patch_authorized", source)

    @unittest.skipUnless(os.getenv("WH3_903_EXE"), "original EXE not present in CI")
    def test_original_exe_scan(self):
        report = xrefs.run(Path(os.environ["WH3_903_EXE"]),
                           SOURCE / "full_chain_manifest.json")
        self.assertEqual(report["proof_level"], "STATIC_EXACT_EXE_XREF_ONLY")
        self.assertFalse(report["patch_authorized"])
        self.assertGreaterEqual(report["xrefs"]["scanned_code_sections"], 1)


if __name__ == "__main__":
    unittest.main()
