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

Status: **OPEN / T1 STRUCTURE READY / T2-B RUNTIME CONCEPT PROVEN EXPERIMENTALLY**.

Current T1 code deliberately preserves strict Move→Attack until current Move `semantic_done` (`ATTACK_REQUIRES_ROUTE_COMPLETE`). The 2026-10-05 direct T2-B experiment produced repeated smooth `ATTACK_TERMINAL_HANDOFF` events in WH3 9.0.2 and the user reported no pause, but that direct patch is historical evidence rather than current runtime.

Planned closure: reintroduce T2-B through the shared TransitionPolicy evaluator, then pass T2 regression + WH3 RT-TP-02/03 again.

### O-09 — SC6 rolls back immediate future MOVE

Status: **OPEN / T1 + T1.5 STRUCTURE READY / T2-A NOT ACTIVE**.

Current T1.5 SC6 deliberately preserves the legacy immediate future MOVE rollback so the structural work remains behavior-neutral. T1.5 now exposes whether an exact match comes from the original `PLAYER_NATIVE` capture or a later `BSC_ISSUED` ACK identity. Direct T2-A/hairpin experiments on 2026-10-05 were not promotable: permissive adoption produced fold-back self-compression; stricter rollback gates produced stepwise movement. The native-passthrough diagnostic was useful isolation evidence but is not the BSC product architecture.

Planned closure: T2-A must use the shared evaluator and D1 decision vocabulary; T2-C hysteresis must provide a wider bounded adopt window before any final runtime promotion.

### O-10 — Transition policy behavior/MCT only partially implemented

Status: **T1H/T1/T1.5 IMPLEMENTED; T2/T3 PENDING**.

The hidden PolicyProfile scaffold, shared behavior-neutral TransitionPolicy evaluator, and execution-lineage separation are implemented. Smooth/Balanced/Precise movement values remain reserved; visible MCT is still absent. T2 is the first intentional gameplay change.

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
- T1 shared evaluator and T1.5 execution-lineage separation are implemented and behavior-neutral. T2 must still implement immediate successor MOVE policy, Move→Attack terminal handoff, and hysteresis through that evaluator.
- Minimum Engagement Time is wired at the legacy-equivalent default 3.0 s; alternate values are not exposed to users in T1H.
