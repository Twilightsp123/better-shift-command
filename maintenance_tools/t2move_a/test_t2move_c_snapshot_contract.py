"""Fail-closed integration inventory. Report current missing fields as a blocker,
not as a passed controller integration. Run against current repository source.
"""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
controller=(ROOT/'source/better_shift_command.lua').read_text(encoding='utf-8')
mirror=(ROOT/'src/better_shift_command.lua').read_text(encoding='utf-8')
template=(ROOT/'src/better_shift_command_selfcontained.template.lua').read_text(encoding='utf-8')
assert controller==mirror, 'source/src controller mirrors diverged'
needed={'remaining','leg','next_leg','progress','route_min_progress','threshold','stall',
        'route_mode','route_debt_mode','arrival_brake_ready','arrival_sync_margin',
        'cut_error','cut_safe_limit','cut_tolerance','corner_window','corner_window_base',
        'corner_window_early'}
for label,src in [('source',controller),('template',template)]:
    a='local function transition_geometry_snapshot(g)'
    b='function Core.begin_transition_txn('
    assert src.count(a)==1 and src.count(b)==1, (label,'snapshot boundary mismatch')
    block=src.split(a,1)[1].split(b,1)[0]
    included=set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*g\.([a-zA-Z_][a-zA-Z0-9_]*)',block))
    included={k for k,v in included if k==v}
    missing=sorted(needed-included)
    print(f'{label} snapshot fields {len(included)}; T2-MOVE-C needed missing={missing}')
    assert missing, 'unexpectedly complete: do not activate without runtime integration review'
    assert {'leg','progress','route_min_progress','cut_safe_limit','threshold','stall'}<=set(missing), 'known critical missing-field audit drift'
    assert 'T2MOVE_C_TXN_SHADOW_1' not in src, 'shadow has leaked into live controller'
    assert 'd.adopt_window=transition_envelope(false,"CANONICAL_INTERMEDIATE_ACTIONS_OWED",true)' in src, 'MOVE adoption unexpectedly activated'
assert 'NATIVE_MOVE_PASSTHROUGH' not in controller
assert 'T2B_G11_DUAL_ENVELOPE_CANDIDATE' in controller
assert 'function Core.begin_transition_txn(' in controller and 'function Core.commit_transition_edge(' in controller
print('PASS: critical integration gap is documented; live MOVE adopt remains closed')
