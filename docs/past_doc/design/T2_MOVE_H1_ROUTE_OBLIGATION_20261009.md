# T2-MOVE-H1 — Route Obligation Shadow (NOT GAMEPLAY-PROMOTED)

Date: 2026-10-09. Parent: sealed G `580252224363c8d14fae1556ef15f4bee87e5377`.
Branch: `maintenance/t2move-h1-route-obligation-shadow`.
Draft PR: https://github.com/Twilightsp123/better-shift-command/pull/3

## 1. Architectural contradiction under review

The original `route_handoff_ready()` allows SC1/SC2/SC4
`STEERING_CORNER` before the player waypoint is physically visited.
`Core.commit_transition_edge()` then unconditionally marks that action
`semantic_done` after ACK or verified Native adoption. Those statements
describe **different facts**:

- *Execution handoff*: the successor is now executing (transaction committed).
- *Route satisfaction*: the player's waypoint has actually been reached or
  observed to be crossed, or a physically plausible debt route remains.

G protects some exact Native turnback adoptions but does **not** address
proactive BSC Move→Move ISSUE. Legacy tests explicitly require an early
proactive 180° U-turn. H1 must make this conflict visible before changing
the frozen permission contract.

## 2. Pure H1 classifier: necessary geometric evidence, no permissions

Module: `source/t2move_h1_route_obligation.lua`.
The same Lua 5.1 logic is embedded as `R1.H1RouteObligation` in all three
controller mirrors.

For a candidate current MOVE `P`, current observed position `X`,
successor destination `Q`, and the **existing** `move_reach_tolerance`
as `reach`, H1 independently determines one of:

| State | Evidence | Proposed H2 credit (not active in H1) |
|---|---|---|
| `SATISFIED` | Current action has a trusted completion reason backed by actual route arrival/observation (not legacy steering completion), position is inside existing reach, or a fresh observed motion segment crossed the reach envelope; unresolved prior debts must remain geometrically payable | `CURRENT_WAYPOINT_COMPLETE` |
| `DEBT_PRESERVED` | The `X→Q` successor chord passes inside the reach envelope around `P`, and every unresolved previous SC3 debt also remains inside its recorded existing tolerance | `REGISTER_ROUTE_OBLIGATION` |
| `BLOCKED` | Missing or invalid evidence, old debt would be cut, or successor chord cannot repay current waypoint | `NONE` |

A preserved chord proves **necessary geometric opportunity only**, not that
the CA engine will follow it. It must never be treated as actual completion.
**Completion provenance is mandatory:** the old `semantic_done=true` flag alone
is not accepted as arrival evidence. In particular,
`done_reason=STEERING_CORNER_HANDOFF` can have been set by the very
handoff we are auditing, so trusting it would make the proof circular.
H1 recognizes only route-observation completion reasons such as
`ROUTE_NODE_REACHED`, `ROUTE_NODE_PASSED`,
`HANDOFF_ROUTE_OBLIGATION_SATISFIED`, or `NATIVE_IDLE_ROUTE_FINISH`.
Unrecognized reasons must rely on separate live geometry instead.

A fresh motion segment is proof only when its two samples belong to an
observed forward model-time step. Unknown debt records fail closed.

This module is non-authoritative: it exposes `permits_issue=false`,
`permits_adopt=false`, and `authoritative=false` for **every** verdict.
It never sends commands, changes debt or increments the canonical cursor.

## 3. Controller observation points (no behavioral change)

- **H1_SHADOW_ISSUE:** when `advance()` evaluates MOVE→MOVE, log the
  H1 verdict alongside the unchanged `issue_window`.
- **H1_SHADOW_CURRENT:** when Native V3 still exactly matches current MOVE,
  log pre-promotion H1 and attach its scalar verdict to D's existing cached
  certificate **only as diagnostic data**.
- **H1_SHADOW_ADOPT:** on exact next Native MOVE, display the prior frozen
  H1 state. Do not recompute old-MOVE legality using successor motion.

All original G source is retained in `route_handoff_ready()`, T1.6
`Core.commit_transition_edge()`, and the gameplay CFG. H1 does not
change `TransitionPolicy` envelopes, dispatch, Native bridge or
journal capture. The H1 observer is outside the frozen T2-B
`route_handoff_ready` source-contract range.

## 4. Explicit mismatches exposed by H1

| Path at early handoff | Legacy G | H1 geometry | Interpretation |
|---|---|---|---|
| 0→100→200, current x=70 | Early forward MOVE / debt registered | `DEBT_PRESERVED` | Compatible necessary condition |
| 0→100→0, current x=60 | Early proactive `STEERING_CORNER` completion | `BLOCKED` | **Unresolved contradiction** |
| 0→100→(100,100), current x=60 | Early 90° steering may complete P | `BLOCKED` | **Unresolved route-fidelity contrast** |
| Same 90° corner at x=98, reach=5 | In completion range | `SATISFIED` | Legitimate no-full-stop handoff can be evaluated |
| Two prior unpaid waypoints on forward successor chord | SC3 soft continuation | `DEBT_PRESERVED` | Payability is still only a geometric hypothesis |
| Two prior debts, one outside successor chord | SC3 rejects | `BLOCKED` | Protects outstanding waypoint semantics |

These are deterministic synthetic examples, not WH3 trajectory
measurements. Do **not** erase or automatically rewrite the legacy early
U-turn test in H1; preserve it as conflict evidence for the next decision.

## 5. Offline verification gates

- Pure H1 fixtures: collinear, 90°, 135°, 180°, reach, fresh/stale
  crossing, two debts, short legs, malformed evidence, multi-unit purity.
- Controller observation: legacy proactive 180° still emits, shadow flags
  `BLOCKED`; Native frozen 180° and 90° compare without changing G
  adoption; straight Native still preserves route debt.
- Mutation checks: fail if prior debt geometry, motion freshness, issue
  shadow hook or pre-promotion frozen proof is bypassed.
- Byte-preservation contract: CFG, SC1–SC4 route evaluator, T1.6 commit,
  native/address paths and source/mirror/controller semantic sections.
- Existing E/F/G, A/B/C/D, full 46-job maintenance and documentation checks.

Record precise Actions run, commit and manifest only after final CI results.
`WH3_RUNTIME: NOT TESTED / BLOCKED`.

## 5.1 Additional provenance-hardening verification

After the initial 14-case proof set, H1 added a dedicated synthetic case
`H1-14`: an early steering handoff marked `semantic_done` still returns
`BLOCKED` when geometry misses the waypoint. A sixth behavioral mutant
attempts to trust every `semantic_done` flag and must be caught. This
does not alter the original G controller's completion logic; it only prevents
H1's independent analysis from inheriting G's circular assumption.

## 6. H2 gate (not implemented here)

Only after reviewing mismatches should H2 propose a shared edge-credit
protocol (handoff vs waypoint obligation) while keeping T1.6 the sole
cursor/transaction commit authority. Changing SC1 proactive steering,
RouteDebt reassert strategy or Native adoption requires an explicit
separate decision and its own red/green fixtures, not a hidden H1 change.
