from pathlib import Path
import subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
controller=(ROOT/'source/better_shift_command.lua').read_text(encoding='utf-8')
contract=ROOT/'tests/test_execution_lineage_t15_contract.py'
python=sys.executable
mutants=[
 ('drop_capture_identity','capture_identity={lineage="PLAYER_NATIVE"','capture_identity={lineage="MUTANT_NATIVE"'),
 ('ignore_issued_identity','local issued=rt.issued_identity','local issued=nil -- mutant'),
 ('drop_issued_identity_record','accepted_rt.issued_identity={lineage="BSC_ISSUED"','accepted_rt.mutant_identity={lineage="BSC_ISSUED"'),
 ('drop_previous_lane_snapshot','previous_execution_lane=st.execution_lane','previous_lane_snapshot=st.execution_lane'),
 ('drop_ack_lane_switch','st.idx=p.idx; st.owned=true;st.execution_lane="BSC_ISSUED"','st.idx=p.idx; st.owned=true;st.execution_lane="PLAYER_NATIVE"'),
 ('drop_reconcile_lineage_context','successor_index=future_index,execution_lineage=future_lineage','successor_index=future_index,execution_lineage=nil'),
 ('drop_rollback_lineage_log','execution_lineage="..clean(execution_lineage)','execution_lineage="..clean(nil)'),
]
base=subprocess.run([python,str(contract)],cwd=ROOT,capture_output=True,text=True)
if base.returncode:
    raise SystemExit('BASELINE DID NOT PASS\n'+base.stdout+base.stderr)
for name,before,after in mutants:
    if before not in controller: raise SystemExit('MUTATION ANCHOR MISSING: '+name)
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'mutant.lua';p.write_text(controller.replace(before,after,1),encoding='utf-8')
        r=subprocess.run([python,str(contract),str(p)],cwd=ROOT,capture_output=True,text=True)
        if r.returncode==0: raise SystemExit('MUTANT SURVIVED: '+name)
        failed=[x for x in r.stdout.splitlines() if x.startswith('FAIL ')]
        if not failed: raise SystemExit('INFRASTRUCTURE FAILURE: '+name+'\n'+r.stdout+r.stderr)
        print('CAUGHT '+name+' :: '+failed[0])
print(f'TOTAL {len(mutants)} T1.5 MUTANTS CAUGHT')
