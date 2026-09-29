# Test Matrix — Runtime Baseline + Transition Policy D1

## 1. Corrected CorePath runtime baseline

| Gate | Result | Meaning |
|---|---:|---|
| Controller source jobs | 19/19 PASS | existing offline Lua/Python baseline |
| Mutation suite | 40/40 CAUGHT | existing invariants |
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
| T1 behavior-neutral evaluator refactor | NOT RUN | old/new decision equivalence + existing suite |
| T2 immediate-MOVE reconciliation | NOT RUN | offline + mutation + WH3 RT-TP-04/05 |
| T2 Move→Attack terminal handoff | NOT RUN | offline + WH3 RT-TP-02/03 |
| T2 hysteresis | NOT RUN | adopt-only boundary tests; no rollback thrash |
| T3 MCT profile compiler | NOT RUN | deterministic presets + missing-MCT fallback |
| T3 MCT runtime comparison | NOT RUN | Smooth/Balanced/Precise differ only in timing/precision |
| T4 Attack/Exit tuning | DEFERRED | only after T2/T3 stable |

Full test plan: `docs/design/TRANSITION_POLICY_TEST_PLAN_D1.md`.

## 4. Separate lifecycle gate

Battle teardown/suspend-resume is a separate stream and must not be marked PASS by Transition Policy tests.
