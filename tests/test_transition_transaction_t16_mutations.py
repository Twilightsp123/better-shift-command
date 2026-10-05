from pathlib import Path
import subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
controller=(ROOT/'source/better_shift_command.lua').read_text(encoding='utf-8')
contract=ROOT/'tests/test_transition_transaction_t16_contract.py'
python=sys.executable
mutants=[
 ('drop_pending_transaction','transition_txn=transition_txn,handoff_geometry=handoff_geometry','mutant_txn=transition_txn,handoff_geometry=handoff_geometry'),
 ('drop_ack_shared_commit','Core.commit_transition_edge(st,p.transition_txn','Core.mutant_commit_edge(st,p.transition_txn'),
 ('drop_native_shared_commit','Core.commit_transition_edge(st,tx,now,{owned=false','Core.mutant_commit_edge(st,tx,now,{owned=false'),
 ('drop_reject_abort','Core.abort_transition_txn(st,p.transition_txn,"OWN_','Core.mutant_abort_transition_txn(st,p.transition_txn,"OWN_'),
 ('allow_authorized_commit','if not tx or (tx.state~="SUBMITTED" and tx.state~="OBSERVED")','if not tx or (tx.state~="AUTHORIZED" and tx.state~="SUBMITTED" and tx.state~="OBSERVED")'),
 ('drop_advance_txn_lock','if S.pending_by_uid[st.uid] or st.transition_txn then return end','if S.pending_by_uid[st.uid] then return end'),
 ('restore_pre_ack_handoff_commit','S.pending_by_uid[st.uid]=pending;S.pending_by_issue[issue]=pending;S.pending_count=S.pending_count+1','S.pending_by_uid[st.uid]=pending;S.pending_by_issue[issue]=pending;S.pending_count=S.pending_count+1\n    local previous=st.plan[pending.previous_idx]; if previous and previous.type=="MOVE" then Core.mark_handoff_committed(st,previous,a,reason,now,g) end'),
]
base=subprocess.run([python,str(contract)],cwd=ROOT,capture_output=True,text=True)
if base.returncode: raise SystemExit('BASELINE DID NOT PASS\n'+base.stdout+base.stderr)
for name,before,after in mutants:
    if before not in controller: raise SystemExit('MUTATION ANCHOR MISSING: '+name)
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'mutant.lua';p.write_text(controller.replace(before,after,1),encoding='utf-8')
        r=subprocess.run([python,str(contract),str(p)],cwd=ROOT,capture_output=True,text=True)
        if r.returncode==0: raise SystemExit('MUTANT SURVIVED: '+name)
        failed=[x for x in r.stdout.splitlines() if x.startswith('FAIL ')]
        if not failed: raise SystemExit('INFRASTRUCTURE FAILURE: '+name+'\n'+r.stdout+r.stderr)
        print('CAUGHT '+name+' :: '+failed[0])
print(f'TOTAL {len(mutants)} T1.6 MUTANTS CAUGHT')
