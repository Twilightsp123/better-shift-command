# T2-MOVE-H2-A — Proactive Move→Move ACK route-credit counterexample

Date: 2026-10-09. Baseline H1: `b5020d9d437b91f3a0f1e410922f049630943105`.
Branch: `maintenance/t2move-h2-ack-route-credit`.
Draft PR: https://github.com/Twilightsp123/better-shift-command/pull/4

## Why this test exists

H1 proves the geometric distinction between transition execution and actual waypoint
satisfaction, but changes no runtime behavior. G protected some premature *Native
ADOPT* cases. H2-A tests the independent **proactive BSC ISSUE → Native ACK →
T1.6 COMMITTED** execution path with the exact real Controller + test fixture.

Legacy `route_handoff_ready()` permits `STEERING_CORNER` early, and
`Core.commit_transition_edge()` then calls
`mark_action_complete(...,"STEERING_CORNER_HANDOFF")` on any committed
MOVE steering edge. That operation is not conditional on observed waypoint reach.

### Observed unmodified H1 proof

[GitHub Actions 37827397901](https://github.com/Twilightsp123/better-shift-command/actions/runs/37827397901)
ran all existing A–H1 tests successfully until the new real-controller ACK step.
The new suite had **4 PASS, 2 FAIL**, exactly:

- H2-A01 (180°): command 0→100→0 sent at x=60, ACK occurs at x=60.
  `TRANSITION_EDGE_COMMITTED` is recorded and the current MOVE receives
  `ACTION_COMPLETE reason=STEERING_CORNER_HANDOFF remaining=40.000000`.
  This is a bogus completion assertion: P=100 has not been reached.
- H2-A02 (90°): at x=60, early perpendicular successor ACK commits the
  same `STEERING_CORNER_HANDOFF` with **40m remaining**.
- H2-A03/04/05/06 **PASS**: actual near-waypoint credit, legal forward
  `PATH_SAFE` route-debt registration, no credit before ACK, no credit on
  Native rejection. These constitute the positive/negative controls.

All claims are fixture results, **not** WH3 engine movement observations.

The baseline regression command intentionally exits nonzero. The separate
`test_t2move_h2a_expected_red.py` checks exact names, counts and the
two `remaining=40.000000` evidence lines, then allows CI to pass while
**explicitly preserving expected-red status**. A green CI wrapper does not
mean that the code defect has been fixed.

## H2-B protocol proposal (not yet implemented)

T1.6 must remain the **only** committed execution edge / cursor authority:

1. **Execution commit**: on verified Native ACK or exact Native adopt,
   `Core.commit_transition_edge()` records that action `i+1`
   is executing and advances the canonical cursor exactly once.
2. **Route obligation credit** is an independent consequence, derived from
   trusted arrival/observed-motion evidence, not from merely naming
   `STEERING_CORNER`. If a current MOVE is genuinely satisfied, record
   a single completion. If it remains payable, register its SC3 route debt
   without credit; if the successor path cannot preserve it, block future
   unsafe transitions and use an explicit recovery decision.
3. An explicit **issue-time route-fidelity gate is still needed** if a
   proposed steering command would make the old waypoint unreachable.
   Merely recording a debt after an unsafe ACK does not fix navigation:
   180° U-turn from x=60 back to x=0 plainly cannot pay waypoint x=100
   on its direct successor path.
4. **Do not casually change the old SC1 90°/180° U-turn tests in place.**
   They currently demand early steering and immediate semantic completion,
   in direct tension with strict waypoint fidelity. H2-B must replace
   that contract only in a separately documented branch with clear
   behavioral regressions and H1 evidence.
5. Avoid arbitrary distance, angle, speed or timing tuning. Use the
   existing `move_reach_tolerance`, SC3 debt corridor and G1 signals.
   Geometry cannot guarantee actual CA trajectory between poll samples.

## Implementation gates

- Confirm the exact failing ACK cases first (H2-A).
- Introduce pure H2-B route-credit transaction preview and test red→green
  independently before activating it in the Controller.
- Prove that the same current MOVE cannot earn `semantic_done` twice,
  that debts are recorded at most once and remain bound to generation,
  canonical action and unit lifetime, and that ACK rejection/timeout never
  earns credit.
- Native ADOPT and proactive ISSUE/ACK must share route-credit policy
  even if their issue/adopt timing windows remain distinct.
- Keep T2-B/ATTACK/EXIT gates, G Native frozen evidence, Native DLL, fixed
  addresses and gameplay CFG untouched unless separately proven essential.
- Run full A/B/C/D/E/F/G/H1 regression, 46-job maintenance, explicit
  mutation gates and mirror/source archive validation.
- WH3 runtime RT-TP-02/03/04/05 is still **BLOCKED / NOT TESTED**.

This H2-A stage changes **only tests, docs and CI**, not player-control logic.
