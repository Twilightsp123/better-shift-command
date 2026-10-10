# WH3 9.0.3 — Native Shift formation-coherence research design

**Authoritative product correction:** [PRODUCT_CAUSE_CORRECTION_20261010.md](PRODUCT_CAUSE_CORRECTION_20261010.md)  
**Implementation sequence:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)  
**Date of corrected scope:** 2026-10-10  
**Status:** N1 STATIC reverse engineering only; original model-level cause and patch site UNKNOWN, no DLL/PACK or release.

## 1. Actual defects and architecture

**Vanilla chained Shift MOVE:** individual soldier models in one unit card arrive at or turn around consecutive waypoints at different times/directions. Their divergent headings and positions cause crowding, mutual obstruction and degraded formation coherence. **This is not a confirmed whole-unit native stop at intermediate MOVE waypoints.**

**Historical BSC Lua MOVE→ATTACK:** the conspicuous stop/attack pause is a regression of the old Lua Controller's active arbitration, reissue and rollback path. Its fix in the replacement architecture is to *remove that competing writer*, not assume native ATTACK transition requires a patch.

**Design rule:** game retains original Shift/RMB input, native order queue, group formation and per-model path/steering/collision/combat. A Windows x64 DLL may be used solely for narrow guarded edits within existing original code. No BSC canonical route plan, scheduler, repeated MOVE/ATTACK, artificial queue head advance, second formation controller, or raw slot mutation.

## 2. Exact build evidence versus new unknowns

Target research binary supplied by user (labelled 9.0.3): SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, preferred image base `0x140000000`. VERSIONINFO independent check remains open. Do not use old 9.0.2 RVA/guard/VTable values as valid 9.0.3 patch sites.

**9.0.3 mechanisms recovered, but not causally attributed to crowding:**
- Native 40-slot ring pop at RVA `0x02F4FD10` (count/head write, original object cleanup).
- Original MOVE task/status path and state-object creation, task count `+0x240`, transfer through MOVE `+0xA0`, state machine 0–4.
- Specific *conditional* native MOVE-to-MOVE state transfer; normal original ATTACK activation is a separate path.
- Native route processing `0x0310F560` and geometry/route-setup branch at `0x0311F8CB`. The branch skips guarded route setup, **not proven to stop soldiers**.
- None demonstrates how individual soldiers select their target/turn or why some soldiers crowd laggards. A unit-level pop is NOT a soldier-level completion rule.

**Unverified:** per-soldier entity identity and safe pointers; formation-slot writer/consumer, soldier steering target/arrival predicate, heading/turn selection timing, collision/avoidance updates, unit/group synchronization and any patch-safe ABI.

## 3. Primary research route: unit command → soldier motions

### A. Recover formation mapping, NOT a second executor
1. Start from exact native unit MOVE issue and already recovered MOVE task/object to identify the formation/group controller that transforms one unit-level waypoint into model-specific targets.
2. Trace how each soldier is assigned a formation slot, position, orientation and current/next segment. Confirm read/write xrefs and root/subobject pointer derivations at x64 instruction level.
3. Trace soldier-specific arrival, next target activation, turning and collision response. Determine which operations can happen *asynchronously* among models sharing one unit card.
4. Distinguish independent per-soldier movement phases from globally updated formation target causing variable model travel distances. User-observed asynchrony does **not** establish separate per-soldier high-level Shift queues.
5. Retain normal RMB MOVE and individual soldier collision/terrain cases as negative controls.

**Do not reuse the retracted Entity+0x18 MovementComponent mapping or unverified old "physical evidence".** Re-establish all structs and virtual dispatch for exact executable hash.

### B. Locate first divergence: competing hypotheses

| Hypothesis (all OPEN) | Engine observation that would support it | Disconfirmation |
|---|---|---|
| F1: per-soldier early waypoint arrival/turn | Soldier-specific predicate advances target/facing before other soldiers complete same leg | only group-wide transition exists; divergence emerges afterward |
| F2: formation-slot destination assignments jump/mismatch | Native group target/rotation update assigns discontinuous/overlapping model-specific slots | assigned targets remain coherent, soldiers diverge due to steering |
| F3: variable model path distance / avoidance causes compression | per-soldier path planner/collision redirects lagging models while others turn | geometry difference absent; problem is phase timing |
| F4: native group transition coordination policy too weak | unit/formation-level native condition allows mixed leg phases despite known laggards | engine already coordinates phases; crowding occurs elsewhere |

Use exact-function control/dataflow and a **model-level** timeline to select or reject each. Speed or route-geometry scalars alone are not cause proof.

### C. Candidate patch scope, only after cause proof

**Preferred:** alter the smallest original formation-phase/slot update predicate so constituent models receive coherent target/turn timing while preserving original locomotion/avoidance.

**Conditional:** localized native group waypoint promotion or existing model arrival policy correction when true fault lies there. Must preserve non-queued behavior, supported mixed mobility and bounded fallback for blocked models; never introduce a permanent barrier waiting for the slowest soldier.

**No-go:** if reliable solution demands replacing per-soldier physics/pathfinding, rebuilding formations, or a BSC shadow controller, refuse minimal patch rather than reintroduce legacy Lua reissuing.

## 4. Native ATTACK regression handling

Original ATTACK `+0x08` work submission and generic head activation already have static evidence, and ATTACK's rejection of special MOVE state transfer is by design for **that** path. It does not imply vanilla MOVE→ATTACK stops.

Disable legacy Lua active issue/rollback first in the new Native mode. A direct original ATTACK Hook is *not* automatically required; its necessity would require a separate native-only reproduction and real ABI/target-lifetime proof. ATTACK→EXIT MOVE→ATTACK remains separately scoped pending feasible native semantics.

## 5. Engineering stage gates

- **N1 (active):** exact build object-map and first model-level divergence, ownership/threads/ABI, competing hypotheses falsified as appropriate; if no native source supports a minimal fix, STOP/NO-GO.
- **N2:** exact native delta and invariant contract; no per-soldier shadow queue, no raw OrderHead writes, original target/slot identities retained.
- **N3:** evidence-derived offline differential scenarios (straight, 90°, 135°, 180°, zigzag, blocked model, sparse/dense formation, terrain, multiple units, RMB REPLACE/HALT, ATTACK); synthetic geometry cannot demonstrate WH3 model behavior.
- **N4:** version-guarded runtime code patch only after verified original predicate/ABI, with no legacy Lua dispatch.
- **N5:** independently fix Win64 Hook installation/lifetime issues (MinHook memory allocation, partial creation, process exit).
- **N6:** one consolidated bounded WH3 acceptance measured on actual **soldier headings/spacing/formation** and separate Lua regression removal; provide full source, build evidence, DLL/PACK hashes only when built and verified. No automatic Steam publication.

## 6. Archive/source handling

All prior exact-file research under `docs/current/N1_903_*.md` is preserved **as static engine mechanism evidence**. It must not be cited as proof of a vanilla whole-unit stop or a finished BSC patch. The new [PRODUCT_CAUSE_CORRECTION_20261010.md](PRODUCT_CAUSE_CORRECTION_20261010.md), [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md), and this design take priority for what the product is fixing.

**Immediate N1 task:** from UnitRoot original queued MOVE, identify formation-slot target writer and per-soldier target/turn consumer. Until then: NO HOOK, NO GAME TEST, NO CLAIMED FIX.
