#!/usr/bin/env python3
"""Static source contract for WH3 6c104 CorePath RC8. No EXE access required."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
CPP=(ROOT/'src/native_bridge/src/platform_windows.cpp').read_text(encoding='utf-8')
HOST=(ROOT/'src/native_bridge/src/bridge_host.cpp').read_text(encoding='utf-8')
LUA=(ROOT/'src/native_bridge/src/lua_module.cpp').read_text(encoding='utf-8')
HDR=(ROOT/'src/native_bridge/include/wh3/bridge_host.hpp').read_text(encoding='utf-8')
EXPECTED_CORE={
'move':0x030344D4,'attack':0x03032854,'allocator':0x02F5248C,'halt':0x0301B890,
'lua_move':0x02ED5808,'lua_attack':0x02ED50A0,'publish_move':0x01CB1DC8,'publish_attack':0x02DF28BC,
'writer_begin':0x01BCE174,'writer_finalize':0x01BD140C,'copy':0x01BAF488,'stage':0x01BB0C94,
'move_handler':0x02ECF0E0,'attack_handler':0x02ECEBAC,'selection':0x02F042D4,'free':0x0052F770}
EXPECTED_OPTIONAL={'contact_pair':0x030A3859,'smart_guard':0x030E2524}
def fail(m): print('FAIL:',m); raise SystemExit(1)
if 'constexpr const char* exe_hash="6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297"' not in CPP: fail('EXE SHA lock')
block=re.search(r'constexpr\s+Guard\s+guards\[\]\s*=\s*\{(.*?)\};',CPP,re.S);nb=re.search(r'constexpr const char\* hook_names\[\]\s*=\s*\{(.*?)\};',CPP,re.S)
if not block or not nb: fail('core blocks missing')
specs=re.findall(r'\{\s*(0x[0-9a-fA-F]+)\s*,\s*"([0-9a-fA-F]+)"\s*\}',block.group(1));names=re.findall(r'"([^"]+)"',nb.group(1))
if len(specs)!=16 or len(names)!=16: fail('core count !=16')
actual={n:int(r,16) for n,(r,g) in zip(names,specs)}
if actual!=EXPECTED_CORE: fail('core RVA map drift: '+repr(actual))
for n,rv in EXPECTED_OPTIONAL.items():
    symbol=n+'_guard'
    m=re.search(rf'constexpr\s+Guard\s+{symbol}\s*\{{\s*(0x[0-9a-fA-F]+)',CPP)
    if not m or int(m.group(1),16)!=rv: fail(n+' optional RVA drift')
if 'std::array<void*,16> detours' not in CPP or 'std::array<void*,16> g_core_targets' not in CPP: fail('core target/detour count')
if 'contact_pair' in names: fail('ContactPair remains mandatory')
for t in ('g_wh3_physical_evidence_staged_disabled = true','g_wh3_smart_guard_staged_disabled = true','platform_stop_observer'):
    if t not in CPP: fail('missing '+t)
if 'bool BridgeHost::issue_ready()const noexcept{return v3_issue_calibration_ready();}' not in HOST: fail('core issue readiness depends on non-command gate')
if 'DIAGNOSTIC_RUNTIME_GATES_NOT_READY' in HOST: fail('diagnostic gates still veto issue')
if '1.0.17-corepath-wh3-6c104-movevtfix' not in HDR: fail('missing bridge version')
for t in ('COREPATH_EXECUTION_IDENTITY_ONLY','PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8'):
    if t not in LUA: fail('missing '+t)
print('PASS')
print('core_hooks=16')
print('optional_sites=2')
print('physical_evidence=QUARANTINED')
print('smart_guard=STAGED_DISABLED')
