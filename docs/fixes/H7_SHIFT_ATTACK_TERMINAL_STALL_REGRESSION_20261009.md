# H7 — Shift Move→Attack Near-Terminal Stall Regression (Candidate, NOT Released)

**Date:** 2026-10-09
**Source branch:** `maintenance/t2move-h6-route-guide-nearpass` at `d10d9bd55c1199e705c20fb458a7472371cd2fd1`.
**Isolated candidate branch:** `maintenance/t2b-h7-attack-stall-recovery`.
**WH3 test input:** `script_log_091026_1253.txt` (user-supplied); frontend `script_log_091026_1252.txt` is not battle behavior proof.
**Current status:** SOURCE PATCH AND PURE/STATIC TESTS PREPARED; FULL LUA/WH3 RUNTIME VERIFICATION **NOT RUN**. Not in Steam pack.

## Incident: observed evidence, not speculation

Actual WH3 9.0.2 / BSC v1.3.0 candidate logs:
- Script initialized; H4/H6 `ROUTE_GUIDE_NEAR_PASS_ACCEPTED` confirms the user's experimental controller behavior.
- `uid=1010` at model 41,000: queued Shift `ATTACK` target 1030 **ACCEPTED**, with `shift=true`; this is NOT a keyboard/input-recognition failure.
- `ATTACK_TRANSITION_WAIT reason=ATTACK_ARRIVAL_BRAKE_UNPROVEN` repeats as distance falls from 160.18 to 13.42, then stays around 13.42 at model 65,700–69,300.
- At 69,800, exact player-native `ATTACK` is ahead of controller permission; `NATIVE_SUCCESSOR_ROLLBACK` calls `REASSERT_MOVE` (`BLOCKED_EXECUTION_IDENTITY`), undoing the native attack in favor of an already near-finished Move.
- Only after `NATIVE_IDLE_ROUTE_FINISH` at model 75,700 (remaining 15.82m) does `DISPATCH_ATTACK` fire, a ~34.7-second interval from the initial Shift attack capture. There is also a second successful dispatch later (model 117,300). Thus the failure is **conditional severe delay/rollback**, not total attack disablement.
- Further `ATTACK_TRANSITION_WAIT` cases, including stationary near-terminal waits, occur on later generations. This observed runtime behavior invalidates treating the T2-B G1.1 *monotonically decreasing ground AND approach speeds across four samples* as the exclusive signal for a safe near-terminal handoff.

## Source-grounded mechanism

`R1.ArrivalBrakeG11.observe` currently requires strict decrease of both ground speed and approach speed for three successive intervals, then a stop-distance coherence check. The `R1.T2BAttackPolicy.evaluate` issue/adopt windows remain closed on `ATTACK_ARRIVAL_BRAKE_UNPROVEN` until the MOVE becomes `semantic_done`. This can cause severe stalls when a real game unit slows/stops by discontinuous pathfinding or collision rather than smooth monotonically decelerating samples.

## H7 single-variable change: bounded real terminal-stall proof

Add one alternative **inside ordinary MOVE→immediate ATTACK only**:
- Current MOVE has actually moved, then stopped making material progress for at least the **existing** `CFG.move_idle_finish_confirm_ms` (700ms) while median speed is <= existing `CFG.stall_speed` (1.5); current progress is >= existing `CFG.move_idle_finish_progress` (0.5).
- Remaining distance is <= the **existing native idle-finish bounded envelope**, capped by current leg fraction; no new free-floating meter constants.
- Target still valid/exact, successor still canonical immediate `i+1`, no unpaid route obligation; current action must **not** be `EXIT_ROUTE`. Maintain T1.6 issue→ACK commit and Native identity/revision guards.
- This evidence opens issue/adopt with `ATTACK_TERMINAL_STALL_VERIFIED` and terminal credit; original G11 braking coherence remains the other path. It does **not** credit earlier MOVE geometry alone or change MOVE→MOVE policies, H4/H6/SC3 debt, Native hooks, ContactPair, Attack hold or Steam pack.

**Risk:** A temporarily stalled unit near a waypoint due to obstruction rather than genuine arrival may be allowed to hand off earlier than before. The safeguard is only existing movement/progress/terminal-envelope constraints; WH3 validation must include angled/obstacle-route corner tests. If that regression appears, withdraw H7 and refine evidence, do not blindly raise distance limits.

## Test gates and evidence

- Pure Lua: `tests/test_t2b_attack_policy_v2.lua` adds H7 positive near-terminal, distant/no-proof, and hard safety negative cases.
- Static mirror/guard check: `python tests/test_h7_attack_stall_contract.py`.
- Existing focused and full T2-B/H4/H5/H6 maintenance must be run locally or in one necessary consolidated Linux/Windows validation, not claimed here.
- **WH3 mandatory:** replay RT-TP-02 straight Move→Attack, RT-TP-03 angled/obstacle route, a short leg, one idle near-terminal stall, Move→Move H6 guide, and real Native early-future rollback. Require queue order/target, no native attack erroneously cancelled by terminal-stall gate, no diagonal route violation, no spurious early issue, no `CONTROLLER_FAIL`.
- Compare same game build and exact pack DLL/controller bytes; **do not** call a Github source commit an installed game fix.

**Immediate user fallback:** if an already-known-good pack exists, temporarily restore it after backing up current experimental pack and DLL; avoid mixing old controller source with a new Native DLL. No production pack files have been overwritten by this GitHub source candidate.
