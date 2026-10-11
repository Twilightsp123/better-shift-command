"""Original WH3 static goal-reader evidence: hard guards plus no false V3 claims."""
import os,sys,tempfile,unittest
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1]/"maintenance_tools"/"native_shift_re"
sys.path.insert(0,str(SOURCE))
import audit_original_motor_goal_reader as g

class GoalReadNativeTests(unittest.TestCase):
    def test_exact_sites_and_typed_action(self):
        self.assertEqual(len(g.PINS),28)
        self.assertEqual(len(g.E8),11)
        self.assertEqual(g.PINS["goal_read_member_target"],(0x03115CBC,"4c8d89e0010000"))
        self.assertEqual(g.E8[0x03256204],0x03115C94)
        self.assertEqual(g.E8[0x0325FD87],0x03256180)
    def test_aux_is_not_physical_integrator(self):
        self.assertEqual(g.E8[0x03119687],0x03102CA4)
        self.assertEqual(g.E8[0x03102CBF],0x0312169C)
        self.assertEqual(g.PINS["aux_unlink_member_ptr"][1],"4c898a00020000")
    def test_wrong_binary_fails_closed(self):
        from audit_wh3_full_native_chain import StrictPE
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"fake.exe"
            old=b"MZ"+b"NOT_WARHAMMER"*20
            p.write_bytes(old)
            with self.assertRaisesRegex(ValueError,"SHA_MISMATCH"):StrictPE(p)
            self.assertEqual(p.read_bytes(),old)
    def test_e8_decoding(self):
        self.assertEqual(g.e8_target(0x03256204,bytes.fromhex("e88bfaebff")),0x03115C94)
        with self.assertRaisesRegex(ValueError,"NOT_E8"):
            g.e8_target(0x03256204,b"\xe9"+b"\0"*4)
    @unittest.skipUnless(os.getenv("WH3_903_EXE"),"Public CI has no game EXE")
    def test_original_exe_if_available(self):
        proof=g.verify(Path(os.environ["WH3_903_EXE"]))
        self.assertEqual(proof["opcode_guards"],28)
        self.assertFalse(proof["patch_authorized"])
        self.assertFalse(proof["game_run"])

if __name__=="__main__":unittest.main()
