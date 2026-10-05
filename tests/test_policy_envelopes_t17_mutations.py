from pathlib import Path
import subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
controller=(ROOT/'source/better_shift_command.lua').read_text(encoding='utf-8')
contract=ROOT/'tests/test_policy_envelopes_t17_contract.py'
python=sys.executable
mutants=[
 ('drop_envelope_stage','envelope_stage=TPOL_T1_7_CONSUMER_NEUTRAL','envelope_stage=MUTANT'),
 ('reintroduce_consumer_permission','context=context or {}','context=context or {}\n    local consumer=context.consumer'),
 ('drop_issue_envelope','issue_window=transition_envelope(false,"TRANSITION_WAIT",false)','issue_window=nil'),
 ('drop_adopt_envelope','adopt_window=transition_envelope(false,"TRANSITION_WAIT",false)','adopt_window=nil'),
 ('open_legacy_move_adopt','d.adopt_window=transition_envelope(false,"CANONICAL_INTERMEDIATE_ACTIONS_OWED",true)','d.adopt_window=transition_envelope(true,"MUTANT_MOVE_ADOPT",false)'),
 ('native_bypasses_adopt_envelope','local adopt_window=decision.adopt_window or {open=false,reason=decision.reason,hard_violation=decision.hard_violation}','local adopt_window={open=decision.zone=="ISSUE_READY",reason=decision.reason,hard_violation=decision.hard_violation}'),
 ('allow_future_skip','if current_index and successor_index and successor_index~=current_index+1 then','if false and current_index and successor_index and successor_index~=current_index+1 then'),
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
