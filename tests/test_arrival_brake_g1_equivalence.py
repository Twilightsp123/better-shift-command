from pathlib import Path
import shutil,subprocess,sys,re
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'archive/geom_g1_pre_arrival_brake/source/better_shift_command.lua'
CUR=ROOT/'archive/t2b_pre_terminal_attack/source/better_shift_command.lua'
PROBE=ROOT/'tests/probe_transition_policy_t1.lua';FIX=ROOT/'tests/fixture.lua'
def fail(m): print('FAIL '+m); raise SystemExit(1)
def lua_cmd():
    for n in ('lua5.1','texlua','lua5.3','lua'):
        p=shutil.which(n)
        if p:return [p]
    p=shutil.which('luatex');return [p,'--luaonly'] if p else None
L=lua_cmd()
if not L: fail('Lua interpreter missing')
def run(p):
    r=subprocess.run(L+[str(PROBE),str(p),str(FIX)],cwd=ROOT,capture_output=True,text=True)
    if r.returncode: fail('probe failed '+str(p)+'\n'+r.stdout+r.stderr)
    return [x for x in r.stdout.splitlines() if x.startswith('RESULT ')]
a,b=run(BASE),run(CUR)
if a!=b: fail('G1 changed transition permission/output\nBASE\n'+'\n'.join(a)+'\nCUR\n'+'\n'.join(b))
def cfg(t):
    a=t.find('local CFG=');b=t.find('\n}',a);return dict(re.findall(r'([A-Za-z0-9_]+)\s*=\s*([-+]?[0-9]+(?:\.[0-9]+)?)',t[a:b+2]))
old=BASE.read_text(encoding='utf-8');new=CUR.read_text(encoding='utf-8')
if cfg(old)!=cfg(new): fail('G1 changed CFG scalar values')
for token in ('ATTACK_TERMINAL_CORRIDOR','NATIVE_MOVE_PASSTHROUGH'):
    if token in new: fail('G1 activated T2 behavior '+token)
print('PASS: ARRIVAL_BRAKE_G1 observes motion with zero permission/CFG change')
for row in b: print(row)
