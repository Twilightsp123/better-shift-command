#!/usr/bin/env python3
"""Static CorePath source contract. Native addresses come only from canonical JSON."""
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'maintenance_tools'))
from generate_native_header import render\nfrom native_map_config import current_map_path

CPP=(ROOT/'src/native_bridge/src/platform_windows.cpp').read_text(encoding='utf-8')
HOST=(ROOT/'src/native_bridge/src/bridge_host.cpp').read_text(encoding='utf-8')
LUA=(ROOT/'src/native_bridge/src/lua_module.cpp').read_text(encoding='utf-8')
HDR=(ROOT/'src/native_bridge/include/wh3/bridge_host.hpp').read_text(encoding='utf-8')
GEN_PATH=ROOT/'src/native_bridge/include/wh3/generated_native_map.hpp'
GEN=GEN_PATH.read_text(encoding='utf-8')
MAP_PATH=current_map_path(ROOT)
MAP=json.loads(MAP_PATH.read_text(encoding='utf-8'))

def fail(m): print('FAIL:',m); raise SystemExit(1)

if MAP.get('schema')!=1: fail('native map schema')
if len(MAP.get('core',{}))!=16: fail('core count !=16')
if set(MAP.get('optional',{}))!={'contact_pair','smart_guard'}: fail('optional site set')
if GEN!=render(MAP): fail('generated native map stale')

for t in (
 '#include "wh3/generated_native_map.hpp"',
 'native_map::kExeSha256',
 'native_map::kCoreGuards',
 'native_map::kHookNames',
 'native_map::kContactPairGuard',
 'native_map::kSmartGuardGuard',
 'native_map::kMapId',
):
    if t not in CPP: fail('missing generated backend binding '+t)

if 'std::array<void*,16> detours' not in CPP or 'std::array<void*,16> g_core_targets' not in CPP:
    fail('core target/detour count')
for t in ('g_wh3_physical_evidence_staged_disabled = true','g_wh3_smart_guard_staged_disabled = true','platform_stop_observer'):
    if t not in CPP: fail('missing '+t)

for t in ('native_map::kFullMoveVTable','native_map::kAttackVTable'):
    if t not in HOST: fail('missing outcome map binding '+t)
if '0x03910AA8:0x03910228' in HOST: fail('hardcoded outcome VTables remain')

if 'bool BridgeHost::issue_ready()const noexcept{return v3_issue_calibration_ready();}' not in HOST:
    fail('core issue readiness depends on non-command gate')
if 'DIAGNOSTIC_RUNTIME_GATES_NOT_READY' in HOST:
    fail('diagnostic gates still veto issue')
if '1.0.17-corepath-wh3-6c104-movevtfix' not in HDR:
    fail('missing bridge version')
for t in ('COREPATH_EXECUTION_IDENTITY_ONLY','PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8'):
    if t not in LUA: fail('missing '+t)

print('PASS')
print('map='+MAP['map_id'])
print('core_hooks=16')
print('optional_sites=2')
print('native_map_source=JSON_GENERATED')
print('physical_evidence=QUARANTINED')
print('smart_guard=STAGED_DISABLED')
