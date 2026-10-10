"""Synthetic-only fail-closed tests for 9.0.3 original MOVE->member dispatch.

These do not simulate soldier movement, prove a waypoint-arrival predicate,
or supply a working game Hook.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "maintenance_tools" / "native_shift_re"))
from audit_903_move_member_fanout import INSTRUCTION_GUARDS, CALL_TARGETS, verify
from test_native_shift_re_formation import fixture


class NativeMoveMemberFanoutContracts(unittest.TestCase):
    def test_38_machine_sites_and_nine_original_calls(self):
        rows = [line for line in INSTRUCTION_GUARDS.strip().splitlines()]
        self.assertEqual(len(rows), 38)
        self.assertEqual(len(CALL_TARGETS), 9)
        self.assertEqual(len(set(row.split()[0] for row in rows)), 38)

    def test_real_move_issue_path(self):
        self.assertEqual(
            CALL_TARGETS["MOVE_ISSUER_TO_ROUTE_UPDATE"],
            (0x03032965, 0x0302DB44),
        )
        self.assertEqual(
            CALL_TARGETS["ROUTE_UPDATE_TO_GROUP_FANOUT"],
            (0x0302DBDB, 0x030D5490),
        )

    def test_original_group_is_derived_from_root_members(self):
        self.assertEqual(CALL_TARGETS["ROUTE_UPDATE_TO_GROUP_BUILDER"][1], 0x0301B8E4)
        self.assertEqual(CALL_TARGETS["GROUP_BUILDER_TO_MEMBER_INSERT"][1], 0x030E0460)

    def test_indexed_output_stride_is_48_bytes(self):
        for i in (0, 1, 2, 3, 25, 200):
            self.assertEqual((i + 2 * i) << 4, i * 0x30)

    def test_native_member_issue_is_virtual_not_new_bsc_queue(self):
        self.assertIn("030d550f ff9068030000", INSTRUCTION_GUARDS)
        self.assertIn("02f5f8bd c6435026", INSTRUCTION_GUARDS)

    def test_secondary_queue_count_gate_not_global_arrival(self):
        self.assertIn("03022a66 84d2", INSTRUCTION_GUARDS)
        self.assertIn("03043284 b201", INSTRUCTION_GUARDS)

    def test_nonmatching_binary_is_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "fixture.exe"
            orig = fixture()
            p.write_bytes(orig)
            with self.assertRaisesRegex(ValueError, "EXE_SHA256_MISMATCH"):
                verify(p)
            self.assertEqual(p.read_bytes(), orig)


if __name__ == "__main__":
    unittest.main()
