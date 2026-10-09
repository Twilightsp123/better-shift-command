# T2-MOVE-H4S — speed-first soft waypoints, exact Native ACK

Date: 2026-10-09. Base: isolated fully built WH3 9.0.2 H2/H3 candidate
`1dedee4a31dff3daa8ce0e9ca584f1a35b3be9b7`. Branch:
`maintenance/t2move-h4-soft-corner-speed`.

## User intent, amended

**Movement speed and flow are the top priority.** Intermediate player
waypoints are approximate directional guides; do not require literal
arrival at every coordinate. A bounded rounded corner near the indicated
position is acceptable. This explicitly supersedes H2-C's hard geometry
requirement and H4-A's speculative beyond-waypoint Q auxiliary command.
H4-A remains archived as evidence of H2's overconstraint but its
"must send Q before P" assertion is NOT a product requirement.

Do not use the game logs to claim an observed velocity gain until WH3
runs this H4S build. WH3 9.0.2 H2/H3 startup passed, but real H2 movement
was stop-and-go with 259 issue denials and Native rollback/reassert traffic.

## Mechanism

Existing SC1/SC2/SC4 computes a bounded steering-authorization window
from actual speed, formation width, turn severity and both adjacent leg
lengths. H2 independently used an exact successor chord-to-waypoint
reach comparison as a veto, so even when the original moving turn window
was open, it delayed the next MOVE until at/after the node.

H4S **reuses that already-validated steering window** for pure MOVE→MOVE
when H1's independent physical proof returns
`H1_SUCCESSOR_CHORD_MISSES_WAYPOINT`, on conditions:

- The current legacy policy's MOVE issue window is actually open.
- `g.route_mode == STEERING_CORNER` with an actual SC1/SC4 reason.
- Existing bounded corner-window progress/remaining checks pass.
- No prior SC3 unpaid waypoint debt remains.
- The source and successor are both MOVE, not ATTACK or EXIT.
- The independent H1 evidence result is precisely
  "current successor chord cuts the present node", not missing
  data, invalid geometry or unpaid prior-debt deviation.

**Three semantic outcomes, not an overloaded reached flag:**

- `SATISFIED`: independent observed actual proximity/crossing.
- `DEBT_PRESERVED`: PATH_SAFE forward chord retains a payable physical
  old waypoint obligation after ACK.
- `CORNER_SOFT_ACCEPTED`: real Native ACK commits the new MOVE edge,
  then records `ACTION_COMPLETE reason=H4_SOFT_WAYPOINT_ACCEPTED`,
  a deliberately **semantic rounded guidance credit**. It is NOT a
  claim that the unit physically occupied the old waypoint coordinate.
  No impossible SC3 return-to-node debt is created.

The policy is frozen into the exact T1.6 transition geometry before
BSC ISSUE, and re-evaluated after Journal drain immediately before
dispatch. Native exact `i+1` adoption consumes equivalent prepromotion
proof (plus its separate T1.7 adopt time window). G's original Native
turnback limit is relaxed **only for an explicitly frozen permitted soft
corner**, not for missing provenance or incorrect generation/revision.
No `i+2` skip, unidentified Native command or missing ACK is promoted.
T2-B MOVE→ATTACK strict credit and Exit/Combat remain unchanged.

## Explicit limitations

- SC1/SC2's current turn window itself is a *heuristic* backed by
  native/formation observations, not a guaranteed geometric spline.
  A speed-first rounded 90°/180° early turn can visibly cut an
  intermediate player waypoint. That tradeoff is user-authorized,
  but actual amount and aesthetic acceptability require WH3 video.
- This patch does NOT rewrite CA's original Shift queue or implement
  the unproven H4-A auxiliary Q machinery.
- This patch does NOT eliminate Native `i+2` overruns, no-proof
  rollbacks or the need to analyze their effect in subsequent WH3 logs.
- Smoothness and movement speed cannot be validated by Lua fixture
  speeds; use real video and motion traces.

## Offline behavior tests

`test_t2move_h4_soft_controller.lua`: early 90° and 180°
issues+ACK, distinct semantic credit, forward debt, 5m short-next-leg
guard, older unpaid-debt protection, pending/rejected ACK.

`test_t2move_h4_soft_native.lua`: Native queued exact i+1 90° and
180° soft adoption and canonical T1.6 commit, collinear payable debt,
stale-revision rejection.

`test_t2move_h4_soft_mutations.py`: neutralizes the new permit,
fakes a physical-arrival reason, disables Native shared soft evidence,
and forces erroneous Native debt credit; each must be caught by active
real-Controller fixtures.

The previous maintenance tests that required the H2 no-turn policy
were explicitly updated to test soft rounding instead. The A/B/C/D,
T1.6, T2-B, address map, Native DLL and CLI contracts remain in
the original 46-check CorePath regression. Older H2/G/H1 branches
and their tests remain unmodified in GitHub.

## Real-game smoke sequence

- Install exactly ONE H4S 9.0.2 diagnostic PACK; disable the prior
  H2/H3 and Workshop BSC version.
- First check `BRIDGE_OK`, `OBSERVER_READY`, `START`, `READY`.
  DLL must be 1.0.18 / EXE hash `fec656f4...`.
- Then one unit in unobstructed field: (1) straight chain, (2)
  90° at long spacing, (3) 180° foldback, (4) 5–15m zigzag,
  (5) Move→Move→Attack, (6) two simultaneous units.
- Each trial separately report: did the unit keep visibly moving
  through the turn, was turn timing acceptable, did it skip an
  entire route leg, were issued/Native commands repeatedly rolled back?
  180° may geometrically reverse direction with no literal full-stop,
  but video should identify whether the unit visibly parks or jitters.
- After every test retain original battle `script_log_*.txt` and
  video, exact PACK hash, game build and other enabled mods.

**Status:** 9.0.2 Native build was separately Windows v142 CTest
14/14 PASS and byte-identity locked. This H4S gameplay-specific variant
still requires its own CI and WH3 runtime results before any promotion.
No merge / Steam publication.
