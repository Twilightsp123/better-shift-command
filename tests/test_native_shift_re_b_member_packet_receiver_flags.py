"""Bounded read-only B member packet audit; CI never distributes an EXE."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'maintenance_tools' / 'native_shift_re' / 'audit_b_member_packet_receiver_flags.py'


class BPacketReceiverFlagEvidence(unittest.TestCase):
    def test_script_is_present(self):
        self.assertTrue(SCRIPT.is_file())

    def test_fail_closed_on_wrong_exe(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / 'Warhammer3.exe'
            fake.write_bytes(b'MZ' + bytes(64))
            proc = subprocess.run([sys.executable, str(SCRIPT), str(fake)], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('EXE SHA mismatch', proc.stderr)

    def test_packet_gate_symbolic_controls_not_runtime(self):
        # Models the observed packet flag predicate only; NOT original gameplay timing.
        gate = lambda flags, helper_value: helper_value == 0 and (flags & 0x20) == 0
        self.assertTrue(gate(0x06, 0))
        self.assertTrue(gate(0x16, 0))
        self.assertFalse(gate(0x26, 0))
        self.assertFalse(gate(0x06, 1))

    @unittest.skipUnless(os.getenv('WH3_903_EXE'), 'private EXE is absent in CI')
    def test_real_exe_only_if_supplied_privately(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), os.environ['WH3_903_EXE']], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('PASS 10/10', proc.stdout)


if __name__ == '__main__':
    unittest.main()
