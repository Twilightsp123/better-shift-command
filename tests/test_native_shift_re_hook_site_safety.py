"""Fail-closed native goal observer hook guards and x64 boundaries."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(SRC))
import validate_native_goal_probe_sites as validator

class NativeGoalHookSafetyTests(unittest.TestCase):
    def test_pins_are_exact_and_corrected_post_write_site(self):
        pins=validator.parse_probe(SRC/'one_shot_goal_branch_v2.js')
        self.assertEqual(len(pins),10)
        self.assertNotIn(0x0311965f,pins)
        self.assertEqual(pins[0x03119660],'c787d80100000000803f')
        self.assertEqual(pins[0x03115cf4],'f3410f104a08')

    def test_opcode_spill_line_not_instruction_start(self):
        asm=''' 3119658:\tf2 0f 11 8f f0 01 00\tmovsd QWORD PTR [rdi+0x1f0],xmm1
 311965f:\t00
 3119660:\tc7 87 d8 01 00 00\tmov DWORD PTR [rdi+0x1d8],0x3f800000
'''
        got=validator.starts_from_asm(asm)
        self.assertEqual(got,{0x3119658,0x3119660})
        self.assertNotIn(0x311965f,got)

    def test_fake_binary_refused_before_disassembly(self):
        from audit_wh3_full_native_chain import StrictPE
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'faux.exe';old=b'MZ'+b'invalid WH3'*200
            p.write_bytes(old)
            with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
                StrictPE(p)
            self.assertEqual(old,p.read_bytes())

    @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Original EXE absent from public CI')
    def test_original_exact_exe_with_independent_disassembly(self):
        report=validator.audit(Path(os.environ['WH3_903_EXE']),
                SRC/'one_shot_goal_branch_v2.js')
        self.assertEqual(report['pin_count'],10)
        self.assertTrue(all(site['owner_rva'].startswith('0x') for site in report['checked']))
        self.assertFalse(report['windows_frida_attach_tested'])

if __name__=='__main__':unittest.main()
