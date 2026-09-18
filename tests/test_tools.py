from __future__ import annotations
import importlib.util,json,struct,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'controller_tools'))
import pack_tools as pt
import install_test as it
from analyze_feg import analyze

class PackTests(unittest.TestCase):
    def test_ready_pack_is_exact_controller(self):
        c=(ROOT/'source/better_shift_command.lua').read_bytes();self.assertEqual(pt.parse_pack(pt.make_pack([(pt.CONTROLLER_PATH,c)])),{pt.CONTROLLER_PATH:c})
    def test_payload_roundtrip_all_byte_values(self):
        raw=bytes(range(256))*37;self.assertEqual(pt.decode_payload(pt.encode_payload('test',raw)),raw)
    def test_truncation_rejected(self):
        with self.assertRaises(ValueError):pt.parse_pack(pt.make_pack([('a',b'123')])[:-1])
    def test_duplicate_path_rejected(self):
        with self.assertRaises(ValueError):pt.make_pack([('a',b''),('a',b'')])
    def test_trailing_garbage_rejected(self):
        with self.assertRaises(ValueError):pt.parse_pack(pt.make_pack([('a',b'')])+b'bad')
    def test_min_hook_hash_required(self):
        with self.assertRaises(ValueError):pt.native_info(b'MZ',b'incorrect')
    def test_v104_block_architecture_is_present(self):
        new=(ROOT/'source/better_shift_command.lua').read_text()
        # v1.0.11 intentionally replaces the global distance guard with action/block state.
        self.assertNotIn('local function protect_leg(st,g)',new)
        for token in ('local function action_runtime(a)','function Core.assign_block(st,a)',
                      'function Core.observe_move_completion(st,now)','local function route_handoff_ready(st,g,nexta)',
                      'function Core.observe_exit_block(st,now)','function Core.maybe_reassert_exit(st,now)',
                      'function Core.reconcile_native_successor(st,now)'):
            self.assertIn(token,new)
        self.assertIn('EXIT_ROUTE',new)
        self.assertIn('ACTION_COMPLETE',new)
        self.assertIn('ACTION_HANDOFF_COMMITTED',new)

    def test_v109_native_startup_hardening_is_present(self):
        s=(ROOT/'src/native_bridge/src/platform_windows.cpp').read_text()
        for token in ('MINHOOK_CREATE_FAILED_hook=', 'MH_ERROR_UNSUPPORTED_FUNCTION',
                      'create_status==9||create_status==10||create_status==-1000',
                      'Sleep(50)', 'MINHOOK_QUEUE_FAILED_hook=',
                      'MINHOOK_PARTIAL_ENABLE_PROCESS_RESTART_REQUIRED_status='):
            self.assertIn(token,s)
        # Structural hook failures must stay fail-closed; only transient MinHook statuses retry.
        self.assertNotIn('create_status==8||',s)
        self.assertNotIn('create_status==3||',s)

    def test_no_charge_or_killcount_dependency(self):
        s=(ROOT/'source/fresh_engagement_gate.lua').read_text()
        self.assertNotIn('is_charging(',s);self.assertNotIn('number_of_enemies_killed(',s)
    def test_gate_inline_matches_module_source(self):
        s=(ROOT/'source/better_shift_command.lua').read_text()
        self.assertIn('local FEG = (function()\n'+(ROOT/'source/fresh_engagement_gate.lua').read_text().rstrip()+'\nend)()',s)
    def test_selfcontained_preserves_bytes(self):
        a,b=b'bridge-fixture\0',b'minhook-fixture\0'
        with patch.object(pt,'native_info',return_value={}):
            p=pt.selfcontained(ROOT,(ROOT/'source/better_shift_command.lua').read_bytes(),a,b)
        d=pt.parse_pack(p);self.assertEqual(pt.decode_payload(d[pt.BRIDGE_PATH]),a);self.assertEqual(pt.decode_payload(d[pt.MINHOOK_PATH]),b)
        self.assertIn(b'    ensure_embedded_native()\n',d[pt.CONTROLLER_PATH])
        self.assertIn(pt.sha(a).encode(),d[pt.CONTROLLER_PATH])

class Reports(unittest.TestCase):
    def test_no_test_is_not_pass(self):
        r=analyze('nothing');self.assertFalse(r['test_loaded']);self.assertFalse(r['sampled_gate_contract_pass'])
    def test_sample_proof_not_physical_proof(self):
        text=(ROOT/'tests/fixtures/synthetic_residual_reentry.log').read_text()
        r=analyze(text);self.assertTrue(r['timed_exit_command_pass']);self.assertTrue(r['legacy_early_time_suppressed'])
        self.assertTrue(r['physical_majority_engagement'].startswith('UNASSESSED'))
    def test_under_three_seconds_rejected(self):
        text=(ROOT/'tests/fixtures/synthetic_residual_reentry.log').read_text().replace('hold_ms=3000','hold_ms=1000')
        self.assertFalse(analyze(text)['timed_exit_command_pass'])
    def test_closed_credit_rejected(self):
        s='[BETTER_SHIFT_COMMAND] FEG_CONFIG version=FEG1\n[BETTER_SHIFT_COMMAND] FEG_SAMPLE uid=1 gen=1 gate_open=false eligible_ms=100 raw_eligible=true'
        self.assertFalse(analyze(s)['sampled_gate_contract_pass'])
    def test_ack_without_issue_rejected(self):
        s='[BETTER_SHIFT_COMMAND] FEG_CONFIG version=FEG1\n[BETTER_SHIFT_COMMAND] FEG_EXIT_ACK uid=1 gen=1 issue=9'
        self.assertFalse(analyze(s)['timed_exit_command_pass'])
    def test_controller_failure_overrides_success(self):
        s=(ROOT/'tests/fixtures/synthetic_residual_reentry.log').read_text()+'\n[BETTER_SHIFT_COMMAND] CONTROLLER_FAIL reason=TEST'
        self.assertFalse(analyze(s)['timed_exit_command_pass'])

class Transactions(unittest.TestCase):
    def fixture(self,base:Path):
        root=base/'package';game=base/'game';(root/'data').mkdir(parents=True);(root/'source').mkdir();(game/'data').mkdir(parents=True)
        c=(ROOT/'source/better_shift_command.lua').read_bytes();(root/'source/better_shift_command.lua').write_bytes(c)
        (root/'data'/it.PACK_NAME).write_bytes(pt.make_pack([(pt.CONTROLLER_PATH,c)]))
        (game/'Warhammer3.exe').write_bytes(b'GAME_FIXTURE_NOT_REAL')
        (game/'wh3_native_bridge.dll').write_bytes(b'BRIDGE_TEST_FIXTURE');(game/'minhook.x64.dll').write_bytes(b'MH_TEST_FIXTURE')
        (game/'data'/it.PACK_NAME).write_bytes(b'ORIGINAL_PACK_FIXTURE')
        return root,game
    def test_install_then_rollback_does_not_touch_dlls(self):
        with tempfile.TemporaryDirectory() as td:
            root,game=self.fixture(Path(td))
            with patch.object(it,'native_info',return_value={'bridge_sha256':'fixture','minhook_sha256':'fixture'}),patch.object(it,'selfcontained',return_value=b'NEW_PACK_FIXTURE'):
                info=it.install(game,root,False)
            self.assertEqual(info['status'],'INSTALLED');self.assertEqual((game/'wh3_native_bridge.dll').read_bytes(),b'BRIDGE_TEST_FIXTURE')
            self.assertEqual(it.rollback(root,False)['status'],'ROLLED_BACK');self.assertEqual((game/'data'/it.PACK_NAME).read_bytes(),b'ORIGINAL_PACK_FIXTURE')
    def test_changed_pack_blocks_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            root,game=self.fixture(Path(td))
            with patch.object(it,'native_info',return_value={}),patch.object(it,'selfcontained',return_value=b'NEW'):it.install(game,root,False)
            (game/'data'/it.PACK_NAME).write_bytes(b'USER_EDIT')
            with self.assertRaises(RuntimeError):it.rollback(root,False)
            self.assertEqual((game/'data'/it.PACK_NAME).read_bytes(),b'USER_EDIT')
    def test_active_receipt_blocks_second_install(self):
        with tempfile.TemporaryDirectory() as td:
            root,game=self.fixture(Path(td))
            with patch.object(it,'native_info',return_value={}),patch.object(it,'selfcontained',return_value=b'NEW'):
                it.install(game,root,False)
                with self.assertRaises(RuntimeError):it.install(game,root,False)
    def test_native_failure_makes_no_install(self):
        with tempfile.TemporaryDirectory() as td:
            root,game=self.fixture(Path(td))
            with self.assertRaises(ValueError):it.install(game,root,False)
            self.assertEqual((game/'data'/it.PACK_NAME).read_bytes(),b'ORIGINAL_PACK_FIXTURE')
    def test_source_pack_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root,game=self.fixture(Path(td));(root/'source/better_shift_command.lua').write_text('different')
            with patch.object(it,'native_info',return_value={}):
                with self.assertRaises(RuntimeError):it.install(game,root,False)
    def test_failure_during_replace_restores_old_pack(self):
        with tempfile.TemporaryDirectory() as td:
            root,game=self.fixture(Path(td));actual=it.atomic;calls=[]
            def fail_first(path,data):
                calls.append(data)
                if len(calls)==1:raise OSError('fixture permission error')
                return actual(path,data)
            with patch.object(it,'native_info',return_value={}),patch.object(it,'selfcontained',return_value=b'NEW'),patch.object(it,'atomic',side_effect=fail_first):
                with self.assertRaises(OSError):it.install(game,root,False)
            self.assertEqual((game/'data'/it.PACK_NAME).read_bytes(),b'ORIGINAL_PACK_FIXTURE')
            self.assertEqual(json.loads((root/'output/install_receipt_FEG1.json').read_text())['status'],'INSTALL_FAILED_RESTORED')

if __name__=='__main__':unittest.main(verbosity=2)
