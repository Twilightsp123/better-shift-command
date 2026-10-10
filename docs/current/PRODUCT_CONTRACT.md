# BSC Product Contract — Native Shift behavior patch

**Authoritative correction (2026-10-10):** [PRODUCT_CAUSE_CORRECTION_20261010.md](PRODUCT_CAUSE_CORRECTION_20261010.md). Do not revive prior assertions that unmodified WH3 Shift MOVE necessarily stops at each waypoint. Historical experiments are evidence, not a substitute for this product observation.

## Distinct product problems

### P0 — Vanilla chained Shift MOVE causes intra-unit formation desynchronization

The player observes **different soldier models within the same unit card** reaching, turning at, and progressing beyond queued route points at different moments. Early models change heading while trailing models are still completing the leg; orientation mismatches and intra-unit crowding/jostling result. This is **NOT** a confirmed stop-and-restart of the whole unit after every native waypoint.

Acceptance target: improve *coherence of model-level path progression and formation travel* through guide points without distorting the player's intended route. Small physiological slowdowns when turning are normal, especially at 180 degrees; a constant-speed requirement is expressly rejected.

Exact cause is **open**: individual soldier arrival timing, formation-slot target assignment, unit/group promotion, steering, obstacles/collision, or combinations. Do not equate a read-only unit-level ring queue with each soldier having its own queued command list; prove any such mechanism before using it.

### P1 — Legacy BSC Lua MOVE→ATTACK pause/rollback regression

The conspicuous MOVE→ATTACK stop/delay reported during BSC testing was introduced by the earlier Lua Controller's arbitration/reissuing/rollback, **not shown to be a native vanilla stop bug**. Existing logs show BSC could overwrite an already accepted native ATTACK with MOVE. In the new architecture the old Lua active issuer must be retired/disabled; vanilla ATTACK is not to be patched unless *separate* evidence proves a native bug.

### P2 — ATTACK→EXIT MOVE→ATTACK product extension

Preserve desired target/minimum engagement time/exit guidance requirements if a safe native representation can be proven. Defer unsupported functionality instead of using the old shadow scheduler.

## Behavior and regression contract

- Same card, multiple soldier models: consistent route-leg progression, bounded relative heading divergence, reasonable model spacing and formation recovery, no crowding/wedging from premature individual turns.
- Route turns: straight, 90°, 135°, 180°/U-turn; short dense legs and zigzags; multiple units, different unit geometries and collision/terrain constraints.
- No mandatory exact waypoint-center intersection for guidepoints, but do not silently skip critical turns or cut across the planned route.
- Native right-click MOVE/ATTACK, REPLACE, HALT, queued future-tail identity, target death and combat state retain their original semantics. Avoid additional native/pathfinding/animation regressions.
- The successful implementation must actually improve the **models' observed formation motion**, not merely produce smoother unit-centroid coordinates or a synthetic path-pass assertion.
- Native MOVE→ATTACK must not be overwritten by old BSC; success cannot be claimed from removing Lua alone without a bounded final in-game acceptance.

## Implementation boundary and N1 proof requirement

WH3 retains original Shift input, queued order objects, queue advance/retire, original formation-slot assignment, per-soldier locomotion, collision and combat. BSC is allowed only *proven localized native decisions* in that original path, perhaps using exact-build guarded runtime DLL detours. **No new BSC executor, order queue, replay/reassert or direct OrderHead writes.**

First reverse **unit-level queued MOVE → formation target assignment → individual model movement / arrival / orientation → native synchronization or collision response**. Evidence must show which original decision causes premature/asymmetric progression and a minimal change that does not corrupt object lifetime. Old +0x18 Entity/MovementComponent assumptions are quarantined. An isolated queue pop, state-4 check or geometry early exit is not causal proof of intra-unit collision.

Version: user-provided 9.0.3-labelled EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`; version resource label unverified, existing addresses are exact-binary research, not patch-authorized.

## Verification gates

1. **STATIC:** object lifetime, exact x64 ABI, unit-vs-model semantics, formation target/promotion path, read/write effects, competing causes and precise native candidate.
2. **OFFLINE:** evidence-derived differential tests, no skipped route legs, no model-order desynchronization in the modeled proven branch, no second BSC commander. Synthetic tests are not WH3 physics evidence.
3. **WINDOWS:** stable exact-hash-guarded Hook, call-through, install/disable/cleanup failure handling including MinHook allocation; no partial patch.
4. **WH3:** one consolidated in-game acceptance focused on intra-unit model cohesion; MOVE→ATTACK separately confirms no legacy Lua regression. No Steam release before game proof.

**No-go:** if reliable change requires a new formation/pathfinding/collision engine rather than local native conditions, report the scope as infeasible instead of returning to a growing Lua Controller.
