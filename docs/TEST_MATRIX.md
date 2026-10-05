# Test Matrix — Better Shift Command v1.3.0

## 1. Corrected CorePath runtime baseline

| Gate | Result | Meaning |
|---|---:|---|
| Maintenance jobs | **30/30 PASS** | GitHub Actions v4 consolidated runner: recovered CorePath/T1 gates plus 3 T1.5 gates |
| Mutation suite | **PASS** | Core mutation harness PASS (43/43) + T1.5 lineage 7/7 CAUGHT; consolidated runner PASS |
| Portable Native CTest | 13/13 PASS | portable native fixtures |
| ASan/UBSan CTest | 13/13 PASS | sanitizer baseline |
| Windows VS2019 v142 + MASM | PASS | audited Move-VTable-fix delivery |
| Windows Native CTest | 14/14 PASS | includes backend/module/mid-function smoke |
| Current EXE inspect | PASS 16/16 | target build guards |
| Move/Attack outcome dataflow audit | PASS with queue-full prose caveat | exact allocator/constructors/VTables proven |
| WH3 Move-VTable fix smoke | PASS ENOUGH TO CONTINUE | Bridge 1.0.17 runs without old outcome fatal |

## 2. Runtime behavior findings that motivate D1

| Behavior | Current result | Status |
|---|---|---|
| Move→Move normal steering | operational, but SC6 exact future-MOVE rollback still observed | redesign needed |
| Move→Attack | strict boundary can brake/stop | redesign needed |
| SC6 immediate successor ATTACK | current adopt/rollback path exists | migrate to shared evaluator |
| SC6 immediate successor MOVE | current code rolls back | **known limitation** |
| future index > i+1 | rollback | must remain |
| canonical target identity | enforced | must remain |

## 3. D1 design/implementation gates

| Gate | D1 status | Promotion requirement |
|---|---:|---|
| D1 architecture document | PASS / approved design | this package |
| D1 decision table | PASS / approved design | this package |
| T1H hidden PolicyProfile/MCT scaffold | PASS | static contract + existing suite; no visible MCT UI |
| T1 shared behavior-neutral evaluator refactor | **PASS** | old/new deterministic decision probe equivalent; existing suite unchanged |
| T1.5 execution-lineage separation | **PASS / BEHAVIOR-NEUTRAL** | capture/issued identity split; 15,625 identity states equivalent; 7/7 lineage mutants caught; consolidated 30/30 PASS |
| T2 immediate-MOVE reconciliation | NOT ACTIVE | implement only after T1; offline + mutation + WH3 RT-TP-04/05 |
| T2 Move→Attack terminal handoff | HISTORICAL EXPERIMENT PASS; CURRENT T1.5 NOT ACTIVE | reimplement through evaluator + rerun offline/WH3 RT-TP-02/03 |
| T2 hysteresis | NOT ACTIVE | issue/adopt bands required before T2 promotion |
| T3 visible MCT adapter/UI wiring | NOT RUN | uses existing T1H profile compiler; missing-MCT fallback |
| T3 MCT runtime comparison | NOT RUN | Smooth/Balanced/Precise differ only in timing/precision |
| T4 Attack/Exit tuning | DEFERRED | only after T2/T3 stable |

Full test plan: `docs/design/TRANSITION_POLICY_TEST_PLAN_D1.md`.

## 4. Separate lifecycle gate

Battle teardown/suspend-resume is a separate stream and must not be marked PASS by Transition Policy tests.

## TPOL-T1H hidden profile scaffold

| Check | Result |
|---|---|
| no `get_mct()` / MCT registration in controller | PASS (static contract) |
| hidden PolicyProfile schema present | PASS |
| legacy attack hold preserved through profile | PASS: 3.0 s → 3000 ms |
| movement policy fields affect runtime | NO — intentionally reserved |
| existing CorePath controller suite | PASS |
| existing evidence wiring | PASS |
| Native code changed | NO |
| visible MCT UI runtime test | N/A — intentionally absent |
