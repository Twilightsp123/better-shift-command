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
need('transaction_stage=TPOL_T1_6_TRANSITION_TRANSACTION',1)
need('function Core.begin_transition_txn(',1)
need('function Core.abort_transition_txn(',1)
need('function Core.commit_transition_edge(',1)
need('st.transition_txn=tx',1)
need('transition_txn=transition_txn,handoff_geometry=handoff_geometry',1)
need('Core.commit_transition_edge(st,p.transition_txn',1)
need('Core.commit_transition_edge(st,tx,now,{',1)
need('Core.abort_transition_txn(st,p.transition_txn,"OWN_',1)
need('Core.mark_handoff_committed(st,current,successor',1)

need('if not tx or (tx.state~="SUBMITTED" and tx.state~="OBSERVED")',1)
need('if S.pending_by_uid[st.uid] or st.transition_txn then return end',1)
need('if st.transition_txn then return BSC_HUGE,"TRANSITION_TXN_OPEN" end',1)
# The old pre-ACK direct commit call in dispatch must be gone.
if 'if previous and previous.type=="MOVE" then Core.mark_handoff_committed(st,previous,a,reason,now,g) end' in s:
    fail('dispatch still commits handoff before ACK')
# T1.6 is permission-neutral: later T2 behavior remains inactive.
for forbidden in ('zone="ADOPT_ONLY"','ATTACK_TERMINAL_CORRIDOR','NATIVE_MOVE_PASSTHROUGH'):
    if forbidden in s: fail('T1.6 accidentally activates staged T2 behavior: '+forbidden)
need('if successor.type=="MOVE" then',1)
need('d.zone="HARD_BLOCK";d.reason="CANONICAL_INTERMEDIATE_ACTIONS_OWED"')
print('PASS: T1.6 transition transaction structural contract; T1.5 permission remains unchanged')
