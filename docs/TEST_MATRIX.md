# Test Matrix — Better Shift Command v1.3.0

## 1. Native build baselines

### 1.1 Last runtime-validated baseline — WH3 9.0.1 / Bridge 1.0.17

| Gate | Result | Meaning |
|---|---:|---|
| Controller source jobs | 19/19 PASS | existing offline Lua/Python baseline |
| Mutation suite | 40/40 CAUGHT | existing invariants |
| Portable Native CTest | 13/13 PASS | portable native fixtures |
| ASan/UBSan CTest | 13/13 PASS | sanitizer baseline |
| Windows VS2019 v142 + MASM | PASS | audited 9.0.1 Move-VTable-fix delivery |
| Windows Native CTest | 14/14 PASS | includes backend/module/mid-function smoke |
| WH3 9.0.1 EXE inspect | PASS 16/16 | SHA 6c104a63...3297 |
| Move/Attack outcome dataflow audit | PASS | exact allocator/constructors/VTables |
| WH3 Move-VTable fix smoke | PASS ENOUGH TO CONTINUE | Bridge 1.0.17 ran without old outcome fatal |

### 1.2 Current build candidate — WH3 9.0.2 / Bridge 1.0.18

| Gate | Result | Meaning |
|---|---:|---|
| Address pipeline Stages 1–6 | PASS | exact + normalized + .pdata + relationships |
| Target EXE SHA | PASS | fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785 |
| Mandatory guards | PASS 16/16 BYTE-EXACT | independent readback from supplied 9.0.2 EXE |
| Optional guards | PASS 2/2 BYTE-EXACT | ContactPair/Smart Guard remain non-gating |
| Move/Attack allocator→constructor→VTable | PASS STATIC | re-derived on 9.0.2 EXE |
| JSON → generated C++ map synchronization | PASS | one maintained address source |
| Windows VS2019 v142 + MASM | **NOT RUN** | required next gate |
| Windows Native CTest | **NOT RUN** | required next gate |
| WH3 9.0.2 EXE inspect from built candidate | **NOT RUN** | must pass 16/16 |
| WH3 native smoke | **NOT RUN** | required before release authorization |

The 9.0.1 PASS rows are historical/currently proven evidence and must not be read as 9.0.2 validation.

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
| T1 shared behavior-neutral evaluator refactor | NOT RUN | old/new decision equivalence + existing suite |
| T2 immediate-MOVE reconciliation | NOT RUN | offline + mutation + WH3 RT-TP-04/05 |
| T2 Move→Attack terminal handoff | NOT RUN | offline + WH3 RT-TP-02/03 |
| T2 hysteresis | NOT RUN | adopt-only boundary tests; no rollback thrash |
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
