from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
mutated=len(sys.argv)>1
controller=Path(sys.argv[1]) if mutated else ROOT/'source/better_shift_command.lua'
s=controller.read_text(encoding='utf-8')

def fail(msg):
    print('FAIL '+msg)
    raise SystemExit(1)

if not mutated:
    src=(ROOT/'src/better_shift_command.lua').read_text(encoding='utf-8')
    tpl=(ROOT/'src/better_shift_command_selfcontained.template.lua').read_text(encoding='utf-8')
    if s != src: fail('source/src controller mirrors diverged')
else:
    tpl=''
if s.count('function R1.TransitionPolicy.evaluate(')!=1:
    fail('shared TransitionPolicy compatibility evaluator missing or duplicated')
if 'function R1.TransitionPolicy.evaluate_edge(' in s:
    if s.count('consumer="PROACTIVE"')!=2:
        fail('advance must project both MOVE and ATTACK through shared edge policy')
    if s.count('consumer="NATIVE_RECONCILE"')!=1:
        fail('SC6 must project exact native successor through shared edge policy')
    if s.count('consumer="SCHEDULER"')!=0:
        fail('T1.7 scheduler must read consumer-neutral edge policy directly')
    if s.count('R1.TransitionPolicy.evaluate_edge(st,cur,')<5:
        fail('runtime consumers do not all read shared edge evaluator')
else:
    if s.count('consumer="PROACTIVE"')!=2:
        fail('advance must route both MOVE and ATTACK through evaluator')
    if s.count('consumer="NATIVE_RECONCILE"')!=1:
        fail('SC6 must route exact native successor through evaluator')
    if s.count('consumer="SCHEDULER"')!=2:
        fail('scheduler must route both MOVE and ATTACK through evaluator')
if 'T1_BEHAVIOR_NEUTRAL' not in s:
    fail('missing explicit T1 behavior-neutral marker')
if 'if future_index and current_index and future_index~=current_index+1 then' not in s and 'if future_index and future_index~=current_index+1 then' not in s:
    fail('H2 future-skip hard guard missing from shared transition path')
if 'zone="ADOPT_ONLY"' in s or "zone='ADOPT_ONLY'" in s:
    fail('T1 must not activate ADOPT_ONLY behavior')
if not mutated:
    for token in ('function R1.TransitionPolicy.evaluate(', 'T1_BEHAVIOR_NEUTRAL'):
        if token not in tpl: fail('template missing '+token)
print('PASS: T1 shared TransitionPolicy structural contract')