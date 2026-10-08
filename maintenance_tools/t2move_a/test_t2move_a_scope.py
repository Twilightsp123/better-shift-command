from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
controller=(ROOT/'source/better_shift_command.lua').read_text(encoding='utf-8')
mirror=(ROOT/'src/better_shift_command.lua').read_text(encoding='utf-8')
template=(ROOT/'src/better_shift_command_selfcontained.template.lua').read_text(encoding='utf-8')
assert controller==mirror, 'controller mirrors diverged'
for x in (controller,mirror,template):
    assert 'T2MOVE_A_SHADOW_1' not in x, 'shadow implementation leaked into controller'
    assert 'NATIVE_MOVE_PASSTHROUGH' not in x, 'native MOVE passthrough is forbidden'
    assert 'd.adopt_window=transition_envelope(false,"CANONICAL_INTERMEDIATE_ACTIONS_OWED",true)' in x, 'MOVE adopt unexpectedly enabled'
assert 'T2B_G11_DUAL_ENVELOPE_CANDIDATE' in controller, 'T2B frozen candidate missing'
print('PASS: T2-MOVE-A remains pure shadow; T2-B unchanged, MOVE adopt closed')
