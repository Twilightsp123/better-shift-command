from pathlib import Path
import subprocess,sys,tempfile,shutil
root=Path(__file__).resolve().parent
source=(root/'t2move_a_shadow.lua').read_text()
test=str(root/'test_t2move_a_shadow.lua')
lua=shutil.which('texlua') or shutil.which('lua5.1') or shutil.which('lua')
assert lua, 'Lua interpreter missing'
mutants=[
 ('skip_exact_current','e.exact_current_execution~=true','false'),
 ('skip_exact_native','q.exact_native_successor~=true','false'),
 ('skip_future','q.future_index~=q.current_index+1','false'),
 ('ignore_generation','q.gen~=c.gen','false'),
 ('ignore_lifetime','q.unit_lifetime~=c.unit_lifetime','false'),
 ('ignore_successor_id','q.successor_action_id~=c.successor_action_id','false'),
 ('ignore_cache_age','age>q.observed_step_ms','false'),
 ('ignore_route_proof','not c.issue_open or not c.route_ok or not modes[c.route_mode]','not c.issue_open'),
 ('ignore_issue','not c.issue_open or not c.route_ok or not modes[c.route_mode]','not c.route_ok or not modes[c.route_mode]'),
 ('wrong_credit','credit="REGISTER_ROUTE_OBLIGATION"','credit="STEERING_CORNER_HANDOFF"'),
 ('forgive_prior_debt','preserve_prior_debt=c.prior_debt_mode=="SOFT_PRESERVED"','preserve_prior_debt=false'),
 ('alias_geometry','geometry=g,','geometry=e.geometry,'),
]
base=subprocess.run([lua,test,str(root/'t2move_a_shadow.lua')],capture_output=True,text=True,timeout=10)
if base.returncode:raise SystemExit('BASELINE FAILED\n'+base.stdout+base.stderr)
for name,needle,replacement in mutants:
    if needle not in source:raise SystemExit('mutation source anchor missing '+name)
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'mutant.lua';p.write_text(source.replace(needle,replacement,1))
        result=subprocess.run([lua,test,str(p)],capture_output=True,text=True,timeout=10)
        if result.returncode==0:raise SystemExit('MUTANT SURVIVED '+name)
        print('CAUGHT '+name)
print('TOTAL',len(mutants),'MUTANTS CAUGHT')
