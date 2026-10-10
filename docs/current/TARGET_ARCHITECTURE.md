# BSC Target Architecture — original formation-aware Shift MOVE patch

**Product truth:** [PRODUCT_CAUSE_CORRECTION_20261010.md](PRODUCT_CAUSE_CORRECTION_20261010.md). A native Shift MOVE issue is *individual models in one unit becoming out of sync through queued waypoint turns and crowding*, **not** a proven native full-stop between MOVE orders. The MOVE→ATTACK stop belongs to the old Lua Controller regression unless independently reproduced in unmodified WH3.

## Original engine remains authoritative

WH3 retains the original Shift/RMB input, unit-level queued order objects, command identity, append/REPLACE and HALT, group/formation slot assignments, per-model locomotion and arrival, collision/avoidance, combat and animations. Native detours are only a means of changing a *verified narrow native decision within WH3's original execution path*.

BSC must not own a Lua shadow route, C++ order executor, ACK/reissue loop, early queue-head mutation, separate formation simulator, or repeated replacement MOVE/ATTACK calls. Optional Lua can expose settings/diagnostics only.

## Actual N1 layers to correlate

**L0 — unit command context:** Where a unit-level original queued MOVE destination/next route leg is represented. Relevant known 9.0.3 issuer/queue evidence exists, but this is *context*, not a fix for soldiers crowding.

**L1 — formation route mapping:** How the unit's current/next order becomes a formation origin, heading, slots and per-soldier movement target. Find actual producer and consumer fields in exact EXE, not stale offsets.

**L2 — individual soldier movement:** How each soldier decides it has approached/reached its assigned point, turns, starts following the next leg, and responds to blocked or slower neighbors. Compare identity and timestamps at *soldier* level rather than only UnitRoot/order head.

**L3 — synchronization policy:** Find existing native formation coherence/coordination, if any, and verify whether early individual arrival/promotion can be altered with minimal local conditions. Avoid all-or-none group fences that stall behind a permanently blocked soldier. Preserve valid path navigation, collision and realistic U-turn slowing.

**L4 — combat regression isolation:** Old BSC Lua caused MOVE→ATTACK pause/rollback. Retiring that competing authority is the direct architectural fix; do not patch original ATTACK unless another native defect is established. Existing original generic ATTACK activation path remains authoritative.

## Candidate design possibilities (hypotheses, not approved Hooks)

A. Existing formation waypoint phase/slot target handoff already has a group-level policy, but an original predicate permits early soldier turn/divergence. A scoped change to *that* decision is preferred.

B. Native unit/group promotes the route and updates slot targets at unsuitable times, creating model heading spread; a scoped formation destination/transition fix may work without rewriting solver or individual movement.

C. Crowding originates in native soldier avoidance/pathfinding that cannot be improved without a major rewrite. If no safe small change, **NO-GO** for simple Native Shift Patch; do not paper over it with Lua resends.

The prior investigation into original MOVE state0–4, task counts, special MOVE state transfer, and the geometry early exit is **still valid partial machine-code research** for the exact binary. It is not a demonstrated link to intra-unit soldier misalignment, cannot be called the root cause, and must not be used to justify a braking-distance fix.

## Safety gates and acceptance

- Version-guard and byte-guard actual 9.0.3 binary; register ABI, threading and object life proven independently for each targeted site.
- Model-level relative headings, spacing, slot alignment, route-bend fidelity and formation recovery are primary outcomes. Unit centroid speed alone is not acceptance.
- Preserve ordinary RMB commands, CANCEL/REPLACE, native order sequence, i+1/i+2, target and animation lifetimes, multiple unit selection.
- One bundled final WH3 check only after static+offline+Windows gates; no false PASS from synthetic geometry.
- If original engine lacks a safe formation-level transition lever, report limitation and stop before constructing an alternative command executor.

**Development status:** research only. No verified per-model cause or safe behavior patch; no DLL/PACK or Steam release from this branch.
