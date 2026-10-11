"""BSC exact original goal direction / same-member B source correlation."""
import sys,os,tempfile,unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(SRC))
import audit_directional_goal_gate as g
import analyze_goal_branch_v2 as a

class GoalDirectionAndTraceTests(unittest.TestCase):
    def test_signed_dot_predicate(self):
        self.assertEqual(len(g.GUARDS),29)
        self.assertEqual(len(g.CALLS),4)
        self.assertFalse(g.goal_behind((0,0),(4,0),(1,0)))
        self.assertTrue(g.goal_behind((0,0),(-4,0),(1,0)))
        self.assertTrue(g.goal_behind((0,0),(4,0),(-1,0)))
    def test_native_conditional_gate_is_not_global_motor(self):
        self.assertFalse(g.action_branch_conditional(3,False,0,True))
        self.assertFalse(g.action_branch_conditional(3,True,1,True))
        self.assertTrue(g.action_branch_conditional(3,True,0,True))
    def test_sha_wrong_game_no_writes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wrong.exe';data=b'MZ'+b'wrong'*100;p.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):g.verify(p)
            self.assertEqual(p.read_bytes(),data)
    def test_packet_origin_required(self):
        r={'type':'event','ev':'B_DEFERRED_RECEIVE','member':'0xaa','traceId':3,
           'atMs':100,'source':{'memberFanoutMatched':False}}
        q={'type':'event','ev':'GOAL_READ','member':'0xaa','traceId':3,
           'writeSeenSinceReceive':False,'goalUnchangedSinceReceive':True}
        b={'type':'event','ev':'OLD_GOAL_DIRECTION_DECISION','member':'0xaa',
           'traceId':3,'predicateReturn':1,'lastGoalReadSameThread':True,
           'lastGoalReadWithin100ms':True,'writeSeenSinceReceive':False,
           'goalUnchangedSinceReceive':True}
        summary=a.analyze([r,q,b])
        self.assertEqual(summary['old_direction_with_B_fanout_count'],0)
        self.assertFalse(summary['physical_crowding_proven'])
        r['source']['memberFanoutMatched']=True
        summary=a.analyze([r,q,b])
        self.assertEqual(summary['grade'],'B_FANOUT_LINKED_OLD_GOAL_DIRECTION_DECISION')
        self.assertFalse(summary['geometric_route_conflict_proven'])
    def test_queue_identity_strict_fallback(self):
        r={'type':'event','ev':'B_DEFERRED_RECEIVE','member':'0xa','traceId':2,
           'atMs':100,'source':{'memberFanoutMatched':True,
                                'queuedUnitIdentityMatches':True}}
        q={'type':'event','ev':'GOAL_READ','member':'0xa','traceId':2,
           'writeSeenSinceReceive':False,'goalUnchangedSinceReceive':True}
        b={'type':'event','ev':'OLD_GOAL_DIRECTION_DECISION','member':'0xa',
           'traceId':2,'predicateReturn':0,'lastGoalReadSameThread':True,
           'lastGoalReadWithin100ms':True,'writeSeenSinceReceive':False,
           'goalUnchangedSinceReceive':True}
        result=a.analyze([{'type':'event','ev':'QUEUED_CONTINUATION'},r,q,b])
        self.assertEqual(result['grade'],'QUEUE_LINKED_B_OLD_GOAL_DIRECTION_DECISION')
        self.assertFalse(result['native_fix_proven'])
    def test_source_uses_proven_instruction_registers(self):
        js=(SRC/'one_shot_goal_branch_v2.js').read_text(encoding='utf8')
        self.assertIn("this.context.r14",js)
        self.assertIn("this.context.rdx",js)
        self.assertIn("this.context.rax.toUInt32()&0xff",js)
        self.assertIn("goalUnchangedSinceReceive",js)
        self.assertIn("ORIGINAL_CODE_GUARD_FAIL",js)
        self.assertLess(js.index('for(const [rva,expected] of PINS)'),
                        js.index('Interceptor.attach('))
    @unittest.skipUnless(os.getenv('WH3_903_EXE'),'GitHub CI excludes game EXE')
    def test_actual_exe_if_present(self):
        proof=g.verify(Path(os.environ['WH3_903_EXE']))
        self.assertEqual(proof['machine_guards'],29)
        self.assertFalse(proof['patch_authorized'])

if __name__=='__main__':unittest.main()
