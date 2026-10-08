"""T2-MOVE-E active-controller mutation tests: only real test failure counts."""
from pathlib import Path
import shutil,subprocess,tempfile,sys
ROOT=Path(__file__).resolve().parents[2]
src=(ROOT/"source/better_shift_command.lua").read_text(encoding="utf-8")
test=ROOT/"maintenance_tools/t2move_a/test_t2move_e_controller.lua"
fixture=ROOT/"tests/fixture.lua"
f_test=ROOT/"maintenance_tools/t2move_a/test_t2move_f_boundaries.lua"
lua=shutil.which("lua5.1") or shutil.which("texlua") or shutil.which("lua")
if not lua: raise SystemExit("Lua missing")
cases=[
 ("remove_D_cache","st.t2move_d_evidence=cert","st.t2move_d_evidence=nil"),
 ("skip_D_revision_debt_revalidation",'local revalidated,why=R1.T2MoveEvidence.revalidate(cached,query)','local revalidated,why=true,"MUTANT"'),
 ("bypass_A_issue_window",'if not c.issue_open or not c.route_ok or not modes[c.route_mode] then','if not c.route_ok or not modes[c.route_mode] then'),
 ("unbound_B_one_poll_margin",'if g.remaining>temporal_frontier+one_poll_travel then','if false then'),
 ("close_E_adopt_envelope",'d.adopt_window=transition_envelope(true,proof.reason,false)','d.adopt_window=transition_envelope(false,proof.reason,false)'),
 ("skip_T16_observed_state",'tx.state="OBSERVED";tx.execution_lineage=future_lineage','tx.state="AUTHORIZED";tx.execution_lineage=future_lineage'),
 ("remove_steering_completion",'elseif g.route_mode=="STEERING_CORNER" then','elseif false then'),
 ("replace_frozen_route_with_live_geometry",'g=proof and transition_geometry_snapshot(proof.geometry) or nil','g=geometry(st,future)'),
]
def invoke(path):
    # F extends the behavioral proof set; do not relax any original E mutants.
    results=[subprocess.run([lua,str(case),str(path),str(fixture)],
        cwd=ROOT,capture_output=True,text=True,timeout=20) for case in (test,f_test)]
    from types import SimpleNamespace
    return SimpleNamespace(returncode=max(x.returncode for x in results),
        stdout="\n".join(x.stdout for x in results),
        stderr="\n".join(x.stderr for x in results))
base=invoke(ROOT/"source/better_shift_command.lua")
if base.returncode:raise SystemExit("BASE FAILED\n"+base.stdout+base.stderr)
for name,old,new in cases:
    if src.count(old)!=1:raise SystemExit("ANCHOR NOT UNIQUE "+name+" count="+str(src.count(old)))
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/"mutant.lua"
        path.write_text(src.replace(old,new,1),encoding="utf-8")
        parse=subprocess.run([lua,"-e","assert(loadfile("+repr(str(path))+"))"],cwd=ROOT,capture_output=True,text=True,timeout=10)
        if parse.returncode:raise SystemExit("MUTATION SYNTAX FAILURE "+name+"\n"+parse.stderr)
        result=invoke(path)
        failures=[x for x in result.stdout.splitlines() if x.startswith(("FAIL E-RT","FAIL F-RISK"))]
        if result.returncode==0 or not failures:
            raise SystemExit(("MUTANT SURVIVED " if result.returncode==0 else "NON-BEHAVIOR MUTANT FAILURE ")+name+"\n"+result.stdout+result.stderr)
        print("CAUGHT "+name+" :: "+failures[0])
print("TOTAL",len(cases),"E CONTROLLER MUTANTS CAUGHT")
