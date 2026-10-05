from pathlib import Path
import shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
def lua_cmd():
    for n in ('lua5.1','texlua','lua5.3','lua'):
        p=shutil.which(n)
        if p:return [p]
    p=shutil.which('luatex');return [p,'--luaonly'] if p else None
LUA=lua_cmd()
if not LUA: raise SystemExit('FAIL: Lua interpreter missing')
probe=ROOT/'tests/probe_transition_policy_t1.lua'
fixture=ROOT/'tests/fixture.lua'
baseline=ROOT/'archive/tpol_t1_pre_shared_evaluator/source/better_shift_command.lua'
current=ROOT/'source/better_shift_command.lua'
def run(controller):
    r=subprocess.run(LUA+[str(probe),str(controller),str(fixture)],cwd=ROOT,capture_output=True,text=True)
    if r.returncode:
        raise SystemExit('FAIL: probe failed for '+str(controller)+'\n'+r.stdout+r.stderr)
    return [x for x in r.stdout.splitlines() if x.startswith('RESULT ')]
a,b=run(baseline),run(current)
if a!=b:
    print('FAIL: T1 changed transition behavior')
    print('--- baseline');print('\n'.join(a));print('--- current');print('\n'.join(b))
    raise SystemExit(1)
if len(a)!=5: raise SystemExit(f'FAIL: expected 5 probe rows, got {len(a)}')
print('PASS: T1 old/new transition behavior equivalence')
for row in b: print(row)