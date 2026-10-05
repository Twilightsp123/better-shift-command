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
need('envelope_stage=TPOL_T1_7_CONSUMER_NEUTRAL',1)
need('VERSION="TPOL_T1_7"',1)
need('function R1.TransitionPolicy.evaluate(',1)
need('local successor_index=context.successor_index or context.future_index or (current_index and current_index+1)',1)
need('issue_window=transition_envelope(false,"TRANSITION_WAIT",false)',1)
need('adopt_window=transition_envelope(false,"TRANSITION_WAIT",false)',1)
need('d.adopt_window=transition_envelope(false,"CANONICAL_INTERMEDIATE_ACTIONS_OWED",true)',1)
need('local adopt_window=decision.adopt_window or {open=false,reason=decision.reason,hard_violation=decision.hard_violation}',1)
need('decision.issue_window and decision.issue_window.open',2)
if s.count('R1.TransitionPolicy.evaluate(st,')!=6: fail('shared evaluator call-site count changed')
for legacy in ('consumer="PROACTIVE"','consumer="NATIVE_RECONCILE"','consumer="SCHEDULER"','context.consumer'):
    if legacy in s: fail('consumer-specific permission remains: '+legacy)
for forbidden in ('ATTACK_TERMINAL_CORRIDOR','NATIVE_MOVE_PASSTHROUGH'):
    if forbidden in s: fail('T1.7 activated T2 behavior: '+forbidden)
need('if current_index and successor_index and successor_index~=current_index+1 then',1)
print('PASS: T1.7 consumer-neutral issue/adopt envelope structural contract')
