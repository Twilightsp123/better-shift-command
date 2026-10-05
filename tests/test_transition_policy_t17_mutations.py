from pathlib import Path
import subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
controller=(ROOT/'source/better_shift_command.lua').read_text(encoding='utf-8')
contract=ROOT/'tests/test_transition_policy_t17_contract.py'
python=sys.executable
mutants=[
 ('consumer_leaks_into_edge','function R1.TransitionPolicy.evaluate_edge(st,current,successor,g)\n','function R1.TransitionPolicy.evaluate_edge(st,current,successor,g)\n    local consumer="PROACTIVE"\n'),
 ('widen_adopt_early','d.adopt_ready=d.issue_ready','d.adopt_ready=true'),
 ('activate_adopt_only','d.adopt_window.ready=d.adopt_ready;d.adopt_window.reason=issue_reason','d.adopt_window.ready=d.adopt_ready;d.adopt_window.reason=issue_reason\n    if d.adopt_ready and not d.issue_ready then d.zone="ADOPT_ONLY" end'),
 ('drop_native_projection','local decision=R1.TransitionPolicy.project(edge,{consumer="NATIVE_RECONCILE"','local decision=edge -- consumer="NATIVE_RECONCILE"'),
 ('drop_proactive_projection','local decision=R1.TransitionPolicy.project(edge,{consumer="PROACTIVE"})','local decision=edge'),
 ('scheduler_becomes_consumer','local decision=R1.TransitionPolicy.evaluate_edge(st,cur,nexta,g)','local decision=R1.TransitionPolicy.project(R1.TransitionPolicy.evaluate_edge(st,cur,nexta,g),{consumer="SCHEDULER"})'),
 ('drop_h2_projection_guard','if future_index and current_index and future_index~=current_index+1 then','if false and future_index and current_index and future_index~=current_index+1 then'),
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
print(f'TOTAL {len(mutants)} T1.7 MUTANTS CAUGHT')
