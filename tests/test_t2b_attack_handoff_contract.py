from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
controller=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'source/better_shift_command.lua'
pre=ROOT/'archive/t2b_pre_terminal_attack/source/better_shift_command.lua'
s=controller.read_text(encoding='utf-8')
old=pre.read_text(encoding='utf-8')
def fail(m): print('FAIL '+m); raise SystemExit(1)
def need(t,n=None):
    c=s.count(t)
    if c==0: fail('missing '+t)
    if n is not None and c!=n: fail(f'{t} count={c}, expected {n}')
need('t2b_stage=T2B_ARRIVAL_BRAKE_HANDOFF_CANDIDATE',1)
need('VERSION="T2B_ATTACK_HANDOFF_1"',1)
need('local function attack_transition_handoff_ready(',1)
need('arrival_braking=g.arrival_braking==true',1)
need('brake_boundary=g.arrival_brake_boundary==true',1)
need('sync_margin=g.arrival_sync_margin')
need('d.current_credit=g.current_credit',1)
need('d.current_credit=="ATTACK_TERMINAL_HANDOFF"',1)
need('successor.type=="ATTACK" and g.current_credit=="ATTACK_TERMINAL_HANDOFF"',1)
need('local fresh_decision=fresh and R1.TransitionPolicy.evaluate(',1)
need('fresh.current_credit=fresh_decision.current_credit',1)
need('local commit_reason=decision.current_credit or why',1)
need('ATTACK_PATH_SAFE')
need('ATTACK_TERMINAL_CORRIDOR')
if s.count('R1.TransitionPolicy.evaluate(st,')!=7: fail('expected 7 shared evaluator call sites including post-drain revalidation')
if 'NATIVE_MOVE_PASSTHROUGH' in s: fail('T2-B must not activate Native MOVE passthrough')
if 'd.adopt_window=transition_envelope(false,"CANONICAL_INTERMEDIATE_ACTIONS_OWED",true)' not in s:
    fail('T2-MOVE must remain inactive')
def block(text,a,b):
    i=text.find(a)
    if i<0: fail('missing '+a)
    j=text.find(b,i+len(a))
    if j<0: fail('missing end '+b)
    return text[i:j]
if block(s,'local function route_handoff_ready(', '\n\n-- T1.6 Transition Transaction') != block(old,'local function route_handoff_ready(', '\n\n-- T1.6 Transition Transaction'):
    fail('T2-B changed MOVE->MOVE route_handoff_ready')
if block(s,'local function attack_geometry(', '\nlocal function attack_brake_state') != block(old,'local function attack_geometry(', '\nlocal function attack_brake_state'):
    fail('T2-B changed legacy attack_geometry telemetry')
def cfg(t):
    a=t.find('local CFG=');b=t.find('\n}',a)
    return dict(re.findall(r'([A-Za-z0-9_]+)\s*=\s*([-+]?[0-9]+(?:\.[0-9]+)?)',t[a:b+2]))
if cfg(s)!=cfg(old): fail('T2-B introduced/tuned CFG scalar values')
helper=block(s,'-- T2B_ATTACK_HANDOFF_MODULE_BEGIN','-- T2B_ATTACK_HANDOFF_MODULE_END')
for forbidden in ('attack_lead_straight','attack_lead_uturn','attack_speed_seconds','attack_execution_cap','route_corner_'):
    if forbidden in helper: fail('T2-B policy depends on legacy tuned threshold '+forbidden)
print('PASS: T2-B semantic-corridor + arrival-brake contract; MOVE->MOVE/CFG/native-MOVE permission preserved')
