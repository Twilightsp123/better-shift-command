#!/usr/bin/env python3
from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'source/better_shift_command.lua'
s=SRC.read_text(encoding='utf-8')

def fail(msg):
    print('FAIL:',msg);raise SystemExit(1)

def section(start,end):
    a=s.find(start)
    if a<0:fail('missing '+start)
    b=s.find(end,a)
    if b<0:fail('missing end '+end)
    return s[a:b]

# Behavior-critical execution identity must be V3-authoritative.
adapter=section('function R1.read_active_execution(st)','function R1.execution_matches_action')
for token in ('S.evidence_v3_caps','read_active_order_identity_v3','S.evidence_caps','read_active_order_identity_v2'):
    if token not in adapter:fail('identity adapter missing '+token)
if adapter.index('read_active_order_identity_v3')>adapter.index('read_active_order_identity_v2'):
    fail('V3 must precede V2 fallback')
reconcile=section('function Core.reconcile_native_successor(st,now)','local function advance(st,now)')
for token in ('R1.read_active_execution(st)','R1.execution_matches_action','NATIVE_FUTURE_OVERRUN','NATIVE_SUCCESSOR_ROLLBACK_TO_CURRENT_MOVE'):
    if token not in reconcile:fail('reconciliation missing '+token)
for forbidden in ('read_active_order_identity_v2','R1.evidence(st'):
    if forbidden in reconcile:fail('reconciliation directly uses legacy identity '+forbidden)
sc5=section('function Core.maybe_reassert_exit(st,now)','local function rollback_native_future_to_current')
for token in ('EXIT_REASSERT_DEFER_IDENTITY','R1.read_active_execution(st)','R1.execution_matches_action(active,a)'):
    if token not in sc5:fail('SC5 identity layer missing '+token)
# current_target may remain diagnostic but may not authorize transition/adoption.
if 'current_target()' in reconcile and 'NATIVE_SUCCESSOR_ADOPTED' not in reconcile:
    fail('unexpected reconciliation structure')
# Direct V2 execution-identity reads are allowed only inside the explicit adapter fallback.
occ=[m.start() for m in re.finditer(r'read_active_order_identity_v2',s)]
a0=s.find('function R1.read_active_execution(st)');a1=s.find('function R1.execution_matches_action')
if len(occ)!=2 or any(not (a0 <= x < a1) for x in occ):
    fail('legacy active-order read escaped compatibility adapter')
# Old V2 entity/combat readers are telemetry-only legacy code. They must not appear in
# route handoff, successor reconciliation, SC5 recovery, attack gating, or dispatch.
critical='\n'.join([
    section('function Core.observe_exit_block(st,now)','function Core.vector_at(st,p)'),
    reconcile,
    sc5,
])
for forbidden in ('read_entity_snapshot_v2','read_combat_groups_v2','R1.entity(st,now)','R1.combat(st,now)'):
    if forbidden in critical:fail('legacy V2 physical evidence leaked into behavior-critical path: '+forbidden)
# Native keeps V2 ABI names but they must fail explicitly retired after argument validation.
cpp=(ROOT/'src/native_bridge/src/lua_module.cpp').read_text(encoding='utf-8')
for token in ('order_identity_read_v2_retired','entity_snapshot_read_v2_retired','combat_snapshot_read_v2_retired','V2_RETIRED_USE_V3'):
    if token not in cpp:fail('native V2 retirement hardening missing '+token)
reg=cpp[cpp.find('REG("r1_evidence_capabilities_v2"'):cpp.find('REG("version"')]
for token in ('order_identity_read_v2_retired','entity_snapshot_read_v2_retired','combat_snapshot_read_v2_retired'):
    if token not in reg:fail('native V2 export still wired to live reader: '+token)
# Tests must include V3-only and V2-fallback coverage.
t=(ROOT/'tests/test_exec_identity_v3.lua').read_text(encoding='utf-8')
for token in ('V3_ONLY_SUCCESSOR_READY','V3_ONLY_SUCCESSOR_EARLY_ROLLBACK','V3_FUTURE_OVERRUN_ROLLBACK','V3_IDENTITY_MISMATCH_NO_FALSE_ADOPT','NONCANONICAL_ACTIVE_ORDER','V2_COMPAT_FALLBACK'):
    if token not in t:fail('missing execution identity regression '+token)
print('PASS: execution identity wiring is V3-authoritative; V2 is compatibility-only/telemetry-only; retired native V2 readers fail closed')
