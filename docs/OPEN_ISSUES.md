# Open Issues — 2026-09-29

Formal project version: **v1.3.0**. Internal maintenance labels below identify architecture/history only.

This file contains current unresolved work only. Historical failures belong in `DEVELOPMENT_HISTORY.md`.

## A. Current Native maintenance status

WH3 9.0.1 remains the last runtime-validated Native baseline. WH3 9.0.2 is now the active build candidate on this branch. Address relocation itself is no longer the open question: all 16 mandatory sites and both optional sites have been statically relocated and the Move/Attack constructor/VTable chain has been re-derived. The remaining 9.0.2 work is build/runtime validation.

| ID | Status | Evidence / required closure |
|---|---|---|
| O-01 WH3 9.0.2 Windows v142 + MASM Build | **OPEN / NOT RUN** | build Bridge `1.0.18-corepath-wh3-fec656f4-map902` |
| O-02 WH3 9.0.2 Windows Native CTest | **OPEN / NOT RUN** | run full Windows Native CTest after build |
| O-03 WH3 9.0.2 Current EXE guards | **STATIC PASS 16/16** | locked SHA `fec656f4...3785`; built-candidate inspect still required |
| O-04 WH3 9.0.2 order identity dataflow | **STATIC PASS** | allocator → Move/Attack constructors → VTables re-derived |
| O-05 WH3 9.0.2 deterministic candidate pack | **OPEN** | only after Windows build/tests |
| O-06 WH3 9.0.2 Native runtime smoke | **OPEN / NOT RUN** | Move, Attack, queued commands, ownership, execution identity, safe-stop |
| O-07 Last runtime baseline | **WH3 9.0.1 PASS** | Bridge 1.0.17 / SHA 6c104a63 remains proven fallback |

The automated address-maintenance pipeline is documented in `docs/NATIVE_ADDRESS_MAINTENANCE_PIPELINE.md`.

## B. Gameplay blockers — Transition Policy D1

### O-08 — Move→Attack can still brake/stop before Attack

Status: **OPEN / DESIGN APPROVED**.

Current code deliberately blocks Move→Attack until current Move `semantic_done` (`ATTACK_REQUIRES_ROUTE_COMPLETE`). Runtime evidence on 2026-09-29 showed Native already entering immediate Attack and SC6 rolling it back because route permission was still strict.

Planned closure: `BSC-TPOL-D1` T2-B terminal Attack handoff.

### O-09 — SC6 rolls back immediate future MOVE

Status: **OPEN / DESIGN APPROVED**.

Current SC6 treats any future type other than ATTACK as overrun. Runtime `script_log_290926_1833.txt` records exact immediate/future MOVE execution followed by `NATIVE_FUTURE_OVERRUN` rollback.

Planned closure: `BSC-TPOL-D1` T2-A shared transition evaluator + immediate-MOVE adopt/soft-adopt.

### O-10 — Transition policy/MCT not implemented

Status: **DESIGN ONLY**.

Smooth/Balanced/Precise/Custom policy architecture is defined under `docs/design/`; no runtime source in this package implements it yet.

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
- T2 must still implement the shared transition evaluator, immediate successor MOVE adoption, Move→Attack terminal handoff, and hysteresis.
- Minimum Engagement Time is wired at the legacy-equivalent default 3.0 s; alternate values are not exposed to users in T1H.
