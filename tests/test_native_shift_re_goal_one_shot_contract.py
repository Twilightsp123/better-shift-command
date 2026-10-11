"""Offline fail-closed one-shot goal trace contracts; no game runtime claim."""
import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_original_motor_goal_reader as audit
import analyze_once_goal_trace as analyzer
import run_once_goal_trace_windows as launcher

class GoalProbeContractTests(unittest.TestCase):
    def test_wrong_exe_refused_before_debugger_attach(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wrong.exe';old=b'MZ'+b'not original'*20;p.write_bytes(old)
            with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
                launcher.verify_preconditions(p,12345,Path(d)/'out.jsonl')
            self.assertEqual(p.read_bytes(),old)
    def test_after_receive_before_goal_write_is_observed_without_fake_conflict(self):
        events=[
          {'type':'event','ev':'B_DEFERRED_RECEIVE','actor':'0x100','traceId':3,
           'ms':100,'goalRaw':'aa'*32,'nearQueuedContinuation':True},
          {'type':'event','ev':'GOAL_READ','actor':'0x100','traceId':3,'ms':110,
           'motorWriteSinceReceive':False,'goalEqualToAtReceive':True},
          {'type':'event','ev':'GOAL_WRITE_PRE','actor':'0x100','traceId':3,'ms':150},
          {'type':'event','ev':'GOAL_READ','actor':'0x100','traceId':3,'ms':180,
           'motorWriteSinceReceive':True,'goalEqualToAtReceive':False},
        ]
        x=analyzer.classify_events(events)
        self.assertEqual(x['cases']['B_DEFERRED_RECEIVE']['instance_reads_old_goal_before_write'],1)
        self.assertEqual(x['cases']['B_DEFERRED_RECEIVE']['goal_commit_delays_ms'],[50])
        self.assertFalse(x['geometric_conflict_proven'])
        self.assertFalse(x['shift_b_object_identity_matched'])
        self.assertFalse(x['physical_collision_proven'])
    def test_direct_branch_is_negative_control(self):
        events=[
           {'type':'event','ev':'DIRECT_ACTION_RESET','actor':'0x1','traceId':6,'ms':3},
           {'type':'event','ev':'GOAL_WRITE_PRE','actor':'0x1','traceId':6,'ms':4},
        ]
        x=analyzer.classify_events(events)
        self.assertEqual(x['cases']['DIRECT_ACTION_RESET']['goal_commit_delays_ms'],[1])
        self.assertEqual(x['cases']['B_DEFERRED_RECEIVE']['member_task_instances'],0)
    def test_original_goal_audit_pinned(self):
        self.assertEqual(audit.E8[0x03256204],0x03115C94)
        self.assertEqual(audit.PINS['goal_read_member_target'][0],0x03115CBC)
        self.assertEqual(audit.E8[0x03102CBF],0x0312169C)
    def test_probe_opcode_guards_before_attach(self):
        code=(ROOT/'one_shot_goal_trace.js').read_text()
        self.assertIn('ORIGINAL_OPCODE_GUARD_FAILED',code)
        self.assertLess(code.index('for(const [rva,hex] of pins)'),code.index('Interceptor.attach('))
        self.assertNotIn('WriteProcessMemory',code)
        self.assertNotIn('writePointer(',code)
    @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Public CI has no original game executable')
    def test_original_executable_static_only(self):
        proof=audit.verify(Path(os.environ['WH3_903_EXE']))
        self.assertEqual(proof['opcode_guards'],28)
        self.assertFalse(proof['patch_authorized'])

if __name__=='__main__':unittest.main()
