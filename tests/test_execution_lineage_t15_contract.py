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
need('execution_lineage=future_lineage',4)
need('successor_index=future_index,execution_lineage=future_lineage',2)
need('execution_lineage="..clean(execution_lineage)',1)
need('local current_match,_,current_lineage=R1.execution_matches_action(e,cur)',1)
need('local match,_,lineage=R1.execution_matches_action(e,st.plan[i])',1)
# Later T2-B vocabulary is allowed in current source; lineage invariants must still
# reject the still-unimplemented Native MOVE passthrough.
if 'NATIVE_MOVE_PASSTHROUGH' in s: fail('later stage bypasses T1.5/T2-MOVE architecture')
# Existing T1 evaluator remains the sole transition decision plane.
need('function R1.TransitionPolicy.evaluate(',1)
if s.count('R1.TransitionPolicy.evaluate(st,')!=11: fail('shared evaluator calls include E Native MOVE adoption and H4 fresh MOVE postdrain')
for legacy in ('consumer="PROACTIVE"','consumer="NATIVE_RECONCILE"','consumer="SCHEDULER"','context.consumer'):
    if legacy in s: fail('later stage reintroduced consumer-specific permission: '+legacy)
print('PASS: T1.5 execution-lineage structural contract preserved through later permission-neutral stages')
