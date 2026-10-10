# BSC Native Shift Behavior Patch — corrected implementation plan (9.0.3)

**2026-10-10 product correction is binding:** [PRODUCT_CAUSE_CORRECTION_20261010.md](PRODUCT_CAUSE_CORRECTION_20261010.md). The vanilla Shift MOVE defect is **within-unit model arrival/turn desynchronization and mutual crowding at route corners**, *not* a proven whole-unit stop at intermediate MOVE waypoints. The MOVE→ATTACK stop in prior BSC runs is attributed to the **legacy Lua Controller**, not a demonstrated vanilla engine flaw.

**Exact research EXE:** user-provided 9.0.3-labelled `Warhammer3.exe` SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`; version resource not independently authenticated. 9.0.2 RVAs are historical; current 9.0.3 addresses are research evidence, not patch-authorized ABI.

## Stage 0 — Preserve and correct scope — DONE for documents

- Freeze H8 reference `e711e716f2411599d75184618fc1ee5cb85bcd54` and `docs/past_doc`.
- Reject "Native Transition Owner", new BSC queue/executor, Lua canonical reissue and debt-based fixes.
- Correct former 9.0.3 N1 *braking-first* research plan. Retain ring pop, task state, special MOVE state transfer and route-geometry findings as valid **code-level background**, not proven explanation of the user's crowding report.

## Stage 1 — N1: reverse formation/model-level native behavior — ACTIVE

**2026-10-10 V3 evidence gate correction:** The existence of within-unit crowding during a *progressive* original Shift turn is now proven by real game member trajectories. The confirmed user behavior is not a bad instantaneous 180° command: CA already steers through gradual bends. Do not waste more work requiring geometrically matched ordinary RMB/Shift paths for defect recognition. The remaining N1 obligation is narrower: trace the actual V3 hit MOVE worker `0x03025D70` -> route config `0x0301287C` / task `0x02F2C734` to the true group/member steering consumers; the independently audited `0x0302DB44→0x030D5490` route had 0 hits in that real capture. Then select a reversible original group target/phase/avoidance predicate, preserve CA's bend sequence, and judge efficacy only by same-Shift pre/post measurements. See [N1_903_PROGRESSIVE_SHIFT_TURN_REAL_BASELINE.md](N1_903_PROGRESSIVE_SHIFT_TURN_REAL_BASELINE.md).


### Workstream N1-A — unit-to-model command/dataflow

Trace original **queued UnitRoot MOVE route leg** into (1) unit formation target/origin/heading, (2) model/slot target distribution and per-soldier movement state, (3) model-specific arrival/turn/next-leg updates, (4) group synchronization and collision response.

Use the actual 9.0.3 EXE; reconstruct x64 object pointer provenance, aliasing, per-entity membership, writers, readers and virtual consumers. Do not resurrect retracted Entity+0x18 MovementComponent layout. The unit-level order ring is already partly mapped but may be several layers above the actual bug.

### Workstream N1-B — distinguish common order versus independent model arrival

**P0 causal question (user clarified):** Can WH3 apply *one common Shift MOVE command* but let individual models independently mark the current waypoint reached / switch to the next leg? If so the first native change target is a **unit/formation-level leg promotion decision**, not a new command-issuance mechanism. Check this before searching for soldiers receiving different Shift commands. An alternative is a globally updated leg with asynchronous slot target/steering effects: explicitly falsify the independent-arrival hypothesis when evidence contradicts it. See [N1_903_SHARED_ORDER_GROUP_ARRIVAL_HYPOTHESIS.md](N1_903_SHARED_ORDER_GROUP_ARRIVAL_HYPOTHESIS.md).

**Do not assume the group should wait for all soldiers.** A bounded group passage criterion can trigger coherent phase change once; a single distant outlier must not trigger wholesale early turning. No guessed arrival radius, threshold tuning or new controller until real original producer/writer xrefs are verified.

### Workstream N1-B — divergence and coordination

Find which *original instruction condition* lets model A turn/change target while model B of the same unit is still executing the prior segment, OR find native group-wide route target changes that are spatially asymmetric. Distinguish per-soldier waypoint arrival from formation-slot target updates and collision/avoidance responses. The model-level root cause is OPEN and may be multiple interacting mechanisms.

Compare native unit-centroid/order timing with soldier pose and relative motion. Do not assume individual models each own an independent high-level Shift command queue. Record disassembly, control-flow graph, evidence grade and disconfirming cases.

### Workstream N1-C — old Lua regression isolation

Review H8 native ATTACK rollback/reassert path as a **BSC-introduced MOVE→ATTACK pause**. New Native mode will not issue/cancel old Lua movement/attack commands. Verify original generic ATTACK is capable of activation (already has static evidence), but do not invest in vanilla ATTACK braking Hook absent independent evidence.

### Required N1 output and pass

- Exact binary/ABI ledger for unit route → formation slots → soldier steering/arrival/turn → native group policy.
- A diagram showing the first divergent point in **same unit's soldier models**, not merely queue head.
- Proof that a localized original native condition could reduce crowding while preserving nav/collision/lifetime, OR explicit no-go if no such site exists.
- Candidate list marked **SEARCH / STATIC / WINDOWS / WH3**, unknowns never promoted to "verified fix".
- No engine-memory writes; old Lua H8 and historical map untouched.

## Stage 2 — N2: minimal formation-transition algorithm contract

If N1 identifies a safe policy boundary:
- Define exact per-model or group-level preconditions and original decision delta; preserve all original queue objects, motion solver and steering.
- Avoid a rigid all-models-present barrier that deadlocks on slow/blocked soldiers. Preserve curved geometry, realistic turn speed, path bend fidelity, unit shape and recovery.
- Specify branch invariants and negative controls (ordinary RMB, attack, stop/cancel, entity deaths, formation change, short legs, 90/135/180 turn).
- If patch requires rebuilding soldier collision/pathfinding or a parallel planner, **NO-GO** for minimal patch.

## Stage 3 — N3: offline evidence-derived differential tests

Use dataflow extracted from **real original functions**, with synthetic counterexample fixtures representing per-model asynchronous arrival, early turning, crowding, lagging model, blocked model, formation change and queued next leg. Establish expected behavior of *proven native predicate only*.

Track: original order identity, slot/target assignment, model-relative headings and spacing, native lifecycle and no double-trigger. Passing a mathematical route model is **not** proof of WH3 physical gameplay.

## Stage 4 — N4: exact-build in-process Native patch

Only after N1–N3 pass: guarded, reversible and narrowly scoped local patch at proven original function(s) in runtime memory. WH3 still handles orders, per-soldier movement, formation solver, physics/avoidance and combat.

Retire/disable old Lua active controller/reissue in new mode; Lua settings/diagnostics only. Do **not** automatically inherit legacy 16-Hook native-issuer bootstrap. Scope Hook count to the actually proven patch sites.

## Stage 5 — Hook reliability (parallel prerequisite)

Resolve legacy `MH_ERROR_MEMORY_ALLOC` using bounded isolated Win64 allocator/proximity instrumentation, exact build SHA/byte guards and partial install failure/cleanup, no unbounded retry. Process exit and disable safety must be demonstrated.

## Stage 6 — one consolidated WH3 gameplay acceptance

After static/offline/Windows evidence and packaging: test **within-unit soldier heading spread and mutual crowding** through straight, 90°,135°,180°, short zigzags, terrain, multiple units, formation changes and order REPLACE/HALT. Separately verify **no BSC Lua MOVE→ATTACK rollback** with normal ATTACK. Include ATTACK→EXIT route only if implemented with proven native semantics.

Deliver complete source, build recipe, DLL, normal+DEBUG PACK, hash manifest and explicit STATIC/OFFLINE/WINDOWS/WH3 status. No Steam publish before in-game acceptance.

## Immediate action

**Stop treating native terminal-braking/desired-speed or 0x0311F8CB geometry early exit as the primary suspected defect.** Start at per-soldier destination/formation-slot producer/consumer xrefs and prove how a single Shift MOVE leg is assigned to individual models. Use past native state/queue work only to bridge from a unit's original command to soldier-level movement. Distinguish H8 Lua ATTACK pause and leave native attack code alone unless new evidence requires it.
