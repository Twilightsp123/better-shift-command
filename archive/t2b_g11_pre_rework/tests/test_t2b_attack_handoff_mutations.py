from pathlib import Path
import subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
module=(ROOT/'source/t2b_attack_handoff.lua').read_text(encoding='utf-8')
test=ROOT/'tests/test_t2b_attack_handoff.lua'
def lua_cmd():
    import shutil
    for n in ('lua5.1','texlua','lua5.3','lua'):
        p=shutil.which(n)
        if p:return [p]
    p=shutil.which('luatex');return [p,'--luaonly'] if p else None
L=lua_cmd()
if not L: raise SystemExit('FAIL Lua interpreter missing')
base=subprocess.run(L+[str(test),str(ROOT/'source/t2b_attack_handoff.lua')],cwd=ROOT,capture_output=True,text=True)
if base.returncode: raise SystemExit('BASELINE DID NOT PASS\n'+base.stdout+base.stderr)
mutants=[
 ('ignore_prior_debt','if f.prior_clear~=true then','if false and f.prior_clear~=true then'),
 ('ignore_exit_strictness','if f.exit_route==true then','if false and f.exit_route==true then'),
 ('ignore_braking','if f.arrival_braking~=true then','if false and f.arrival_braking~=true then'),
 ('ignore_brake_boundary','if f.brake_boundary~=true then','if false and f.brake_boundary~=true then'),
 ('path_safe_unconditional','if f.path_error<=f.waypoint_tolerance then','if true or f.path_error<=f.waypoint_tolerance then'),
 ('terminal_unconditional','if f.remaining<=d.terminal_limit then','if true or f.remaining<=d.terminal_limit then'),
 ('inflate_sync_margin','local sync=finite(f.sync_margin) and math.max(0,f.sync_margin) or 0','local sync=(finite(f.sync_margin) and math.max(0,f.sync_margin) or 0)+10'),
]
for name,a,b in mutants:
    if a not in module: raise SystemExit('MUTATION ANCHOR MISSING '+name)
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'mutant.lua';p.write_text(module.replace(a,b,1),encoding='utf-8')
        r=subprocess.run(L+[str(test),str(p)],cwd=ROOT,capture_output=True,text=True)
        if r.returncode==0: raise SystemExit('MUTANT SURVIVED '+name)
        if 'FAIL ' not in r.stdout: raise SystemExit('INFRASTRUCTURE FAILURE '+name+'\n'+r.stdout+r.stderr)
        print('CAUGHT '+name)
print(f'TOTAL {len(mutants)} T2-B POLICY MUTANTS CAUGHT')
