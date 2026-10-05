from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
mutated=len(sys.argv)>1
controller=Path(sys.argv[1]) if mutated else ROOT/'source/better_shift_command.lua'
s=controller.read_text(encoding='utf-8')
def fail(msg): print('FAIL '+msg); raise SystemExit(1)
if not mutated:
    src=(ROOT/'src/better_shift_command.lua').read_text(encoding='utf-8')
    tpl=(ROOT/'src/better_shift_command_selfcontained.template.lua').read_text(encoding='utf-8')
    if s != src: fail('source/src controller mirrors diverged')
else: tpl=''
if s.count('function R1.TransitionPolicy.evaluate(')!=1: fail('shared TransitionPolicy evaluator missing or duplicated')
if s.count('R1.TransitionPolicy.evaluate(st,')!=6: fail('advance/SC6/scheduler must keep five shared evaluator call sites')
for legacy in ('consumer="PROACTIVE"','consumer="NATIVE_RECONCILE"','consumer="SCHEDULER"','context.consumer'):
    if legacy in s: fail('consumer-specific policy permission path remains: '+legacy)
if 'if current_index and successor_index and successor_index~=current_index+1 then' not in s: fail('immediate-successor invariant missing')
if 'T1_BEHAVIOR_NEUTRAL' not in s: fail('missing explicit T1 behavior-neutral lineage marker')
if not mutated:
    for token in ('function R1.TransitionPolicy.evaluate(', 'T1_BEHAVIOR_NEUTRAL'):
        if token not in tpl: fail('template missing '+token)
print('PASS: T1 shared TransitionPolicy structural contract; later consumer-neutral stages preserve one evaluator')
