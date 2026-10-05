from pathlib import Path
import shutil,subprocess,re
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'archive/tpol_t17_pre_consumer_neutral/source/better_shift_command.lua'
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

def run_probe(controller):
    r=subprocess.run(L+[str(PROBE),str(controller),str(FIX)],cwd=ROOT,capture_output=True,text=True)
    if r.returncode: fail('probe failed for '+str(controller)+'\n'+r.stdout+r.stderr)
    return [x for x in r.stdout.splitlines() if x.startswith('RESULT ')]
old,new=run_probe(BASE),run_probe(CUR)
if old!=new:
    print('FAIL T1.7 changed deterministic transition output')
    print('--- baseline');print('\n'.join(old));print('--- current');print('\n'.join(new));raise SystemExit(1)

def cfg_scalars(text):
    start=text.find('local CFG=');end=text.find('\n}',start);block=text[start:end+2]
    return dict(re.findall(r'([A-Za-z0-9_]+)\s*=\s*([-+]?[0-9]+(?:\.[0-9]+)?)',block))
a=BASE.read_text(encoding='utf-8');b=CUR.read_text(encoding='utf-8')
if cfg_scalars(a)!=cfg_scalars(b): fail('CFG scalar values changed during T1.7')
for token in ('zone="ADOPT_ONLY"','ATTACK_TERMINAL_CORRIDOR','NATIVE_MOVE_PASSTHROUGH'):
    if token in b: fail('T1.7 activated staged behavior: '+token)
for sig,end in [
 ('local function route_handoff_ready(', '\nlocal function transition_handoff_ready'),
 ('local function attack_geometry(', '\nlocal function attack_brake_state'),
]:
    aa=a[a.find(sig):a.find(end,a.find(sig))]
    bb=b[b.find(sig):b.find(end,b.find(sig))]
    if aa!=bb: fail(sig+' changed during T1.7')
print('PASS: T1.7 permission equivalence; deterministic T1/T1.6 behavior and CFG unchanged')
for row in new: print(row)
