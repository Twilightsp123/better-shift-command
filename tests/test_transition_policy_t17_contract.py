from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
controller=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'source/better_shift_command.lua'
s=controller.read_text(encoding='utf-8')

def fail(msg): print('FAIL '+msg); raise SystemExit(1)
def need(token,count=None):
    n=s.count(token)
    if n==0: fail('missing '+token)
    if count is not None and n!=count: fail(f'{token} count={n}, expected {count}')

def block(start,end):
    a=s.find(start)
    if a<0: fail('missing '+start)
    b=s.find(end,a+len(start))
    if b<0: fail('missing end '+end)
    return s[a:b]

need('policy_envelope_stage=TPOL_T1_7_CONSUMER_NEUTRAL',1)
need('function R1.TransitionPolicy.evaluate_edge(',1)
need('function R1.TransitionPolicy.project(',1)
need('function R1.TransitionPolicy.evaluate(',1)
edge=block('function R1.TransitionPolicy.evaluate_edge(', '\nfunction R1.TransitionPolicy.project(')
if 'consumer' in edge: fail('consumer leaked into evaluate_edge permission calculation')
project=block('function R1.TransitionPolicy.project(', '\n-- Compatibility wrapper')
if 'local consumer=context.consumer or "PROACTIVE"' not in project: fail('projection consumer selector missing')
need('d.adopt_ready=d.issue_ready',1)
need('d.adopt_window.ready=d.adopt_ready',1)
need('mode="T1_7_LOCKED_TO_ISSUE"',1)
if 'zone="ADOPT_ONLY"' in s or "zone='ADOPT_ONLY'" in s: fail('T1.7 must not activate ADOPT_ONLY')
need('if future_index and current_index and future_index~=current_index+1 then',1)
need('if d.successor_type=="MOVE" then',1)
need('local decision=R1.TransitionPolicy.project(edge,{consumer="NATIVE_RECONCILE"',1)
if s.count('local decision=R1.TransitionPolicy.project(edge,{consumer="PROACTIVE"})')!=2:
    fail('proactive MOVE/ATTACK must project the same edge decision')
if 'consumer="SCHEDULER"' in s: fail('scheduler still participates as a permission consumer')
if s.count('R1.TransitionPolicy.evaluate_edge(st,cur,')<5:
    fail('runtime consumers do not all read the shared edge evaluator')
if not controller.name.endswith('.lua'):
    fail('bad controller path')
print('PASS: T1.7 consumer-neutral policy contract; adopt envelope locked to issue envelope')
