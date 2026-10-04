#!/usr/bin/env python3
"""Fail-closed source contract for Better Shift Command CorePath RC8 PREBUILD."""
from pathlib import Path
import hashlib,re,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'maintenance_tools'))
from native_map_config import current_map_path
from generate_native_header import render

def fail(msg): print('FAIL:',msg); raise SystemExit(1)
def need(text,token,label=None):
    if token not in text: fail(label or ('missing '+token))

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

controller=(ROOT/'source/better_shift_command.lua').read_text(encoding='utf-8')
controller2=(ROOT/'src/better_shift_command.lua').read_text(encoding='utf-8')
if controller!=controller2: fail('source/src controller mismatch')
for token in (
 'local CONTROLLER_VERSION = "1.3.0"',
 'local RUN_ID = "V1_3_0"',
 'BETTER_SHIFT_COMMAND_V1.3.0',
 'local PHYSICAL_EVIDENCE_MODE = "QUARANTINED"',
 'COREPATH_POSITIVE_CONTACT_FALLBACK',
 'PHYSICAL_EVIDENCE_QUARANTINED',
 'NATIVE_FUTURE_OVERRUN','NATIVE_SUCCESSOR_ROLLBACK','read_active_order_identity_v3'):
    need(controller,token)
# Physical APIs may exist as dormant compatibility helpers, but boot may not hard-require them.
boot=controller[controller.find('function Core.boot()'):]
required_start=boot.find('for _,k in ipairs({')
required_end=boot.find('}) do',required_start)
if required_start<0 or required_end<0: fail('bridge API requirement list not found')
required=boot[required_start:required_end]
for token in ('bind_evidence_unit_v3','read_entity_snapshot_v3','read_combat_groups_v3','read_contact_events_v3','contact_owner_ready_v3'):
    if token in required: fail('physical API leaked into boot hard requirements: '+token)
for token in ('r1_evidence_capabilities_v3','read_active_order_identity_v3','stop_observer'):
    if token not in required: fail('core evidence API missing from boot requirements: '+token)
need(boot,'bridge.version()~="1.0.18-corepath-wh3-fec656f4-map902"')
need(controller,'BSC_COREPATH_SAFE_STOP_QUIT_WINDOWS')
need(controller,'OBSERVER_SAFE_STOP reason=QUIT_WINDOWS_CLICK')
# Quarantined binder must short-circuit before touching userdata/native physical API.
bind=controller[controller.find('local function bind_evidence_unit'):controller.find('local function register',controller.find('local function bind_evidence_unit'))]
need(bind,'if not physical_evidence_enabled() then return false end','evidence binder does not fail closed under quarantine')
# No temporary input diagnosis in candidate.
for forbidden in ('RMB_DIFF_V2','RAW_RMB_DOWN','RMB_EXIT_TRACE','read_input_snapshot','TH_RMB_DIFF_'):
    if forbidden in controller: fail('temporary diagnostic leaked into controller: '+forbidden)

cpp=(ROOT/'src/native_bridge/src/platform_windows.cpp').read_text(encoding='utf-8')
lua=(ROOT/'src/native_bridge/src/lua_module.cpp').read_text(encoding='utf-8')
host=(ROOT/'src/native_bridge/src/bridge_host.cpp').read_text(encoding='utf-8')
map_path=current_map_path(ROOT)
native_map=json.loads(map_path.read_text(encoding='utf-8'))
generated_path=ROOT/'src/native_bridge/include/wh3/generated_native_map.hpp'
generated=generated_path.read_text(encoding='utf-8')
if native_map.get('schema')!=1: fail('native map schema')
if len(native_map.get('core',{}))!=16: fail('expected 16 mandatory core hooks in promoted map')
if set(native_map.get('optional',{}))!={'contact_pair','smart_guard'}: fail('optional site set drift')
if generated!=render(native_map): fail('generated native map stale')
for token in (
              '#include "wh3/generated_native_map.hpp"',
              'native_map::kExeSha256','native_map::kCoreGuards','native_map::kHookNames',
              'native_map::kContactPairGuard','native_map::kSmartGuardGuard','native_map::kMapId',
              'std::array<void*,16> g_core_targets','std::array<void*,16> detours',
              'g_wh3_physical_evidence_staged_disabled = true','platform_stop_observer'):
    need(cpp,token)
for forbidden in ('constexpr Guard guards[]={','constexpr const char* hook_names[]={','constexpr const char* exe_hash="'):
    if forbidden in cpp: fail('duplicate native-map constant remains in backend: '+forbidden)
for token in ('native_map::kFullMoveVTable','native_map::kAttackVTable'):
    need(host,token)
if native_map['derived']['simple_intercept_move_vtable'].get('release_use') is not False:
    fail('Simple/Intercept Move VTable may not become top-level release identity')
# Core issue authorization must not wait on Component/Alive diagnostics.
need(host,'bool BridgeHost::issue_ready()const noexcept{return v3_issue_calibration_ready();}')
if 'DIAGNOSTIC_RUNTIME_GATES_NOT_READY' in host: fail('physical diagnostic gate still vetoes core issue path')
hdr=(ROOT/'src/native_bridge/include/wh3/bridge_host.hpp').read_text(encoding='utf-8')
need(hdr,'1.0.18-corepath-wh3-fec656f4-map902')
for token in ('PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8','physical_evidence_quarantined','COREPATH_EXECUTION_IDENTITY_ONLY'):
    need(lua,token)
# Production physical capability bits must be false while execution identity follows the build lock.
caps=lua[lua.find('static int evidence_caps'):lua.find('static int evidence_caps_v2_retired')]
need(caps,'bit(L,"execution_identity",build_ok)')
for token in ('bit(L,"entity_snapshot",false)','bit(L,"combat_groups",false)','bit(L,"contact_pairs",false)','bit(L,"target_specific_physical_contact",false)'):
    need(caps,token)

# Frozen upstream v1.2.2 source provenance hashes.
expected={
 'better_shift_command.lua':'7876a5068378d36cd302e39d7c6e1cb8c6b964fa8ac77a7c7ed87c0213570302',
 'fresh_engagement_gate.lua':'31cb6fa4b2264dec7016cb100c206e6ab311ef6be56e49faec68a240ba7feb8b',
 'r1_v3_contacts.lua':'53e175cf26c7007c44e530190f814eb2b6ed4d06ea30a803b519f6342a1cafbe',
 'r1_v3_handoff.lua':'69b9acab964b602ab85e841fc39fde3e13a2c8f6fcb7eebe6cad6e4cc98bd670',
 'r1_v3_recovery.lua':'2b9899fc27e0d6aa3257728981227057d861aa2ae3a510ed14fa7b82efed88b4',
}
for name,h in expected.items():
    p=ROOT/'archive/upstream_v1.2.2'/name
    if not p.exists() or sha(p)!=h: fail('upstream v1.2.2 archive drift: '+name)
print('PASS: CorePath RC8 source contract; 16 command hooks mandatory, physical evidence quarantined, provenance frozen')
