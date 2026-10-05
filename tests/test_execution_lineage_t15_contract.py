from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
controller=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'source/better_shift_command.lua'
s=controller.read_text(encoding='utf-8')

def fail(msg):
    print('FAIL '+msg)
    raise SystemExit(1)

def need(token,count=None):
    n=s.count(token)
    if n==0: fail('missing '+token)
    if count is not None and n!=count: fail(f'{token} count={n}, expected {count}')

need('policy_stage=TPOL_T1_5_EXECUTION_LINEAGE',1)
need('function R1.action_execution_identity(a)',1)
need('local issued=rt.issued_identity',1)
need('capture_identity={lineage="PLAYER_NATIVE"',1)
need('issued_identity={lineage="BSC_ISSUED"',1)
need('previous_execution_lane=st.execution_lane',1)
need('st.execution_lane="BSC_ISSUED"',1)
need('st.execution_lane=p.previous_execution_lane or st.execution_lane',2)
need('execution_lineage=future_lineage',2)
need('future_index=future_index,execution_lineage=future_lineage',1)
need('execution_lineage="..clean(execution_lineage)',1)
need('local current_match,_,current_lineage=R1.execution_matches_action(e,cur)',1)
need('local match,_,lineage=R1.execution_matches_action(e,st.plan[i])',1)
# T1.5 must not itself activate the later T2 behavior vocabulary.
for forbidden in ('zone="ADOPT_ONLY"','ATTACK_TERMINAL_CORRIDOR','NATIVE_MOVE_PASSTHROUGH'):
    if forbidden in s: fail('T1.5 accidentally activates/retains staged behavior: '+forbidden)
# Existing T1 evaluator remains the sole transition decision plane.
need('function R1.TransitionPolicy.evaluate(',1)
need('consumer="PROACTIVE"',2)
need('consumer="NATIVE_RECONCILE"',1)
need('consumer="SCHEDULER"',2)
print('PASS: T1.5 execution-lineage structural contract; transition behavior remains T1')
