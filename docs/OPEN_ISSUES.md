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

Status: **OFFLINE FIX CANDIDATE / WH3 RUNTIME SMOKE REQUIRED**.

The strict `ATTACK_REQUIRES_ROUTE_COMPLETE` boundary has been replaced for ordinary Move→Attack by the bounded T2-B `ATTACK_TERMINAL_CORRIDOR`. The implementation requires exact immediate successor semantics, viable target, clear prior route debt, bounded progress, attack-geometry distance caps, extra high-angle progress, and stricter short-leg preservation. Accepted proactive handoff and exact Native adoption both grant explicit `ATTACK_TERMINAL_HANDOFF` completion credit; Exit→Attack remains on its separate strict gate.

Offline closure evidence: dedicated T2-B suite **9/9 PASS**, legacy block suite **33/33 PASS**, and mutation coverage catches both disabled-terminal-corridor and removed-short-leg-guard mutants. The remaining closure requirement is WH3 RT-TP-02/03 runtime smoke on the 9.0.2 candidate.

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
- T2 still needs the shared transition evaluator, immediate successor MOVE adoption, and hysteresis. Move→Attack terminal handoff is implemented as an offline-tested candidate and awaits WH3 runtime smoke.
- Minimum Engagement Time is wired at the legacy-equivalent default 3.0 s; alternate values are not exposed to users in T1H.
