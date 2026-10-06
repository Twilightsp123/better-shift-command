from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'source/better_shift_command.lua'
s=p.read_text(encoding='utf-8')
def fail(m): print('FAIL '+m); raise SystemExit(1)
def need(t,n=1):
    c=s.count(t)
    if c!=n: fail(f'{t} count={c}, expected={n}')
need('geometry_stage=ARRIVAL_BRAKE_G1_OBSERVE_ONLY')
need('-- ARRIVAL_BRAKE_G1_MODULE_BEGIN')
need('VERSION="ARRIVAL_BRAKE_G1"')
need('R1.ArrivalBrake.observe(st.motion_samples,a.pos,action_runtime(a).entered_ms)')
need('motion_samples={}')
need('arrival_brake_preempt_distance=brake.preempt_distance')
need('arrival_sync_margin=brake.sync_margin')
if re.search(r'arrival_brake|ArrivalBrake', s[s.index('function R1.TransitionPolicy.evaluate('):s.index('local function attack_metrics',s.index('function R1.TransitionPolicy.evaluate('))], re.I):
    fail('observer leaked into TransitionPolicy permission')
if 'ATTACK_TERMINAL_CORRIDOR' in s: fail('G1 activated T2-B')
if 'NATIVE_MOVE_PASSTHROUGH' in s: fail('G1 activated T2-MOVE bypass')
print('PASS: ARRIVAL_BRAKE_G1 is wired as observation-only geometry data')
