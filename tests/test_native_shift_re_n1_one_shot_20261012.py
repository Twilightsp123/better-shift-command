"""CI entrypoint for N1 strict original-EXE one-shot native source/motor probe.

Only mocks and synthesized tests run in public CI. The original WH3 binary and
private user runtime trace are never uploaded to GitHub.
"""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "maintenance_tools" / "native_shift_re" / "experiments" / "n1_one_shot_20261012"
sys.path.insert(0, str(EXPERIMENT))

# The imported TestCase makes the nine source-level contract tests discoverable
# by the existing N1 native_shift_re*.py GitHub workflow.
from test_offline import OfflineTests  # noqa: F401


class OriginalOneShotJavascriptContracts(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node not installed on this runner")
    def test_frida_source_javascript_syntax(self):
        completed = subprocess.run(
            ["node", "--check", str(EXPERIMENT / "one_shot_native_source.js")],
            text=True, capture_output=True, timeout=15)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node not installed on this runner")
    def test_mocked_native_send_receive_and_gradual_motion(self):
        completed = subprocess.run(
            ["node", str(EXPERIMENT / "test_probe_node.js")],
            text=True, capture_output=True, timeout=15)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("OFFLINE_FRIDA_MOCK_PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
