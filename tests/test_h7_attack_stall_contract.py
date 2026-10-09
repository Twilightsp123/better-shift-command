"""H7 static fail-closed guard: no WH3 runtime or Native DLL required."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "src/better_shift_command.lua").read_bytes()
mirror = (ROOT / "source/better_shift_command.lua").read_bytes()
assert src == mirror, "H7 gameplay source and canonical mirror drifted"
text = src.decode("utf-8")
start = text.index('-- T2B_ATTACK_POLICY_V2_MODULE_BEGIN')
end = text.index('-- T2B_ATTACK_POLICY_V2_MODULE_END', start)
policy = text[start:end]
for marker in (
    'f.immediate_successor~=true',
    'f.target_exact~=true',
    'f.target_terminal_abort==true',
    'f.prior_route_clear~=true',
    'f.semantic_done==true',
    'f.exit_route==true',
    'f.terminal_stall_proven==true',
    'f.remaining<=f.terminal_stall_limit',
    'ATTACK_TERMINAL_STALL_VERIFIED',
    'ATTACK_TERMINAL_HANDOFF',
):
    assert marker in policy, marker
assert policy.index('f.prior_route_clear~=true') < policy.index('f.terminal_stall_proven==true')
assert policy.index('f.exit_route==true') < policy.index('f.terminal_stall_proven==true')
for marker in (
    'g.stall==true and rt.movement_seen==true',
    'g.progress>=CFG.move_idle_finish_progress',
    'g.remaining<=terminal_limit',
    'stable_ms>=CFG.move_idle_finish_confirm_ms',
    'Core.move_idle_finish_envelope(st)',
):
    assert marker in text, marker
assert 'H7 regression' in policy
print('PASS H7 attack stall issue gate + hard-route/exit/canonical guards + source mirrors')
