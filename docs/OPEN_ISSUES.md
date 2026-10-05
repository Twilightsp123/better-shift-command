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

### O-09 — Move→Move ownership conflict / destructive rollback

Status: **NATIVE PASSTHROUGH DIAGNOSTIC / WH3 RUNTIME SMOKE REQUIRED**.

The first T2-A adopt-only candidate exposed a deeper ownership conflict. With a permissive Move→Move gate, Native could start a fold-back early and formations compressed into themselves; tightening the gate then caused repeated `NATIVE_SUCCESSOR_ROLLBACK` / nonqueued Move reasserts, which broke the native Shift queue into stepwise movement. The two symptoms come from the same architecture: BSC was treating disagreement between the Lua cursor and CA's already-running Move queue as a reason to mutate that queue.

Current diagnostic architecture makes **player-native Move chains authoritative**. Pure Move→Move transitions do not proactively dispatch a BSC Move and do not rollback/reassert a Native Move. Exact canonical Native Move execution only advances the Lua shadow cursor; all-Move sampling gaps may fast-forward the shadow cursor; crossings over Attack/Exit semantics yield BSC Move tracking rather than issuing a replacement. Once BSC itself issues a command (for example T2-B Attack or Attack→Exit Move), the generation becomes BSC-owned and existing command/ACK/recovery rules continue to apply.

Offline evidence: native Move passthrough suite **7/7 PASS**, active block suite **19/19 PASS**, contracts **24/24 PASS**, v109 **27/27 PASS**, and mutation protection for ownership disable, proactive Move re-enable, shadow-sync disable, and cross-semantic fast-forward. The previous T2-A/hairpin candidates and SC1–SC4 controller-owned Move scheduler tests are archived under `archive/legacy_move_scheduler_tests/`.

The required WH3 diagnostic smoke is intentionally simple: straight Move chains, 90° corners, and 180° fold-back. If passthrough removes both self-compression and stepwise movement, the ownership diagnosis is confirmed. If native passthrough still self-compresses on fold-back, the remaining problem belongs to CA's native queue behavior and must be solved by a new, non-destructive intervention design rather than rollback/reassert.

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
