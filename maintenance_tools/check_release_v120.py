#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import hashlib,re,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fail(s): print('FAIL:',s); raise SystemExit(1)
src=(ROOT/'source/better_shift_command.lua').read_text(encoding='utf-8')
if 'local CONTROLLER_VERSION = "1.2.0"' not in src or 'local RUN_ID = "V1_2_0"' not in src or 'build=BETTER_SHIFT_COMMAND_V1.2.0' not in src: fail('release identity')
if 'local DEBUG_TELEMETRY = false' not in src: fail('DEBUG_TELEMETRY must default false')
if (ROOT/'source/better_shift_command.lua').read_bytes()!=(ROOT/'src/better_shift_command.lua').read_bytes(): fail('source/src controller mismatch')
# Every runtime dlog call (except its function definition) must sit behind an explicit DEBUG gate so disabled builds avoid formatting the string.
for i,line in enumerate(src.splitlines(),1):
    if 'dlog(' in line and 'function dlog(' not in line and 'if DEBUG_TELEMETRY then' not in line:
        fail(f'unguarded dlog line {i}')
# High-frequency release events must not be emitted unconditionally.
for ev in ('FEG_SAMPLE','ATTACK_CONTACT_SAMPLE','MOVE_ROUTE_PROTECT','ACTION_HANDOFF_COMMITTED','ORDER_INPUT','HEARTBEAT','BRIDGE_STATUS','V3_ENTITY_SNAPSHOT_MISS','R1_V3_EVIDENCE_ROOT_BIND_MISS','EXIT_GLOBAL_CONTACTS','V3_EXIT_BODY_STATUS'):
    for i,line in enumerate(src.splitlines(),1):
        if ev in line and ('log(' in line or 'dlog(' in line) and 'if DEBUG_TELEMETRY then' not in line:
            fail(f'unguarded telemetry {ev} line {i}')
if b'1.0.15-r4-evidence-v3-validated-userdata-root' not in (ROOT/'src/native_bridge/src/lua_module.cpp').read_bytes(): fail('native ABI marker changed unexpectedly')
print('PASS: v1.2.0 identity + quiet production logging + source sync + native ABI retained')
