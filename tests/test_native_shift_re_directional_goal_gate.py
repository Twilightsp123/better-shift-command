"""Original-native directional gate, synthetic negative tests, exact EXE optional."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1]/"maintenance_tools"/"native_shift_re"
sys.path.insert(0,str(SOURCE))
import audit_directional_goal_gate as audit

class GoalDirectionGateTests(unittest.TestCase):
    def test_native_direct_branch_and_opcode_contract(self):
        self.assertEqual(len(audit.GUARDS),29)
        self.assertEqual(len(audit.CALLS),4)
        self.assertEqual(audit.GUARDS[0x03115CBC],"4c8d89e0010000")
        self.assertEqual(audit.GUARDS[0x03256209],"84c0")
        self.assertEqual(audit.GUARDS[0x0325620B],"0f845d010000")
    def test_target_before_and_after_180_turn(self):
        self.assertFalse(audit.goal_behind((0,0),(4,0),(1,0)))
        self.assertTrue(audit.goal_behind((0,0),(-4,0),(1,0)))
        self.assertTrue(audit.goal_behind((0,0),(4,0),(-1,0)))
    def test_guarded_mode_negative_cases(self):
        self.assertFalse(audit.action_branch_conditional(3,False,0,True))
        self.assertFalse(audit.action_branch_conditional(3,True,1,True))
        self.assertTrue(audit.action_branch_conditional(3,True,0,True))
        self.assertTrue(audit.action_branch_conditional(0,True,0,False))
    def test_failure_on_untrusted_game_executable(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"not_wh3.exe";old=b"MZ"+b"wrong"*100
            path.write_bytes(old)
            with self.assertRaisesRegex(ValueError,"SHA_MISMATCH"):
                audit.verify(path)
            self.assertEqual(path.read_bytes(),old)
    def test_original_binary_if_attached(self):
        path=os.getenv("WH3_903_EXE")
        if not path:self.skipTest("GitHub CI has no copyrighted game executable")
        proof=audit.verify(Path(path))
        self.assertEqual(proof["machine_guards"],29)
        self.assertFalse(proof["patch_authorized"])
        self.assertFalse(proof["physical_collision_proven"])

if __name__=="__main__":unittest.main()
