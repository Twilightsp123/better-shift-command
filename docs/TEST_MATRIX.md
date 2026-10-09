# Test Matrix — Better Shift Command v1.3.0

## 1. Corrected CorePath runtime baseline

| Gate | Result | Meaning |
|---|---:|---|
| Maintenance jobs | **46/46 PASS (GITHUB ACTIONS T2-B G1.1 OFFLINE)** | CorePath/T1/T1.5/T1.6/T1.7 + G1/G1.1 + T2-B policy/cache/transaction gates |
| Mutation suite | **PASS** | core 44/44 + T1.5 7/7 + T1.6 7/7 + T1.7 7/7 + G1.1/T2-B/cache 13/13 CAUGHT |
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
| Move→Attack | G1.1 dual-envelope candidate offline PASS; WH3 runtime not yet rerun | **RT-TP-02/03 pending** |
| SC6 immediate successor ATTACK | exact-current pre-promotion cache + shared adopt envelope offline PASS | WH3 verification pending with T2-B |
| SC6 immediate successor MOVE | T2-B/release retains rollback; isolated E/F/G can adopt with frozen proof and G turnback credit check | **E/F/G offline only, WH3 pending** |
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
| T1.6 committed-edge transaction | **PASS / PERMISSION-NEUTRAL** | submit is not commit; ACK and exact Native adopt share `commit_transition_edge`; reject aborts; deterministic T1 probe/CFG unchanged; 7/7 transaction mutants; runtime 3/3 |
| T1.7 consumer-neutral policy envelopes | **PASS / PERMISSION-NEUTRAL** | one decision exposes issue/adopt envelopes; T1.6 runtime permission must remain equivalent |
| ARRIVAL_BRAKE_G1 observation layer | **PASS / BEHAVIOR-NEUTRAL** | pure radial+ground deceleration observer; G1 CI passed 40-job maintenance suite; no CFG/permission change |
| ARRIVAL_BRAKE_G1.1 coherence layer | **PASS / T2-B POLICY EVIDENCE** | separate issue/adopt stopping-point coherence; no new gameplay CFG scalar |
| T2 immediate-MOVE reconciliation | **E ISOLATED OFFLINE PASS / PRODUCTION INACTIVE** | E controller 11/11, active mutations 8/8, original maintenance 46/46; WH3 RT-TP-04/05 BLOCKED |
| T2-MOVE-F evidence safety (V3 / native revision / SC3 debt) | **F ISOLATED OFFLINE PASS / PRODUCTION INACTIVE** | CI `37819203083`: E baseline F-risk 1/3 PASS, 2/3 FAIL; CI `37820591847`: F controller 5/5 PASS, F mutants 3/3 CAUGHT, E controller 11/11, E mutants 8/8 CAUGHT, 46/46 maintenance; WH3 RT-TP-04/05 BLOCKED |
| T2-MOVE-G Native turnback adoption | **G ISOLATED OFFLINE PASS / PROACTIVE SC1 STILL OPEN** | F baseline adversarial 4/7 PASS, 3/7 FAIL in CI `37822137891`; G corrected CI `37822771962`: 7/7 controller PASS, 3/3 G mutants CAUGHT; original E/F/46 maintenance PASS. Scope Native adoption only; WH3 RT-TP-04/05 NOT TESTED |
| T2-MOVE-H1 read-only route-obligation policy | **H1 ISOLATED OFFLINE PASS / NO PERMISSION CHANGE** | Expanded CI `37825955358`: 15/15 pure (including untrusted `STEERING_CORNER_HANDOFF` reason), 5/5 real-controller shadow, 6/6 H1 mutations CAUGHT, frozen SC1/T1.6/CFG/mirrors contract, original full 46-job maintenance PASS. Legacy 90°/180° premature completion conflicts documented, not fixed. WH3 NOT TESTED |
| T2-MOVE-H2-A proactive ACK false-credit reproduction | **EXPECTED-RED CONFIRMED — NOT FIXED** | CI `37827397901`: H2-A 4 PASS / 2 FAIL by design. A01 180° and A02 90° ACK at 40m short incorrectly mark `STEERING_CORNER_HANDOFF`; A03-A06 controls pass. Full H1/G/F/E and 46 maintenance baselines still PASS. Fix deferred to distinct H2-B stage, WH3 NOT TESTED |
| T2-MOVE-H2-B/C/D + H3 route integrity candidate | **ISOLATED OFFLINE PASS / WH3 NOT TESTED** | CI `37830565468`: H2 7/7, H3 ten-node/multi-unit route stress 9/9, Native parity 4/4, route-credit mutants 5/5 CAUGHT, original 46 maintenance PASS. Old early SC1 90°/U-turn expectation explicitly superseded only here. Real RT-TP-02/03/04/05 blocked. |
| T2 Move→Attack terminal handoff | **OFFLINE PASS / WH3 PENDING** | dual envelopes + one-poll pre-promotion cache + T1.6 commit; 46/46 maintenance, 13/13 dedicated mutants, 4/4 runtime fixtures; WH3 RT-TP-02/03 required |
| T2-MOVE hysteresis | **E ISOLATED OFFLINE PASS / WH3 BLOCKED** | temporal adopt-only band requires prior route proof and one exact pre-promotion poll; not merged/published |
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


## WH3 9.0.2 Native bootstrap and H2/H3 integration (isolated candidate)

| Gate | Status | Evidence |
|---|---|---|
| 9.0.2 address map / 16 mandatory hook guards / Full Move and Attack VTable | **PASS STATIC** | Existing `maintenance/wh3-9.0.2-map-candidate`, cross-checked against integrated `native_maps/candidates/wh3_9.0.2_fec656f4.json` |
| H2/H3 Controller 7/7, H3 stress 9/9, Native parity 4/4, H2 mutations 5/5, full maintenance | **PASS OFFLINE** | GitHub Actions `37877024598` Linux |
| Windows x64 v142 + MASM compilation | **PASS** | Same Actions run: build-local 9.0.2 generated map, MASM-safe CXX-only flags |
| Windows Native CTest | **14/14 PASS** | Same Actions run |
| New 9.0.2 DLL version/hash/pack byte integration | **PASS BUILD** | Windows-built 1.0.18 DLL; plain+DEBUG PFH5 packed and SHA256 sealed |
| WH3 in-game Observer initialization and standard MOVE/ATTACK smoke | **NOT TESTED** | Await script logs on supported 9.0.2 Windows game process |
| WH3 Move/Attack choreography, foldback/no-stutter, multi-unit, teardown | **NOT TESTED** | RT-TP-02/03/04/05 remain blocked |

