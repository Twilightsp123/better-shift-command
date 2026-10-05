from pathlib import Path
import shutil,subprocess,sys,re
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'archive/tpol_t17_pre_policy_envelopes/source/better_shift_command.lua'
CUR=ROOT/'source/better_shift_command.lua'
PROBE=ROOT/'tests/probe_transition_policy_t1.lua'
FIX=ROOT/'tests/fixture.lua'
def fail(msg): print('FAIL '+msg); raise SystemExit(1)
def lua_cmd():
    for n in ('lua5.1','texlua','lua5.3','lua'):
        p=shutil.which(n)
        if p:return [p]
    p=shutil.which('luatex');return [p,'--luaonly'] if p else None
L=lua_cmd()
if not L: fail('Lua interpreter missing')
def run(controller):
    r=subprocess.run(L+[str(PROBE),str(controller),str(FIX)],cwd=ROOT,capture_output=True,text=True)
    if r.returncode: fail('probe failed for '+str(controller)+'\n'+r.stdout+r.stderr)
    return [x for x in r.stdout.splitlines() if x.startswith('RESULT ')]
old,new=run(BASE),run(CUR)
if old!=new:
    print('FAIL: T1.7 changed transition permission/output')
    print('--- T1.6');print('\n'.join(old));print('--- T1.7');print('\n'.join(new));raise SystemExit(1)
def cfg_scalars(text):
    start=text.find('local CFG=');end=text.find('\n}',start);block=text[start:end+2]
    return dict(re.findall(r'([A-Za-z0-9_]+)\s*=\s*([-+]?[0-9]+(?:\.[0-9]+)?)',block))
a=BASE.read_text(encoding='utf-8');b=CUR.read_text(encoding='utf-8')
if cfg_scalars(a)!=cfg_scalars(b): fail('CFG scalar values changed during T1.7')
for token in ('ATTACK_TERMINAL_CORRIDOR','NATIVE_MOVE_PASSTHROUGH'):
    if token in b: fail('T1.7 activated staged T2 behavior: '+token)
print('PASS: T1.7 permission equivalence; T1.6 probe output and CFG scalars unchanged')
for row in new: print(row)
