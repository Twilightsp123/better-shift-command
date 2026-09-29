#!/usr/bin/env python3
"""CorePath RC8 evidence wiring audit.
Execution identity is behavior-authoritative. Entity/Component/Alive/ContactPair
remains archived research and cannot become a production prerequisite.
"""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/better_shift_command.lua').read_text(encoding='utf-8')
def fail(msg): print('FAIL:',msg); raise SystemExit(1)
def section(a,b):
    i=s.find(a);j=s.find(b,i+1)
    if i<0 or j<0: fail('missing section '+a)
    return s[i:j]
if 'local PHYSICAL_EVIDENCE_MODE = "QUARANTINED"' not in s: fail('physical evidence not quarantined')
adapter=section('function R1.read_active_execution(st)','function R1.execution_matches_action')
for t in ('S.evidence_v3_caps','read_active_order_identity_v3'):
    if t not in adapter: fail('execution identity missing '+t)
reconcile=section('function Core.reconcile_native_successor(st,now)','local function advance(st,now)')
for t in ('R1.read_active_execution(st)','R1.execution_matches_action','NATIVE_FUTURE_OVERRUN','NATIVE_SUCCESSOR_ROLLBACK_TO_CURRENT_MOVE'):
    if t not in reconcile: fail('SC6 reconciliation missing '+t)
sc5=section('function Core.maybe_reassert_exit(st,now)','local function rollback_native_future_to_current')
for t in ('R1.read_active_execution(st)','R1.execution_matches_action(active,a)','COREPATH_POSITIVE_CONTACT_FALLBACK','PHYSICAL_EVIDENCE_QUARANTINED'):
    if t not in sc5: fail('SC5 corepath contract missing '+t)
# Quarantined physical helpers must visibly short-circuit.
for fn,needle in (('function R1.v3_refresh_physical(st,now)','if not physical_evidence_enabled() then'),
                  ('function R1.v3_drain_contacts(now)','if not physical_evidence_enabled() then')):
    chunk=section(fn,'\nend')
    if needle not in chunk: fail(fn+' lacks quarantine short-circuit')
# Boot must not hard-require physical APIs.
boot=s[s.find('function Core.boot()'):]
rs=boot.find('for _,name in ipairs({');re_=boot.find('}) do',rs);req=boot[rs:re_]
for t in ('bind_evidence_unit_v3','read_entity_snapshot_v3','read_combat_groups_v3','read_contact_events_v3','contact_owner_ready_v3'):
    if t in req: fail('boot requires quarantined physical API '+t)
# Native production exports fail closed for physical evidence.
cpp=(ROOT/'src/native_bridge/src/lua_module.cpp').read_text(encoding='utf-8')
for t in ('PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8','COREPATH_EXECUTION_IDENTITY_ONLY'):
    if t not in cpp: fail('native quarantine marker missing '+t)
# ContactPair remains code/archive but not mandatory core detour.
plat=(ROOT/'src/native_bridge/src/platform_windows.cpp').read_text(encoding='utf-8')
block=re.search(r'constexpr const char\* hook_names\[\]\s*=\s*\{(.*?)\};',plat,re.S)
if not block or 'contact_pair' in block.group(1): fail('ContactPair still in mandatory hook_names')
if 'contact_pair_guard' not in plat or 'g_wh3_physical_evidence_staged_disabled = true' not in plat: fail('optional ContactPair quarantine missing')
print('PASS: command/execution identity is behavior-authoritative; physical Entity/Component/Alive/ContactPair is quarantined and non-gating')
