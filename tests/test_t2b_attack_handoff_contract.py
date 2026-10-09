from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
controller=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'source/better_shift_command.lua'
base=ROOT/'archive/t2b_g11_pre_rework/source/better_shift_command.lua'
s=controller.read_text(encoding='utf-8')
def fail(m): print('FAIL '+m); raise SystemExit(1)
def need(t,n=None):
    c=s.count(t)
    if c==0: fail('missing '+t)
    if n is not None and c!=n: fail(f'{t} count={c}, expected {n}')
def block(text,a,b):
    i=text.find(a)
    if i<0: fail('missing '+a)
    j=text.find(b,i+len(a))
    if j<0: fail('missing end '+b)
    return text[i:j]
def cfg(text):
    a=text.find('local CFG=');b=text.find('\n}',a)
    return dict(re.findall(r'([A-Za-z0-9_]+)\s*=\s*([-+]?[0-9]+(?:\.[0-9]+)?)',text[a:b+2]))
need('t2b_stage=T2B_G11_DUAL_ENVELOPE_CANDIDATE',1)
need('VERSION="ARRIVAL_BRAKE_G1_1"',1);need('VERSION="T2B_ATTACK_POLICY_2"',1);need('VERSION="T2B_EDGE_DECISION_CACHE_1"',1)
need('ATTACK_PATH_SAFE_HYSTERESIS');need('ATTACK_TERMINAL_HYSTERESIS');need('NATIVE_ADVANCED_WITHOUT_FRESH_T2B_DECISION');need('CACHE_OLDER_THAN_ONE_OBSERVED_POLL')
need('local clear=block_route_clear(st,current)',1)
need('successor.type=="ATTACK" and g.current_credit=="ATTACK_TERMINAL_HANDOFF"',1)
need('fresh_issue=fresh_decision and fresh_decision.issue_window',1)
need('decision.adopt_window or {open=false,reason=decision.reason,hard_violation=decision.hard_violation}',1)
need('d.adopt_window=transition_envelope(false,"CANONICAL_INTERMEDIATE_ACTIONS_OWED",true)',1)
if 'R1.AttackHandoff' in s: fail('legacy ready-boolean AttackHandoff survived')
if 'NATIVE_MOVE_PASSTHROUGH' in s: fail('T2-MOVE passthrough activated')
if s.count('R1.TransitionPolicy.evaluate(st,')!=11: fail('expected 11 shared evaluator calls (H4 fresh MOVE postdrain) including E native MOVE adoption')
old=base.read_text(encoding='utf-8')
if block(s,'local function route_handoff_ready(', '\n\n-- T1.6 Transition Transaction') != block(old,'local function route_handoff_ready(', '\n\n-- T1.6 Transition Transaction'): fail('MOVE->MOVE route_handoff_ready changed')
if cfg(s)!=cfg(old): fail('CFG scalar values changed')
commit=block(s,'function Core.commit_transition_edge(', '\nfunction Core.observe_move_completion')
if 'ATTACK_TERMINAL_HANDOFF' not in commit: fail('terminal credit not commit-only')
reconcile=block(s,'function Core.reconcile_native_successor(', '\nlocal function advance(st,now)')
for t in ('R1.T2BEdgeCache.capture','R1.T2BEdgeCache.read','NATIVE_ADVANCED_WITHOUT_FRESH_T2B_DECISION'):
    if t not in reconcile: fail('reconcile missing '+t)
print('PASS: G1.1/T2-B dual-envelope current-source contract')
