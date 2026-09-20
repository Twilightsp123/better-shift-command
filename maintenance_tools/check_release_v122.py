#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
def fail(s): print('FAIL:',s); raise SystemExit(1)
src=(ROOT/'source/better_shift_command.lua').read_text(encoding='utf-8')
if 'local CONTROLLER_VERSION = "1.2.2"' not in src or 'local RUN_ID = "V1_2_2"' not in src or 'build=BETTER_SHIFT_COMMAND_V1.2.2' not in src: fail('release identity')
if 'local DEBUG_TELEMETRY = false' not in src: fail('DEBUG_TELEMETRY must default false')
if 'local BSC_HUGE = (type(math.huge)=="number" and math.huge) or 1e300' not in src: fail('math.huge compatibility sentinel missing')
for i,line in enumerate(src.splitlines(),1):
    if 'math.huge' in line and 'local BSC_HUGE =' not in line: fail(f'unguarded math.huge dependency line {i}')
reg=(ROOT/'tests/test_regressions_v104.lua').read_text(encoding='utf-8')
if 'missing math.huge host field does not disable controller' not in reg: fail('math.huge compatibility regression missing')
if (ROOT/'source/better_shift_command.lua').read_bytes()!=(ROOT/'src/better_shift_command.lua').read_bytes(): fail('source/src controller mismatch')
for forbidden in ('RMB_DIFF_V2','RAW_RMB_DOWN','RMB_EXIT_TRACE','read_input_snapshot','TH_RMB_DIFF_'):
    if forbidden in src: fail('temporary RMB diagnostic leaked into release: '+forbidden)
for i,line in enumerate(src.splitlines(),1):
    if 'dlog(' in line and 'function dlog(' not in line and 'if DEBUG_TELEMETRY then' not in line:
        fail(f'unguarded dlog line {i}')
for ev in ('FEG_SAMPLE','ATTACK_CONTACT_SAMPLE','MOVE_ROUTE_PROTECT','ACTION_HANDOFF_COMMITTED','ORDER_INPUT','HEARTBEAT','BRIDGE_STATUS','V3_ENTITY_SNAPSHOT_MISS','R1_V3_EVIDENCE_ROOT_BIND_MISS','EXIT_GLOBAL_CONTACTS','V3_EXIT_BODY_STATUS'):
    for i,line in enumerate(src.splitlines(),1):
        if ev in line and ('log(' in line or 'dlog(' in line) and 'if DEBUG_TELEMETRY then' not in line:
            fail(f'unguarded telemetry {ev} line {i}')
for token in ('function R1.read_active_execution(st)','function R1.execution_matches_action(e,a)','NATIVE_FUTURE_OVERRUN','NATIVE_SUCCESSOR_ROLLBACK_TO_CURRENT_MOVE','EXIT_REASSERT_DEFER_IDENTITY'):
    if token not in src: fail('SC6 marker missing: '+token)
cpp=(ROOT/'src/native_bridge/src/lua_module.cpp').read_text(encoding='utf-8')
if '1.0.15-r4-evidence-v3-validated-userdata-root' not in cpp: fail('native ABI marker changed unexpectedly')
for token in ('order_identity_read_v2_retired','entity_snapshot_read_v2_retired','combat_snapshot_read_v2_retired','V2_RETIRED_USE_V3'):
    if token not in cpp: fail('V2 retirement hardening missing: '+token)
for forbidden in ('read_input_snapshot','input_rmb_down','input_rmb_press_seq'):
    if forbidden in cpp: fail('temporary RMB native diagnostic leaked into release: '+forbidden)
print('PASS: v1.2.2 identity + math.huge compatibility + quiet logging + SC6 + source sync + native ABI retained')
