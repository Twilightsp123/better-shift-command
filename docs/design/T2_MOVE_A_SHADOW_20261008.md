# T2-MOVE-A — exact immediate MOVE adoption: offline shadow architecture

**Status:** DESIGN / PURE-LUA SHADOW ONLY. No controller integration, no Move adoption permission, no WH3 test.
**Date:** 2026-10-08
**Parent baseline:** `maintenance/t2b-terminal-attack` at `2c2187edae771e8a5bf9b56f29b65d34786eb119`
**Isolated branch:** `maintenance/t2move-a-shadow`

## Confirmed current-code failure

In `R1.TransitionPolicy.evaluate()`, `successor.type=="MOVE"` unconditionally forces a closed `adopt_window` with `hard_violation=true` and `CANONICAL_INTERMEDIATE_ACTIONS_OWED`. This also happens for the exact immediate `i+1 MOVE`, not just an actual `i+2` overrun. SC6 already recognizes future Native orders by exact V3 execution identity; it then reads the closed policy envelope and triggers bounded rollback/reassert. Consequently Lua can fight a legitimate Native promotion even if route geometry would have authorized the same successor proactively.

This is an upper-layer policy asymmetry, not evidence of a Native address/VTable fault.

## Why simply widening the threshold is incorrect

`route_handoff_ready()` proves more than a distance:

- `PATH_SAFE` constrains current-waypoint deviation from the successor chord, minimum progress, and the shorter adjacent leg;
- `STEERING_CORNER` includes SC1/SC2 turn windows and caps by both neighboring Move lengths;
- SC3 permits unresolved prior route debt only if the *next* chord still preserves every debt corridor;
- SC4 allows a bounded stall escape, not arbitrary early folding;
- current `semantic_done` must not generate duplicate waypoint credit.

Thus **`threshold + one_poll_distance` is not, by itself, an adopt authorization**. One-poll travel compensates asynchronous observation only, not player route intent. Especially on U-turns, relaxing the corner/short-leg proof risks the previously observed self-compression failure.

When Native has already started the next Move, current sampled motion may reflect the new command. SC6 must not recompute permission for the earlier Move from post-promotion motion. `Core.observe_move_completion()` also executes before SC6, so pre-promotion evidence must be separately identity-scoped.

## Stage A: shadow-only proof (implemented here)

`maintenance_tools/t2move_a/t2move_a_shadow.lua` is pure Lua and does not connect to any controller API.

1. `capture` is permitted only when *exact active Native execution still matches CURRENT MOVE*.
2. It requires the canonical current/successor to be MOVE→MOVE, exactly `i -> i+1`, and binds generation, unit lifetime, action IDs, model time and actual poll interval.
3. It freezes scalar geometry plus the result of **the existing SC1–SC4 TransitionPolicy issue decision**. It cannot invent a new `PATH_SAFE` or `STEERING_CORNER` route proof.
4. On exact Native `i+1 MOVE` the preview requires matching identity and cache age ≤ one actual observed poll.
5. Stage A marks an adoption preview ready **only if the stored issue window was already open**, route proof was true, and route mode was `COMPLETE`, `PATH_SAFE`, or `STEERING_CORNER`. Otherwise it stays WAIT/HARD_BLOCK.
6. Completion preview: `STEERING_CORNER` completes the current Move; `PATH_SAFE` registers the current waypoint as route debt; `COMPLETE` has no new credit; previously owed SC3 debts are never silently repaid.
7. The result always has `authoritative=false`. It cannot submit a Native command, create/commit a transaction, or move the cursor. Live SC6 remains unchanged.

Stage A deliberately has **no ADOPT_ONLY hysteresis permission**. Its tests prove a safe proof contract, not a WH3 gameplay improvement.

## Stage B: planned Move adopt-only hysteresis

Add a distinct adopt envelope **only after** identifying per-mode temporal uncertainty windows that preserve route legality, minimum progress, old debt corridor, both adjacent-leg caps and Exit semantics. The band must not be a globally enlarged steering distance. Strong backtracking/hairpin regression cases are mandatory. No new arbitrary meter, angle, or percentage tuning parameter.

## Stage C: future controller/transaction integration

Only after A and B offline gates:

- proactive Move→Move retains existing SC1–SC4 issue permission;
- SC6 exact immediate MOVE consumes the shared *adopt* permission;
- `i+2` and later always remain hard rollback;
- success must create `OBSERVED` and call `Core.commit_transition_edge()`, not increment `idx` locally;
- `STEERING_CORNER` credit, `PATH_SAFE` current route debt, previously owed SC3 debt and T1.6 reject/timeout semantics must match the original ACK path;
- T2-B G1.1, Native Bridge/address files, and lifecycle code must remain unchanged.

## Gate and promotion status

- Stage A pure Lua fixtures: **20/20 PASS**.
- Stage A mutation tests: **12/12 CAUGHT**.
- WH3: **NOT RUN**; this is not a runtime or release claim.
- T2-B RT-TP-02/03: **BLOCKED / DEFERRED** as recorded in `docs/MAINTENANCE_TODO.md`.
- T2-MOVE: **NOT PROMOTED**; no change to the production `adopt_window`.
