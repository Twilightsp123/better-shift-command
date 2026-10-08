# Open Issues — 2026-09-29

Formal project version: **v1.3.0**. Internal maintenance labels below identify architecture/history only.

This file contains current unresolved work only. Historical failures belong in `DEVELOPMENT_HISTORY.md`.

## A. Current runtime status

The Move-VTable correction has been built and exercised in WH3. Native outcome fatal behavior is no longer the primary blocker. The next release candidate is blocked by gameplay smoothness and lifecycle closure, not by the old `0x0390E248` top-level Move assumption.

| ID | Status | Evidence / required closure |
|---|---|---|
| O-01 Windows v142 + MASM Build | **PASS** | audited Windows delivery for Native `1.0.17` |
| O-02 Windows Native CTest | **PASS 14/14** | includes backend/module/mid-function smoke |
| O-03 Current EXE guards | **PASS 16/16** | locked SHA `6c104a63...3297` |
| O-04 PE/toolchain verification | **PASS** | AMD64 + v142 delivery |
| O-05 Deterministic candidate pack | **PASS** | Move-VTable-fix candidate built/verified |
| O-06 WH3 Native outcome smoke | **PASS ENOUGH TO CONTINUE GAMEPLAY WORK** | Bridge `1.0.17` runs; old outcome fatal is absent |

## B. Gameplay blockers — Transition Policy D1

### O-08 — Move→Attack can still brake/stop before Attack

Status: **OPEN / T2-B G1.1 OFFLINE VALIDATED / WH3 RUNTIME BLOCKED-DEFERRED**.

The construction branch implements ordinary Move→Attack through the shared TransitionPolicy + T1.6 transaction path with **dual issue/adopt envelopes**. G1.1 requires the observed stopping point to be coherent with the current waypoint; proactive issue never receives the one-poll synchronization margin, while exact Native adoption may use that margin for at most one cached pre-promotion poll. Prior route debt stays blocking, Exit→Attack stays strict, and no historical `attack_lead_*` scalar authorizes permission.

Offline gate: **46/46 maintenance PASS**, core mutations **44/44**, dedicated G1.1/T2-B/cache mutations **13/13**, T2-B runtime fixtures **4/4**.

Current execution state: WH3 runtime testing is **not currently available**, so RT-TP-02/03 is deliberately deferred. The prepared runtime candidate and exact unblock procedure are recorded in `MAINTENANCE_TODO.md`.

Required closure remains unchanged: WH3 RT-TP-02 (straight Move→Attack) and RT-TP-03 (high-angle/route-fidelity Move→Attack). Only after those pass may T2-B be promoted from construction candidate.

### O-09 — SC6 rolls back immediate future MOVE

Status: **OPEN / T2-MOVE-E ISOLATED OFFLINE PASS / NOT RELEASED / WH3 RUNTIME BLOCKED-DEFERRED**.

Current T1.6 SC6 deliberately preserves the legacy immediate future MOVE rollback; T1.6 is permission-neutral and only changes commit protocol. T1.5 now exposes whether an exact match comes from the original `PLAYER_NATIVE` capture or a later `BSC_ISSUED` ACK identity. Direct T2-A/hairpin experiments on 2026-10-05 were not promotable: permissive adoption produced fold-back self-compression; stricter rollback gates produced stepwise movement. The native-passthrough diagnostic was useful isolation evidence but is not the BSC product architecture.

Current isolation: `maintenance/t2move-e-integration` uses A/B/C/D exact-current evidence with T1.6 committed-edge transaction; offline CI `37733220962` passes 11/11 controller cases, 8/8 active mutations and existing 46/46 maintenance. It is an **experimental branch, not a production or WH3-validated implementation**. Planned closure: after T2-B completes WH3 RT-TP-02/03, run T2-MOVE RT-TP-04/05, including hairpin/short-leg/SC3 debt cases, then make an explicit promotion decision. No standalone permissive T2-A state is allowed. Follow-on `maintenance/t2move-f-audit-hardening` closes two E evidence-authorization defects (V3-only provider and native live revision) under offline CI `37820591847`: F controller 5/5, F mutation 3/3, E controller 11/11, E mutation 8/8 and maintenance 46/46. F does not change route geometry or establish WH3 smoothness; O-09 remains OPEN and its runtime promotion gate is still BLOCKED/DEFERRED. G follow-on CI `37822771962` is offline green (G controller 7/7, G mutants 3/3) after reproducing exact Native 180°/135° turnback waypoint-credit loss and restricting **only** the E/F Native adoption path with frozen geometry. The original proactive SC1 early U-turn remains explicitly unresolved because original tests/contract require it. No WH3 behavior closure is claimed. H1 shadow (`maintenance/t2move-h1-route-obligation-shadow`, CI `37825312679`) is offline PASS without gameplay edits: pure 14/14, real controller 5/5, mutations 5/5 CAUGHT, full 46-job maintenance PASS. It documents the unresolved distinction between proactive STEERING_CORNER execution permission and verified waypoint completion/route debt. H2-A now confirms proactive ACK route-credit loss in two synthetic real-controller cases (180° and 90°; `remaining=40.000000`, `STEERING_CORNER_HANDOFF`) in CI `37827397901`. It is an **expected-red test-only gate**; no fix or WH3 result is claimed. O-09 and WH3 runtime gates stay OPEN/BLOCKED. Subsequent isolated H2-B/C/D + H3 candidate has offline test success (CI `37830565468`): 7/7 H2 controller, 9/9 H3 stress, 4/4 Native parity, 5/5 H2 mutants, full maintenance PASS. It explicitly supersedes the old early-turn/credit contract **only** on its development branch. WH3 route smoothness, genuine SC3 debt payout and Move→Attack interplay remain unverified; no release promotion.

### O-10 — Transition policy behavior/MCT only partially implemented

Status: **T1H/T1/T1.5/T1.6/T1.7 + G1 VALIDATED; T2-B G1.1 OFFLINE VALIDATED; T2-MOVE/T3 PENDING**.

The hidden PolicyProfile scaffold, shared evaluator, execution-lineage separation, committed-edge transaction, consumer-neutral envelopes and behavior-neutral G1 observer are validated. The T2-B G1.1 construction candidate intentionally wires ordinary Move→Attack timing but **does not yet count as WH3 runtime promotion**. Smooth/Balanced/Precise movement profile values remain reserved; visible MCT is still absent. T2-MOVE is the next gameplay architecture stage after T2-B runtime closure.

## C. Lifecycle / teardown stream — separate from gameplay

### O-11 — Battle exit/main-menu/desktop hang

Status: **OPEN / SEPARATE STREAM**.

Observed teardown logs include successful BSC Quit-to-Windows safe-stop and, in at least one run, repeated `jg77_battle_ui.lua` listener-removal errors at Battle Complete. Current BSC also keeps hooks resident across ordinary Battle Complete to support later battles. Root cause is not yet isolated enough to merge a lifecycle fix with Transition Policy work.

Rule: lifecycle changes must be a separate patch/test stage.

### O-12 — Quit confirmation cancellation trade-off

Status: **KNOWN CURRENT TRADE-OFF**.

Current `stop_observer()` is one-way for the process. Clicking Quit-to-Windows and then cancelling can leave BSC stopped until WH3 restart. A future suspend/resume lifecycle design may replace this, but not inside Transition Policy D1.

## D. Quarantined research — not release blockers

- historical Entity semantic identity;
- Entity→MovementComponent relationship;
- movement-state field semantics;
- Alive virtual-call class binding;
- ContactPair ownership chain;
- Smart Guard runtime path.

These remain quarantined/staged-disabled and are not prerequisites for D1.

## E. Static-audit caveat retained

The 2026-09-29 disassembly reports proved allocator return ABI, top-level constructors, VTables, sequence write and payload locations, but their queue-full branch prose remains internally inconsistent. `ACCEPTED_NO_SLOT` therefore remains a valid fail-safe contract until separately disproved. Transition Policy D1 does not depend on resolving that caveat.

## TPOL-T1H / T2 outstanding

- T1H hidden profile scaffold is implemented; visible MCT UI is intentionally deferred.
- Movement Cornering / Attack Handoff / Route Fidelity / Native Successor Tolerance / Disengage Priority are reserved but not runtime-wired yet.
- T1 shared evaluator, T1.5 execution-lineage separation, T1.6 committed-edge transaction, T1.7 consumer-neutral envelopes and G1 are validated. T2-B G1.1 is implemented and offline validated but still awaits WH3 RT-TP-02/03; T2-MOVE exact immediate successor MOVE+hysteresis is implemented **only in the isolated E/F/G offline branches**, not in T2-B, release or any WH3-promoted build.
- Minimum Engagement Time is wired at the legacy-equivalent default 3.0 s; alternate values are not exposed to users in T1H.
