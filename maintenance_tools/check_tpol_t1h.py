#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
a=(R/'source/better_shift_command.lua').read_text(encoding='utf-8')
b=(R/'src/better_shift_command.lua').read_text(encoding='utf-8')
if a!=b: raise SystemExit('FAIL source/src controller mismatch')
required=[
 'policy_stage=TPOL_T1H_HIDDEN',
 'R1.Policy=(function()',
 'VERSION="TPOL_T1H_1"',
 'engagement_hold_seconds={kind="number",min=0.5,max=10.0,step=0.5}',
 'P.defaults={behavior_preset="SMOOTH",engagement_hold_seconds=3.0}',
 'function P.from_mct_values(values)',
 'function P.snapshot_hidden()',
 'CFG.attack_hold_ms=R1.Policy.active.engagement_hold_ms',
 'bridge.version()~="1.0.17-corepath-wh3-6c104-movevtfix"'
]
for x in required:
    if x not in a: raise SystemExit('FAIL missing '+x)
for forbidden in ('get_mct(',':register_mod(',':create_settings_page(',':add_new_option('):
    if forbidden in a: raise SystemExit('FAIL visible MCT wiring found '+forbidden)
schema=(R/'docs/design/MCT_POLICY_SCHEMA_D1.md').read_text(encoding='utf-8')
if '| `attack_commitment` |' in schema:
    raise SystemExit('FAIL current MCT schema still exposes old attack_commitment key')
print('PASS TPOL-T1H hidden policy contract')
print('mct_ui=NOT_REGISTERED')
print('engagement_hold_seconds_default=3.0')
print('engagement_hold_ms=3000')
print('movement_policy_fields=RESERVED_NOT_WIRED')
