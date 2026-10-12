"""Safe offline regressions for BSC original-EXE source observer."""
import json
import os
from pathlib import Path
import tempfile
import threading
import types
import unittest
from unittest.mock import patch
import subprocess
import sys
import struct

import analyze_one_shot
import run_one_shot
import verify_original_probe as native

ROOT=Path(__file__).resolve().parent


class OfflineTests(unittest.TestCase):
    def test_frida_reserved_global_conflict_is_caught_before_game_attach(self):
        original=(ROOT/'one_shot_native_source.js').read_text(encoding='utf8')
        run_one_shot.validate_agent_globals(original)
        with self.assertRaisesRegex(ValueError, 'FRIDA_PTR_GLOBAL_COLLISION'):
            run_one_shot.validate_agent_globals(original + '\nfunction ptr(p,o){return null;}\n')
        with self.assertRaisesRegex(ValueError, 'FRIDA_JS_GLOBAL_SCOPE_NOT_ISOLATED'):
            run_one_shot.validate_agent_globals("'use strict';\nfunction ptr(p,o){return null;}")

    def test_provenance_inferred_only_from_real_sender_pair(self):
        rows=[
            {'type':'ready','guardCount':14},
            {'type':'event','ev':'POSTCTOR_SENDER_ENTER', 'task':'0x1234'},
            {'type':'event','ev':'NATIVE_MEMBER_SEND','source':'POSTCTOR_REWRITE',
             'group':'0x555','unit':'0x444','member':'0x11'},
            {'type':'event','ev':'MEMBER_RECEIVER','source':'POSTCTOR_REWRITE',
             'explicitlyMatchedSender':True,'returnRva':'0x3284b81',
             'group':'0x555','unit':'0x444','member':'0x11'},
            {'type':'event','ev':'DEFERRED_PACKET','source':'POSTCTOR_REWRITE'},
            {'type':'event','ev':'GOAL_WRITE_POST','group':'0x555'},
            {'type':'summary','sourceCounts':{'POSTCTOR_REWRITE':1},'dropped':0,
             'detachErrors':[]}
        ]
        report=analyze_one_shot.analyze(rows)
        self.assertEqual(report['grade'],'RUNTIME_NATIVE_SOURCE_MATCH_CONFIRMED')
        self.assertEqual(report['sender_to_receiver_strict_matches'],{'POSTCTOR_REWRITE':1})
        self.assertEqual(report['groups_ranked_by_distinct_sampled_members'],[('0x555',1)])
        self.assertFalse(report['physical_crowding_causality_proven'])
        self.assertFalse(report['patch_authorized'])

    def test_real_world_style_19868_drops_are_not_native_sender_absence(self):
        # Summary stores attempted events even when raw log budget discarded them.
        # Exact numbers are from the user's first successful 18-second Windows run;
        # this is a synthetic control, not a copy of user runtime pointers.
        saved={'QUEUE_MANAGER_ENTRY':1697,'NATIVE_MOVE_ISSUER':1,
               'POSTCTOR_SENDER_ENTER':2,'MOTOR_GOAL_REVERSAL':10,
               'POST_TURN_POSITION':151,'GROUP_TICK_POSITION':234}
        attempted=dict(saved)
        attempted.update({'QUEUE_MANAGER_ENTRY':21534,'NATIVE_MOVE_ISSUER':7,
          'POSTCTOR_SENDER_ENTER':4,'NATIVE_MEMBER_SEND':3,
          'MEMBER_RECEIVER':3,'DEFERRED_PACKET':3,'GOAL_WRITE_PRE':3,
          'GOAL_WRITE_POST':3,'QUEUED_CONTINUATION':2,'GOAL_READ':3,
          'NATIVE_GOAL_DIRECTION':3})
        rows=[{'type':'ready'}]
        rows.extend({'type':'event','ev':k} for k,n in saved.items() for _ in range(n))
        rows.append({'type':'summary','dropped':19868,'eventCounts':attempted,
                     'sourceCounts':{'POSTCTOR_REWRITE':50,
                                     'RECEIVER_OTHER_OR_UNKNOWN':50},
                     'detachErrors':[]})
        report=analyze_one_shot.analyze(rows)
        self.assertEqual(report['grade'],'NATIVE_SOURCE_EVENTS_TRIGGERED_BUT_DROPPED_BY_LOGGER')
        self.assertEqual(report['agent_event_counts_dropped_by_logger']['QUEUE_MANAGER_ENTRY'],19837)
        self.assertEqual(report['core_identity_records_dropped']['QUEUED_CONTINUATION'],2)
        self.assertEqual(report['core_identity_records_dropped']['NATIVE_MEMBER_SEND'],3)
        self.assertEqual(report['native_sender_hook_executions'],3)
        self.assertEqual(report['queued_hook_executions_from_agent_summary'],2)
        self.assertTrue(report['logger_drop_count_reconciles'])
        self.assertFalse(report['patch_authorized'])

    def test_horizontal_close_approach_is_not_proof_of_collision(self):
        samples=[{'type':'event','ev':'GROUP_TICK_POSITION','group':'g',
             'turnStartTick':658,'groupTick':tick,'member':m,'x':x,'z':z}
             for tick,pos in [(659,[(0.,0.),(1.124,0.)]),
                              (660,[(0.,0.),(0.609,0.)]),
                              (661,[(0.,0.),(0.973,0.)])]
             for m,(x,z) in [('m'+str(i),pair) for i,pair in enumerate(pos)]]
        result=analyze_one_shot.analyze([{'type':'ready'},*samples,
                  {'type':'summary','dropped':0,'detachErrors':[]}])
        approach=result['sampled_close_approaches'][0]
        self.assertEqual(approach['min_distance_tick'],660)
        self.assertAlmostEqual(approach['min_horizontal_member_center_distance'],0.609)
        self.assertFalse(approach['physical_collision_proven'])

    def test_sources_named_without_sender_are_not_positive(self):
        rows=[{'type':'ready'},
              {'type':'event','ev':'MEMBER_RECEIVER','source':'POSTCTOR_REWRITE',
               'returnRva':'0x3284b81','explicitlyMatchedSender':False},
              {'type':'summary','detachErrors':[]}]
        report=analyze_one_shot.analyze(rows)
        self.assertEqual(report['grade'],'RECEIVER_HIT_BUT_NATIVE_SENDER_UNMATCHED')
        self.assertEqual(report['sender_to_receiver_strict_matches'],{})

    def test_callback_error_or_missing_summary_is_not_ready(self):
        a=analyze_one_shot.analyze([{'type':'ready'},{'type':'probe_error','error':'x'}])
        self.assertEqual(a['grade'],'INCOMPLETE_OR_INSTRUMENTATION_ERROR')
        self.assertFalse(a['summary_observed'])

    def test_wrong_exe_rejected_before_attach(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'Warhammer3.exe'
            exe.write_bytes(b'MZ'+b'UNTRUSTED'*100)
            with self.assertRaisesRegex(ValueError,'GAME_SHA256_MISMATCH'):
                run_one_shot.validate(exe,1234,Path(d)/'result.jsonl')
            self.assertEqual(exe.read_bytes(),b'MZ'+b'UNTRUSTED'*100)

    def test_supervisor_terminates_when_detach_hangs(self):
        class FakeProcess:
            def __init__(self):self.terminated=False
            def wait(self,timeout=None):
                if not self.terminated:
                    raise subprocess.TimeoutExpired('python run_one_shot.py',timeout)
                return 0
            def terminate(self):self.terminated=True
        child=FakeProcess()
        with patch.object(run_one_shot,'validate',lambda *x: None),\
             patch.object(run_one_shot.subprocess,'Popen',return_value=child):
            result=run_one_shot.parent(Path('/dummy.exe'),1,Path('x.jsonl'),5)
        self.assertEqual(result,5)
        self.assertTrue(child.terminated)

    def test_worker_shuts_agent_down_even_when_frida_detach_never_returns(self):
        class FakeScript:
            def __init__(self):self.on_message=None
            def on(self,_,func):self.on_message=func
            def load(self):self.on_message({'type':'send','payload':{'type':'ready','guardCount':14}},None)
            def post(self,command):
                if command.get('type')=='stop':
                    self.on_message({'type':'send','payload':{'type':'summary','eventsSaved':2,
                                                             'detachErrors':[]}},None)
        class FakeSession:
            def create_script(self,js):return FakeScript()
            def detach(self):threading.Event().wait(5)
        fake=types.SimpleNamespace(attach=lambda pid:FakeSession())
        with tempfile.TemporaryDirectory() as t,\
             patch.object(run_one_shot,'validate',lambda *x: None),\
             patch.dict(sys.modules,{'frida':fake}):
            target=Path(t)/'trace.jsonl'
            result=run_one_shot.worker(Path(t)/'Warhammer3.exe',123,target,0)
            self.assertEqual(result,0)
            events=[json.loads(line) for line in target.read_text().splitlines()]
            self.assertEqual([x.get('type') for x in events],['ready','summary'])

    def test_supervisor_keeps_completed_trace_if_native_detach_hangs(self):
        class StalledWorker:
            def __init__(self):self.killed=False
            def wait(self,timeout=None):
                if not self.killed:raise subprocess.TimeoutExpired('worker',timeout)
                return 5
            def terminate(self):self.killed=True
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'bsc_once_source.jsonl'
            path.write_text(json.dumps({'type':'ready'})+'\n'+
                json.dumps({'type':'summary','detachErrors':[],'sourceCounts':{},'dropped':0})+'\n')
            with patch.object(run_one_shot,'validate',lambda *a:None),\
                 patch.object(run_one_shot.subprocess,'Popen',return_value=StalledWorker()):
                result=run_one_shot.parent(Path('/dummy.exe'),3,path,5)
            self.assertEqual(result,0)
            report=path.with_name(path.stem+'_report.json')
            self.assertTrue(report.exists())
            analyzed=json.loads(report.read_text())
            self.assertTrue(analyzed['summary_observed'])
            self.assertFalse(analyzed['physical_crowding_causality_proven'])

    def test_group_tick_motion_distinguishes_new_goal_from_physical_displacement(self):
        old=struct.pack('<ffffff',10.,0.,0.,0.,0.,0.).hex()
        new=struct.pack('<ffffff',-10.,0.,0.,0.,0.,0.).hex()
        records=[{'type':'ready'}, {'type':'event','ev':'MOTOR_GOAL_REVERSAL',
          'group':'0xgroup','member':'0xmodel','groupTick':2000,'x':0.,'z':0.,
          'oldGoal24':old,'newGoal24':new,'headingCosine':-1.}]
        for tick,x in [(2001,0.),(2002,1.),(2003,0.9)]:
            records.append({'type':'event','ev':'GROUP_TICK_POSITION',
                'group':'0xgroup','turnStartTick':2000,'groupTick':tick,
                'member':'0xmodel','x':x,'z':0.})
        records.append({'type':'summary','detachErrors':[]})
        result=analyze_one_shot.analyze(records)
        self.assertEqual(len(result['sampled_post_reversal_displacement']),1)
        turn=result['sampled_post_reversal_displacement'][0]
        self.assertEqual(turn['members_with_2plus_group_tick_positions'],1)
        self.assertEqual(turn['old_heading_forward_intervals'],1)
        self.assertEqual(turn['old_heading_reverse_intervals'],1)
        self.assertEqual(turn['earliest_sampled_reverse_tick'],2003)
        self.assertFalse(result['physical_crowding_causality_proven'])

    def test_original_image_validation_if_available(self):
        source=os.getenv('WH3_EXE')
        if not source:self.skipTest('No original game EXE in this CI job')
        out=native.verify(Path(source),ROOT/'one_shot_native_source.js')
        self.assertEqual(out['verified_hook_count'],14)
        self.assertFalse(out['frida_windows_attach_tested'])
        self.assertFalse(out['native_patch_authorized'])


if __name__=='__main__':unittest.main()
