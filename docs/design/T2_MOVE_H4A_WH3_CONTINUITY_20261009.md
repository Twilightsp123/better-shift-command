# T2-MOVE H4-A — WH3 observed waypoint pause and independent continuity control

Date: 2026-10-09. Base is the **verified Windows-built 9.0.2 H2/H3 candidate** at
`1dedee4a31dff3daa8ce0e9ca584f1a35b3be9b7`.
This H4-A branch is a **test/design-only expected-red baseline**. H2/H3 game behavior
is unchanged and is not claimed repaired or promoted.

## Actual WH3 runtime evidence

User supplied `script_log_091026_1109.txt` from WH3 9.0.2.

- `BRIDGE_OK version=1.0.18-corepath-wh3-fec656f4-map902`,
  `OBSERVER_READY`, `START`, `READY` all present.
- `CONTROLLER_FAIL` zero.
- `H2_ROUTE_ISSUE_BLOCKED` **259**: **192**
  `H1_SUCCESSOR_CHORD_MISSES_WAYPOINT` plus **67**
  `H1_PRIOR_DEBT_CHORD_MISSED`.
- `DISPATCH_MOVE` **20**: **14** `MOVE_AFTER_NODE_COMPLETE`,
  **5** `PREDICTIVE`, **1** `ATTACK_COMPLETE_LATCHED`.
  Three of the 14 after-node issues reported `speed=0`.
- `NATIVE_SUCCESSOR_ROLLBACK` **22**, `REASSERT_MOVE` **23**;
  rollbacks: 14 missing prior prepromotion cert, 8 actual native
  canonical i+2 overrun. **These are separate from the 259 H2
  geometric rejects and must not be generalized as one cause.**
- `uid=1004 gen=5 current=3 successor=4`: at model_ms 163600,
  `legacy_issue=true` with `remaining=32.607380` and
  `chord_error=32.607380`, against `reach=10.100000`;
  H2 BLOCKED. At model_ms 166200, remaining still 11.199580 >
  reach 10.1, so still BLOCKED. Only at model_ms 166600
  `ACTION_COMPLETE reason=ROUTE_NODE_PASSED remaining=9.059685`
  was successor issued using `MOVE_AFTER_NODE_COMPLETE`, ACK
  at model_ms 167100.
- `uid=1004 gen=5 action=6`: at model_ms 204900, after sustained
  BLOCKED verdicts, `NATIVE_IDLE_ROUTE_FINISH remaining=13.669074`
  with speed 0, then the next command was issued. This is particularly
  strong evidence of visible stepwise motion.

The observations substantiate an **in-game movement-flow regression**.
Not every issued action has speed zero: 14 after-node dispatches include
11 with nonzero reported speed. Distinguish late issuing from literal
stopping rather than conflating them.

## Structural impossibility of naive H2 relaxation

Let current leg A=(0,0) → waypoint P=(100,0), current location
S=(60,0), next waypoint C=(100,100).

- H2's reach envelope is grounded in the existing unit width/leg
  geometry, e.g. real-game log reach 10.1.
- If a new immediate Native MOVE is issued straight from S toward C,
  the direct successor segment S→C has a minimum distance of roughly
  37.1 to P. It cannot satisfy a 10.1 waypoint envelope.
- The old SC1 `STEERING_CORNER_HANDOFF` credit *invented* completion;
  H2's veto avoids inventing it, but leaves the unit approaching a
  terminal destination until it may brake or stop.
- A single instantaneous `goto_location(C)` command from x=60 **cannot**
  simultaneously preserve P within the envelope and turn without
  terminal behavior. The conflict is command ownership/path
  representation, not an arbitrary angle or distance threshold.

A global `H2_ROUTE_ISSUE_BLOCKED` bypass is **not an acceptable fix**:
it reintroduces the H2-A false-waypoint-completion or impossible unpaid
debt regression.

## H4 candidate architecture, NOT YET IMPLEMENTED

Investigate **virtual run-through / nonterminal current-leg
continuation** separately from canonical successor execution:

1. At a verified pre-braking opportunity for ordinary MOVE→MOVE with a
   pending successor, compute a continuation destination **beyond P
   along the observed incoming leg**, rather than sending C directly.
   The stretch must be derived from observed movement/braking and
   structural geometry, NOT guessed constant meter/angle/time values.
   Do not claim geometry alone proves the destination is navigable;
   require existing engine/nav evidence or explicitly fail closed.
2. Issue a **tracked auxiliary MOVE** with its own Native issue/ACK
   identity and generation. Preserve canonical `st.idx` and
   `P` obligation. Auxiliary ACK **must not call**
   `Core.commit_transition_edge` or manufacture
   `semantic_done`/successor credit.
3. Observe actual route reach/crossing P **while still moving**. Switch
   to real C as a normal T1.6 single-commit successor transition
   only with a fresh independent route-proof. The auxiliary command
   must not survive a plan REPLACE, aborted issue, new generation,
   entity lifetime change or battle teardown.
4. Canonical Native V3 identity and side-channel attribution must
   explicitly recognize the auxiliary owner, not regard it as
   an unauthorized user REPLACE or a finished canonical node.
   Keep `i+2` future overrun and unrelated Native commands fail-closed.
5. For Attack/Exit, do not activate auxiliary movement until
   the separate T2-B/EXIT policies have evidence that this cannot
   alter combat or disengagement logic.
6. First test one straight transition and one 90-degree run-through,
   then 135/180, debt, replacement, rejection, multi-unit, and
   actual WH3 braking/trajectory. Record **two independent outcomes**:
   waypoint fidelity AND continuous motion.

**Risk:** a synthetic beyond-waypoint continuation can itself create
collision/pathfinding hazards or unnecessary overshoot on tight
turnbacks; it must be bounded by verified native path evidence before
gameplay authority. This is an architecture candidate, not an
established working fix.

## H4-A red safety contract

`maintenance_tools/t2move_a/test_t2move_h4a_continuity.lua` is a
real-controller failing-first fixture. It deliberately requires
a noncanonical inbound run-through MOVE for a 90° and an 180° corner
**before** the current Native order reaches the terminal node, while
forbidding direct unsafe successor commands and synthetic waypoint
credit. On the frozen H2/H3 Controller, these two cases are expected
to fail because it makes no such movement continuation.

The other three control cases must pass: forward PATH_SAFE debt
continues, pending ACK cannot commit, Native rejection cannot commit.
`test_t2move_h4a_expected_red.py` checks exactly 2 red + 3 green;
green wrapper means only that the bug/specification gap is reproduced,
**not** that H4 movement works.

## Decision gates

- Freeze current H2/H3+9.0.2 pack as an **offline/build-passing but
  movement-unsatisfactory experimental candidate**, no release.
- Do not merge the H4-A tests alone into production.
- H4-B would implement a narrow generation/Native-identity-safe
  run-through protocol and make the red tests green.
- H4-C: stress previous debts, i+2 races, Native rejection and
  replacement without relaxing route obligation.
- H4-D: rebuild 9.0.2 Windows Native if needed, complete offline
  regressions, deliver single traceable debug PACK.
- H4-E: judge real WH3 route smoothness by video and script-log
  ACK/motion timestamps, not offline geometry PASS alone.

Existing 9.0.2 v142 DLL, the completed H2/H3 controller and all
legacy branches remain unchanged.
