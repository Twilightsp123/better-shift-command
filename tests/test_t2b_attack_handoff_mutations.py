from pathlib import Path
import subprocess,sys,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1]
def lua_cmd():
    for n in ('lua5.1','texlua','lua5.3','lua'):
        p=shutil.which(n)
        if p:return [p]
    p=shutil.which('luatex');return [p,'--luaonly'] if p else None
L=lua_cmd()
if not L: raise SystemExit('FAIL Lua interpreter missing')
def mutate(module,test,mutants):
    src=(ROOT/module).read_text()
    base=subprocess.run(L+[str(ROOT/test),str(ROOT/module)],cwd=ROOT,capture_output=True,text=True)
    if base.returncode: raise SystemExit('BASE FAIL '+module+'\n'+base.stdout+base.stderr)
    for name,a,b in mutants:
        if a not in src: raise SystemExit('ANCHOR MISSING '+name)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'m.lua';p.write_text(src.replace(a,b,1))
            r=subprocess.run(L+[str(ROOT/test),str(p)],cwd=ROOT,capture_output=True,text=True)
            if r.returncode==0: raise SystemExit('MUTANT SURVIVED '+name)
            print('CAUGHT '+name)
mutate('source/arrival_brake_g11.lua','tests/test_arrival_brake_g11.lua',[
 ('drop_ground_decel','ground[1]>ground[2] and ground[2]>ground[3]','true'),
 ('drop_approach_decel','approach[1]>approach[2] and approach[2]>approach[3]','true'),
 ('issue_uses_sync','r.issue_coherence_limit=tol','r.issue_coherence_limit=tol+r.sync_margin'),
 ('adopt_loses_sync','r.adopt_coherence_limit=tol+r.sync_margin','r.adopt_coherence_limit=tol')])
mutate('source/t2b_attack_policy_v2.lua','tests/test_t2b_attack_policy_v2.lua',[
 ('allow_skip','if f.immediate_successor~=true then','if false and f.immediate_successor~=true then'),
 ('ignore_target','if f.target_exact~=true then','if false and f.target_exact~=true then'),
 ('ignore_debt','if f.prior_route_clear~=true then','if false and f.prior_route_clear~=true then'),
 ('ignore_exit','if f.exit_route==true then','if false and f.exit_route==true then'),
 ('sync_widens_issue','f.remaining<=f.waypoint_tolerance then','f.remaining<=f.waypoint_tolerance+sync then'),
 ('adopt_unbounded','f.remaining<=f.waypoint_tolerance+sync then','true then')])
mutate('source/t2b_edge_decision_cache.lua','tests/test_t2b_edge_decision_cache.lua',[
 ('ignore_edge','if c.gen~=q.gen or c.current_action_id~=q.current_action_id or c.successor_action_id~=q.successor_action_id then','if false and (c.gen~=q.gen or c.current_action_id~=q.current_action_id or c.successor_action_id~=q.successor_action_id) then'),
 ('ignore_age','if age>q.current_step_ms then','if false and age>q.current_step_ms then'),
 ('geometry_alias','geometry=gc(e.geometry)','geometry=e.geometry')])
print('PASS: G1.1/T2-B/cache mutants caught')
