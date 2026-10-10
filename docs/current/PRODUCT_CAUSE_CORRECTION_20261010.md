# BSC product-cause correction — formation desynchronization, not vanilla stopping

**Decision date:** 2026-10-10  
**Authority:** explicit user correction of the observed behavior. This document supersedes any contradictory *problem statements or prioritization* in the current 9.0.3 plans. It does not upgrade hypotheses to reverse-engineering proof.

## 1. Two different issues were mistakenly conflated

### A. WH3 native Shift MOVE → MOVE (the original BSC product defect)

**User-observed behavior:** during chained native Shift MOVE waypoints, **individual soldier models/entities within one unit card do not reach and turn at the waypoint in coordination**. Some models have arrived and begun to reorient or proceed while others are still approaching. Their headings and intended trajectories diverge, creating crowding, interpenetration/pressure and mutual jostling within the formation, especially through corners and short segments.

**Important distinction:** The original complaint is **NOT** that the native Shift MOVE necessarily brings the unit card to a full stop at every intermediate point. Do not describe native Shift as a confirmed stop-and-go waypoint system. Do not use average unit speed alone as the acceptance metric.

**Still unverified cause:** whether per-soldier waypoint completion, the mapping of formation slot destinations, group-level transition synchronization, path handoff, collision/avoidance or turn timing is the dominant defect. User-visible models moving differently does NOT itself prove each model owns a separate high-level Shift command queue. Avoid that unverified inference.

### B. MOVE → ATTACK stops/pauses in legacy BSC Lua Controller (regression)

**User-reported attribution:** the conspicuous stop before ATTACK arose from our Lua replacement/controller mechanism, not the stated vanilla Shift MOVE defect. Historic H8 logs show a queued native ATTACK could be followed by BSC's nonqueued MOVE rollback/reassert. Therefore **treat it as a BSC-introduced regression** until a separate unmodded-engine reproduction establishes otherwise.

The first fix is **remove the BSC conflicting reissue/rollback controller from the new mode**. Do NOT alter original WH3 ATTACK handoff based merely on old Lua regression logs, and do not justify a new Native ATTACK Hook by the fact this old implementation stalled.

### C. ATTACK → EXIT MOVE → ATTACK

This is a feature/product requirement of BSC, but any new implementation must have independently proven native semantics. It cannot be used to justify reviving the Lua shadow scheduler. Scope it separately from the original Shift MOVE formation defect.

## 2. Target outcome and acceptance

**Primary:** Under Shift MOVE→MOVE→MOVE, the native unit's constituent models maintain useful mutual alignment and coherent formation travel around route turns; avoid cases where early-arriving soldiers rotate/leave while others are trapped or cross through them. A bounded, realistic group turn or local slowing is allowed; no hard requirement that all soldier speeds stay constant or that the unit never slows.

**Secondary:** MOVE→ATTACK must not be delayed or overwritten by BSC. With the Lua controller removed, verify original ATTACK activates as intended before entertaining native changes.

**Regression controls:** straight multiple waypoints, 90°/135°/180° turns, close-spaced zigzags, dense formation, mixed model speed/terrain/obstacles, single/multiple selected units, ordinary RMB REPLACE, HALT, target death, and game exit. Preserve original order identities/sequence, collision/navigation and animation lifecycle. An overly rigid formation that blocks pathfinding is a failure.

**Evidence measurements**, when real instrumentation becomes safe: time series for model/subgroup position and facing, slot/relative displacement, within-unit heading spread, model spacing/compression, native active-order identity, and command transition timestamps. Prefer invariants and comparative traces over tuning arbitrary thresholds. Synthetic fixtures prove dataflow/model assertions, not WH3 physical behavior.

## 3. New N1 static-research critical path

1. **Separate abstraction levels.** Trace queued *unit-level* order issuance and completion only as context. The root cause search must descend from UnitRoot/native MOVE task to **formation command/slot assignment → soldier/entity movement target → per-soldier arrival/steering/turn execution → collision/avoidance**. Confirm every object pointer/offset and ownership on the exact WH3 9.0.3 hash. Historical Entity+0x18 MovementComponent hypothesis remains quarantined.
2. **Prove the divergence point.** Locate precisely whether different soldiers receive different effective waypoint targets, decide arrival independently, receive the next leg at different times, or update orientation independently. Record opcode/dataflow and meaningful alternative hypotheses; don't infer the cause from names such as "state" or "route".
3. **Identify existing WH3 group coherence behavior.** Follow formation slots, group pivot, target distribution, path-follow updates and any native group-level synchronization already present. The aim is to change the smallest native decision/predicate **in the same original call path**, not to coordinate soldiers from a new BSC loop.
4. **Assess feasible localized changes.** If WH3 has a safely patchable unit/formation-level transition criterion, validate it against short-legs, corners and 180° turn cases. If coherence needs broad soldier movement, collision or pathfinding rewrites, explicitly mark minimal Native Patch as not feasible rather than inventing an external scheduler.
5. **Handle legacy Lua ATTACK separately.** Disable old controller issuing/rollback in the new mode. Investigate original ATTACK only if evidence from native-only execution independently establishes a defect. Do not spend N1 cycles finding "vanilla ATTACK braking" on the basis of H8 failures.

## 4. What previous N1 reverse engineering does and does not establish

Retain as **mechanism evidence**, not defect causality: exact 9.0.3 queue pop (0x02F4FD10), native MOVE VTable/state/task path, conditional MOVE successor state transfer, ordinary ATTACK activation and geometry route branch (0x0311F534 / early exit 0x0311F8CB). These prove relevant native structures exist. **None proves the soldier-level crowding/desynchronization mechanism**, and none establishes a genuine vanilla stop at Shift MOVE junctions. The geometric early exit is NOT an approved brake fix.

Prior plans placing terminal braking/desired-speed at the top of N1 or proposing a universal MOVE arrival-distance patch were based on an incorrect product diagnosis. Reclassify them as lower-priority, conditional investigations only where they relate to real formation-model divergence.

## 5. Safety & status

- No second Lua/C++ command executor, canonical shadow queue, repeated MOVE/ATTACK issue, raw OrderHead mutation, forced state=4 or flag=1, VTable-wide enable, or arbitrary pass-distance tuning.
- Keep native engine the sole owner of orders, movement, formation, physics and attack.
- No claimed engine ABI, per-soldier offset or Hook without exact machine-code proof and thread/lifetime safety.
- No Windows runtime DLL or WH3 gameplay acceptance performed for this correction; no Steam release.
- Current phase is **N1 reformulated**, not N2/N4 implementation-ready.

**Immediate task:** recover the native per-model/formation movement transition from UnitRoot and formation/task callers, not just the unit-level ring queue's head writer. Use offline disassembly and source evidence, then update candidate function ledger with its proof grade.
