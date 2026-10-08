# T2-MOVE-D — exact-current MOVE evidence snapshot (observation-only)

Status: **CONTROLLER-WIRED SHADOW OBSERVER CANDIDATE; NO MOVE ADOPTION ENABLED**.
Date: 2026-10-08
Isolated branch: `maintenance/t2move-d-evidence`
Parent: `maintenance/t2move-c-shadow` at `fcdf356671012ce7101ea0709565fb8ef028dbcd`

## Problem proven by Stage C
`transition_geometry_snapshot()` did not preserve `leg`, `progress`, `route_min_progress`, `threshold`, `stall`, or `cut_safe_limit`, so A/B route legality could not be revalidated from actual controller snapshots. Route debt can also be paid/pruned without incrementing `st.revision`, so revision alone cannot bind the debt set.

## D changes
- The transition geometry snapshot now carries those six MOVE proof fields plus `corner_stall_escape`; no scalar CFG values change.
- The new pure Lua `R1.T2MoveEvidence` module creates a **non-authoritative** snapshot only from exact-current MOVE with exact immediate MOVE successor.
- `R1.observe_t2move_d()` runs solely in SC6's `current_match` branch. It consumes the same shared `TransitionPolicy.evaluate()` decision used for normal Move issue, copies geometry, and freezes the last two actual pre-promotion position samples. One additional evaluator *observation* site is deliberate (8 → 9); the T1/T1.7/T2-B structural contracts are updated accordingly.
- The current block's route debts are fingerprinted deterministically. The identity includes block/action identity, debt action IDs, waypoint coordinates, exact tolerance, and semantic completion. Insertion, removal, repayment, changed waypoint or tolerance invalidates the old signature. Mere per-poll `last_remaining`, trend and progress updates do **not** invalidate it.
- Cache is cleared on generation cancel, transition abort, or T1.6 commit. The observer is otherwise inert: no Native issue, cursor update, abort/commit authorization, or weakening of MOVE's closed adopt envelope.
- For a future Stage E, `revalidate()` can compare generation, command revision, lifetime, current/successor identities, route debt fingerprint and one actual observed poll. Stage D does **not yet consume** that proof to authorize gameplay.

## Gate
- Pure Lua: geometry completeness, deterministic debt signature, mutation of debt set/identity, poll-time and waypoint sample consistency, frozen scalar copy, fail-closed identity.
- Real controller fixture: exact-current MOVE produces `T2MOVE_D_SHADOW_CAPTURE`; exact future MOVE **still rolls back**. No early route credit.
- Existing A/B/C tests, T1/T1.7/T2-B regressions, 46-job maintenance suite and docs contract all remain required.
- Source/src/template mirrors updated equally; Native/address untouched.

## Deferred work
- No replay of the post-Native MOVE trajectory to infer pre-promotion route legality.
- No `i+2` promotion or escape from previous SC3 obligations.
- T2-MOVE's joint A+B+C active adoption is a separate Stage E, not enabled here.
- T2-B RT-TP-02/03 remains **BLOCKED / DEFERRED**, with artifact documented in `docs/MAINTENANCE_TODO.md`.
