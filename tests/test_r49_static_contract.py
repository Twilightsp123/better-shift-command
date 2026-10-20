#!/usr/bin/env python3
"""No native execution. CI-safe private EXE+mod checks are env-gated."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'maintenance_tools/native_shift_re'
sys.path.insert(0,str(SRC))
import audit_r49_sampler_contract as audit

LUA=SRC/'bsc_r49_guarded_passive_sampler_research.lua'
MOCK=ROOT/'tests/test_r49_sampler_mock.lua'


class SamplerContract(unittest.TestCase):
    def test_passive_guard_source(self):
        text=LUA.read_text('utf8')
        self.assertIn('Do not auto-load',text)
        code='\n'.join(line.split('--',1)[0] for line in text.splitlines())
        for token in ['mr.write(', 'mr.call(', 'mr.hook(', 'mr.code_cave(',
                      'mr.patcher(', 'cm:callback(', 'mr.game_alloc(']:
            self.assertNotIn(token,code)
        self.assertIn("roster=mr.read(array,0,n*8)",code)
        self.assertIn('mr.elapsed_us(began)',code)
        self.assertIn("return nil,'duplicate_roster_pointer'",code)
        self.assertIn('intra_sample_full_roster_stable=true',code)
    def test_read_original_alone_is_not_used_as_patch_absence(self):
        s=LUA.read_text('utf8')
        self.assertIn('mr.read_original(entry[1],0,#entry[2])',s)
        self.assertIn('mr.read(entry[1],0,#entry[2])',s)
        self.assertIn('mr.hook_info(entry[1])',s)
    def test_assert_live_scanner_never_trusts_plain_lua_32bit(self):
        s=LUA.read_text('utf8')
        self.assertIn('mr.add(mr.add(base, rva-lo), lo)',s)
        self.assertIn('mr.read_uint16(base,hdr+0x50)',s)
        self.assertNotIn('mr.add(base,rva)',s)
    @unittest.skipUnless(shutil.which('texluac'), 'Lua compiler not on CI')
    def test_lua_source_parses(self):
        r=subprocess.run(['texluac','-p',str(LUA)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
    @unittest.skipUnless(shutil.which('texlua'),'Lua runner not on CI')
    def test_actual_lua_mock(self):
        r=subprocess.run(['texlua',str(MOCK),str(LUA)],capture_output=True,text=True,timeout=12)
        self.assertEqual(r.returncode,0,r.stdout+'\n'+r.stderr)
        self.assertIn('R49_LUA_MOCK_ALL_PASS=20',r.stdout)
    def test_contract_reports_deny_live_and_patch(self):
        text=(SRC/'r49_spatial_evidence_preflight.py').read_text('utf8')
        self.assertIn("'gameplay_patch_authorized':False",text)
        self.assertIn("'same_pointer_same_lifetime_proven':False",text)
    @unittest.skipUnless(all(os.getenv(x) for x in ('BSC_CURRENT_EXE','BSC_DERPY_ZIP','BSC_MEMREADER_ZIP')),
                         'Private user-provided EXE and third-party pack zip omitted from public CI')
    def test_actual_private_game_and_mod_archive_bytes(self):
        result=audit.audit(os.environ['BSC_CURRENT_EXE'],os.environ['BSC_DERPY_ZIP'],os.environ['BSC_MEMREADER_ZIP'])
        self.assertEqual((result['verified_queued_tick_original_bytes'],result['verified_queue_gate_original_bytes']),(7,18))
        self.assertEqual((result['verified_external_action_vtable_slots'],result['verified_member_vtable_slots']),(14,2))
        self.assertFalse(result['live_gameplay_capture_run'])
        self.assertFalse(result['native_gameplay_patch_authorized'])
    def test_rejects_wrong_game_sha_without_touching_game(self):
        with tempfile.TemporaryDirectory() as t:
            fake=Path(t)/'no.exe';fake.write_bytes(b'MZ'+b'\0'*512)
            with self.assertRaisesRegex(ValueError,'GAME_SHA_MISMATCH'):
                audit.audit(fake,'not-existent-derpy.zip','not-existent-memreader.zip')

if __name__=='__main__':unittest.main()
