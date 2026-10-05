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

Status: **WH3 9.0.2 RUNTIME VERIFIED**.

The strict `ATTACK_REQUIRES_ROUTE_COMPLETE` boundary has been replaced for ordinary Move→Attack by the bounded T2-B `ATTACK_TERMINAL_CORRIDOR`. The implementation requires exact immediate successor semantics, viable target, clear prior route debt, bounded progress, attack-geometry distance caps, extra high-angle progress, and stricter short-leg preservation. Accepted proactive handoff and exact Native adoption both grant explicit `ATTACK_TERMINAL_HANDOFF` completion credit; Exit→Attack remains on its separate strict gate.

Closure evidence: dedicated T2-B suite **9/9 PASS**, mutation protection, Windows CI PASS, and the 2026-10-05 WH3 9.0.2 runtime smoke records repeated smooth `ATTACK_TERMINAL_HANDOFF ... mode=ISSUE_ACK` transitions with the old Attack rollback pattern absent.

### O-09 — SC6 rolls back immediate future MOVE

Status: **OFFLINE FIX CANDIDATE / WH3 RUNTIME SMOKE REQUIRED**.

T2-A now permits only an **exact immediate i+1 Native MOVE** to soft-adopt, and only when the current Move is already inside the controller's existing bounded dispatch/steering window. The first implementation is adopt-only: it does not add new proactive Move issue permission. It keeps i+2 overrun rollback, exact execution identity, prior-route-debt blocking, short-leg protection, and Exit-route separation.

Offline evidence: dedicated T2-A suite **11/11 PASS** plus mutation protection for disabled adopt, i+2 skipping, prior-debt bypass, and premature straight-line adoption. WH3 RT-TP-04/05 remains required. The first WH3 fold-back smoke exposed a separate hairpin defect: severe turns could inherit the wide normal `STEERING_CORNER` window and reverse at only 25–40% progress, producing formation self-compression. The current candidate splits >=135° turns into a strict near-waypoint hairpin gate; dedicated hairpin coverage is **5/5 PASS**. A new WH3 fold-back smoke is required.

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
- T2 still needs the shared behavior-neutral evaluator and hysteresis. Move→Attack is runtime verified; immediate successor MOVE adoption is implemented as an offline-tested adopt-only candidate awaiting WH3 runtime smoke.
- Minimum Engagement Time is wired at the legacy-equivalent default 3.0 s; alternate values are not exposed to users in T1H.
