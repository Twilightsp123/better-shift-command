"""Existing-record evidence counter: no repeat-game capture required."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(root))
import diagnose_existing_goal_capture as audit

class ExistingTraceDiagnostics(unittest.TestCase):
 def test_ambiguous_analyzer_grade_reveals_missing_kind(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'trace.jsonl'
   p.write_text('\n'.join(json.dumps(x) for x in [
      {'type':'ready'}, {'type':'event','ev':'QUEUED_CONTINUATION'},
      {'type':'event','ev':'B_MEMBER_FANOUT'}])+'\n')
   x=audit.diagnose(p)
   self.assertEqual(x['reason'],'B_FANOUT_BUT_NO_DEFERRED_RECEIVE')
   self.assertEqual(x['event_counts']['B_MEMBER_FANOUT'],1)
   self.assertFalse(x['game_fix_proven'])
 def test_receive_without_matching_packet_not_no_branch(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'trace.jsonl'
   p.write_text(json.dumps({'type':'event','ev':'B_DEFERRED_RECEIVE',
       'source':{'memberFanoutMatched':False},'packet58':('00'*88)})+'\n')
   self.assertEqual(audit.diagnose(p)['reason'],'RECEIVE_PRESENT_BUT_NO_PACKET_IDENTITY_MATCH')

 def test_captured_0x02_flag_excludes_original_B_packet_ctor(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'trace.jsonl'
   b=bytearray(88);b[0x50]=2
   lines=[
       {'type':'ready'},
       {'type':'event','ev':'B_DEFERRED_RECEIVE','member':'0x123',
        'traceId':1,'atMs':100,'packet58':b.hex(),
        'source':{'memberFanoutMatched':False}},
       {'type':'event','ev':'GOAL_COMMIT_PRE','traceId':1,
        'atMs':102,'before24':'00'*24,'proposed24':'01'*24},
       {'type':'event','ev':'GOAL_COMMIT_POST','traceId':1,'atMs':103},
       {'type':'event','ev':'SUMMARY','atMs':30002,'droppedEvents':0},
   ]
   p.write_text('\n'.join(json.dumps(x) for x in lines)+'\n')
   report=audit.diagnose(p)
   self.assertEqual(report['reason'],'RECEIVER_PACKETS_INCOMPATIBLE_WITH_KNOWN_B_BUILDER')
   self.assertEqual(report['packet_flag50_counts'],{'0x2':1})
   self.assertEqual(report['first_write_delay_ms']['median'],3)
   self.assertEqual(report['packet_count_incompatible_with_known_B_constructor'],1)
   self.assertFalse(report['B_route_execution_confirmed'])
 def test_B_packet_flag_0x06_requires_actual_source_proof(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'trace.jsonl'
   b=bytearray(88);b[0x50]=0x0e
   p.write_text(json.dumps({'type':'event','ev':'B_DEFERRED_RECEIVE',
       'traceId':1,'member':'0x333','packet58':b.hex(),
       'source':{'memberFanoutMatched':False}})+'\n')
   report=audit.diagnose(p)
   self.assertEqual(report['packet_count_incompatible_with_known_B_constructor'],0)
   self.assertFalse(report['B_route_execution_confirmed'])

if __name__=='__main__':unittest.main()
