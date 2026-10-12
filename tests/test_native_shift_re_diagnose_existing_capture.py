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
       'source':{'memberFanoutMatched':False}})+'\n')
   self.assertEqual(audit.diagnose(p)['reason'],'RECEIVE_PRESENT_BUT_NO_PACKET_IDENTITY_MATCH')

if __name__=='__main__':unittest.main()
