#!/usr/bin/env python3
"""Fail-closed documentation contract for BSC-TPOL-D1 staged handoffs."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def fail(msg): print('FAIL:',msg); raise SystemExit(1)
def read(rel):
    p=ROOT/rel
    if not p.exists(): fail('missing required documentation file: '+rel)
    return p.read_text(encoding='utf-8')
required=[
 'README_FIRST.md','VERSION','PACK_NAME','DESIGN_MANIFEST.json','docs/VERSION_POLICY.md','docs/MAINTAINER_INDEX.md','docs/ARCHITECTURE_STATUS_20260929.md',
 'docs/OPEN_ISSUES.md','docs/ASSUMPTION_LEDGER.md','docs/TEST_MATRIX.md','docs/CURRENT_BUILD_MAP.md',
 'docs/DECISION_LOG.md','docs/VERSION_LINEAGE.md','docs/PROVENANCE.md','docs/HISTORY_COVERAGE.md',
 'docs/DEVELOPMENT_HISTORY.md','docs/MAINTENANCE_PROTOCOL.md','docs/design/BSC_TRANSITION_POLICY_ARCHITECTURE_D1.md',
 'docs/design/HIDDEN_MCT_INTERFACE_T1H.md','docs/design/MCT_POLICY_SCHEMA_D1.md','docs/design/TRANSITION_DECISION_TABLE_D1.md',
 'docs/design/TRANSITION_POLICY_MIGRATION_D1.md','docs/design/TRANSITION_POLICY_TEST_PLAN_D1.md']
for r in required: read(r)
first=read('README_FIRST.md')
for token in ('Mandatory maintainer reading order','v1.3.0','zzz_better_shift_command_steam.pack','BSC-TPOL-D1','BSC-TPOL-T1.5','MCT UI: **not exposed yet**','QUARANTINED'):
    if token.lower() not in first.lower(): fail('README_FIRST missing contract token: '+token)
version_policy=read('docs/VERSION_POLICY.md')
for token in ('v1.3.0','zzz_better_shift_command_steam.pack','not the Mod version'):
    if token not in version_policy: fail('VERSION_POLICY missing token: '+token)
index=read('docs/MAINTAINER_INDEX.md')
for token in ('Document authority','Implemented TPOL scaffold + approved-next design','Historical narrative','Do not count ContactPair as the 17th mandatory hook','D1 promotion rule'):
    if token not in index: fail('MAINTAINER_INDEX missing rule: '+token)
arch=read('docs/ARCHITECTURE_STATUS_20260929.md')
for token in ('Current production/runtime architecture','Strict Move→Attack boundary remains current behavior','SC6 immediate-MOVE asymmetry remains current behavior','T1.5 execution-lineage separation','TPOL-T1H + TPOL-T1 + TPOL-T1.5 implementation status'):
    if token not in arch: fail('ARCHITECTURE_STATUS missing current/design separation: '+token)
policy=read('docs/design/BSC_TRANSITION_POLICY_ARCHITECTURE_D1.md')
for token in ('T1H + T1 SHARED EVALUATOR + T1.5 EXECUTION LINEAGE IMPLEMENTED','T1.5 execution-lineage input','Hard invariants','Hysteresis','MOVE → ATTACK policy','SC6 becomes a coordinator','MCT architecture'):
    if token not in policy: fail('D1 architecture missing token: '+token)
mct=read('docs/design/MCT_POLICY_SCHEMA_D1.md')
for token in ('Smooth   (default / recommended)','Movement Cornering','Attack Handoff','Route Fidelity','Native Successor Tolerance','Minimum Engagement Time','Disengage Priority','Forbidden MCT controls'):
    if token not in mct: fail('MCT schema missing token: '+token)
hidden=read('docs/design/HIDDEN_MCT_INTERFACE_T1H.md')
for token in ('NO USER-VISIBLE MCT UI','from_mct_values','engagement_hold_seconds = 3.0','reserved but intentionally do not alter gameplay yet'):
    if token not in hidden: fail('T1H hidden interface missing token: '+token)
dec=read('docs/DECISION_LOG.md')
for token in ('D-20260929-02','D-20260929-03','D-20260929-04','D-20260929-05','D-20260929-06','D-20261005-01','D-20261005-02','D-20261005-03','Replace abstract Attack Commitment with direct Minimum Engagement Time'):
    if token not in dec: fail('DECISION_LOG missing decision: '+token)
issues=read('docs/OPEN_ISSUES.md')
for token in ('O-08 — Move→Attack','O-09 — SC6 rolls back immediate future MOVE','O-11 — Battle exit/main-menu/desktop hang','T1.5','TPOL-T1H / T2 outstanding'):
    if token not in issues: fail('OPEN_ISSUES missing current blocker: '+token)
matrix=read('docs/TEST_MATRIX.md')
for token in ('Windows Native CTest | 14/14 PASS','T1H hidden PolicyProfile/MCT scaffold | PASS','T1 shared behavior-neutral evaluator refactor | **PASS**','T1.5 execution-lineage separation | **LOCAL STRUCTURAL/EQUIVALENCE PASS**','T2 Move→Attack terminal handoff | HISTORICAL EXPERIMENT PASS; CURRENT T1 NOT ACTIVE','T3 visible MCT adapter/UI wiring | NOT RUN'):
    if token not in matrix: fail('TEST_MATRIX missing gate: '+token)
ledger=read('docs/ASSUMPTION_LEDGER.md')
if '`Entity +0x18 = MovementComponent*` | **RETRACTED**' not in ledger: fail('Assumption ledger lost retracted Entity+0x18 status')
lineage=read('docs/VERSION_LINEAGE.md')
for token in ('BSC-CONV-RC2','NATIVE-MAP-RC7','COREPATH-RC8','SMARTGUARD-RC2','BSC-TPOL-D1','BSC-TPOL-T1H','BSC-TPOL-T1.5'):
    if token not in lineage: fail('VERSION_LINEAGE missing token: '+token)
hist=read('docs/DEVELOPMENT_HISTORY.md')
for token in ('HISTORICAL DOCUMENT — NOT CURRENT AUTHORITY','## 18. 2026-09-29 — Move VTable closure reveals transition-policy limitations','## 19. 2026-09-29 — TPOL-T1H hidden MCT/profile scaffold','## 21. 2026-10-05 — direct T2 experiments','## 22. 2026-10-05 — BSC-TPOL-T1 shared evaluator implemented behavior-neutrally','## 23. 2026-10-05 — BSC-TPOL-T1.5 execution-lineage separation'):
    if token not in hist: fail('DEVELOPMENT_HISTORY missing marker: '+token)
manifest=json.loads(read('DESIGN_MANIFEST.json'))
if manifest.get('design_stream')!='BSC-TPOL-D1' or manifest.get('status')!='T1_5_EXECUTION_LINEAGE_IMPLEMENTED_BEHAVIOR_NEUTRAL_T2_NOT_ACTIVE': fail('DESIGN_MANIFEST identity/status mismatch')
if manifest.get('product_default')!='SMOOTH' or manifest.get('hard_invariants_configurable') is not False: fail('DESIGN_MANIFEST policy contract mismatch')
if 'T1_SHARED_EVALUATOR_IMPLEMENTED' not in manifest.get('implementation_stages',[]): fail('DESIGN_MANIFEST missing implemented T1 stage')
if 'T1_5_EXECUTION_LINEAGE_IMPLEMENTED' not in manifest.get('implementation_stages',[]): fail('DESIGN_MANIFEST missing implemented T1.5 stage')
if 'T2A_IMMEDIATE_MOVE_PENDING' not in manifest.get('implementation_stages',[]) or 'T2C_HYSTERESIS_PENDING' not in manifest.get('implementation_stages',[]): fail('DESIGN_MANIFEST must keep T2 pending after T1')
if manifest.get('mct_ui')!='HIDDEN_NOT_REGISTERED': fail('DESIGN_MANIFEST MCT visibility mismatch')
if manifest.get('formal_project_version')!='1.3.0' or manifest.get('canonical_pack_name')!='zzz_better_shift_command_steam.pack': fail('DESIGN_MANIFEST formal version/pack identity mismatch')
print('PASS: v1.3.0 documentation contract; T1.5 execution lineage is current while T2 behavior remains pending')