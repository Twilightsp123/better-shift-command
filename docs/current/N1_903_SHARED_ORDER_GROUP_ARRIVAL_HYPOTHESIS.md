# N1 P0 — Same command, independent model arrival? Group-phase hypothesis

**2026-10-10, user clarification. Hypothesis, NOT an established WH3 internal behavior.**
This supersedes any project narrative that the BSC bug necessarily means separate Shift commands are delivered to each soldier model. Observed behavior: some soldiers in one unit-card turn toward the next queued destination before trailing soldiers have finished the previous leg, and they crowd one another.

## Important distinction: three different layers

- **Order identity:** one native Shift queue / one active unit-level MOVE may be fully consistent with the observation. Existing exact-binary queue and MOVE→unit-route research is at this level, not evidence of separate model commands.
- **Arrival and route phase:** the same original unit-level destination can be decomposed into different assigned formation-slot destinations. Each model may use its own `near_destination`/path completion signal or the engine may update group target globally. Distinct **arrival decisions** do not imply distinct **high-level commands**.
- **Physical response:** even if a group advances the route phase simultaneously, models with different speeds, slots, avoidance and turn radius can exhibit different headings. A shared phase alone may not entirely eliminate crowding. Prove the first cause.

## Priority hypothesis H-P0-A

The engine uses common queued MOVE `leg=k`, but model-specific arrival/status conditions let model A advance toward `k+1` while model B remains on `k`. This causes opposite or crossing movement near waypoint corners, especially with 90°/135°/180° turns.

This would be a **coordination/promotion predicate defect**, not multiple Shift command issuance and not vanilla stopping.

### Alternative H-P0-B

Only the unit/formation route phase is advanced globally, but per-model slot targets and steering/avoidance update at different times or demand conflicting motion. Here no independent leg-index promotion exists, and forcing model-level phase synchronization would target the wrong system.

### What would discriminate them in the original WH3 binary?

1. Start at verified original MOVE worker `0x03025D70` → `0x0301287C` → unit route pointer `root+0x270`. This proves the unit route source only.
2. Resolve concrete member/submember vtables and the consumers of unit route `+0x270` (candidate `0x03012A6C`, vfunc `+0xC8` is not yet identified). Follow native formation-slot assignment, destination and facing **writes**.
3. Determine whether a per-model field represents `current waypoint/leg phase`, `arrived`, or merely path steering. **Look for a condition which writes/advances different per-model phases on the same original unit order.**
4. Independently recover any unit/group completion or common route-transition event and which native targets it distributes. Compare queued Shift with ordinary RMB and native group-turn controls.
5. If there is **only a shared route phase** and no per-model advancement, reject H-P0-A and pursue slot geometry / independent steering / collision (H-P0-B). Do not invent separate model queues.

## Potential patch *only after* proof

If H-P0-A is real, prefer an original-engine **unit/formation-scoped, one-time route-phase promotion**: a valid bounded group-level waypoint passage condition (e.g., formation reference/pivot, qualified leading subset and geometry, not necessarily all models arrived) enables the group to advance, and all model destination/heading assignments are refreshed coherently by WH3's native path. It is **not** a hard all-models-arrived barrier, and is not automatically "first soldier ever near it" (outliers or a separated model could trigger an unintended turn).

Preserve full route bends, especially U-turns; blocked/casualty/out-of-formation fallback; gradual physical heading change; native avoidance. The common command must not be replicated via Lua or a parallel BSC planner.

If H-P0-B is real, this patch concept is wrong: fix the actual native formation-target / steering update discontinuity instead, if a safe local change exists.

## Negative controls and required evidence

- Same queued unit command, two models with different approach distances, shared destination but staggered *candidate* arrival flags: no early heading conflict from different leg phases after a proven group-level predicate.
- Single outlier reaches waypoint extremely early: must not cause all remaining models to cut a crucial corner.
- Slow/blocked model: must not deadlock the entire unit waiting for 100% exact arrival.
- 90°, 135°, 180° and short zigzag: no skipped required turn, no collapse of spacing, no formation jamming from sudden remapping.
- Normal RMB, nonqueued REPLACE/HALT, ATTACK and old Lua MOVE→ATTACK regression must remain independent.
- Distinguish engine observation **STATIC/WH3** from synthetic scenario analysis **MODEL**. These examples are hypothesis-test designs, not evidence that a WH3 predicate exists.

**Status: H-P0-A and H-P0-B OPEN. No code patch, address, per-soldier arrival offset or working mod established.** 
