# NQTR Implementation Plan — Native Shift Queue Transition Rewrite

**Plan only. Runtime construction not started.** Base H8 commit e711e716f2411599d75184618fc1ee5cb85bcd54. Keep game DLL/addresses/Steam untouched until the relevant gate is satisfied. All phases are separate commits/PRs with explicit exit evidence, not time-based tuning campaigns.

## Stage 0 — Freeze baseline / architecture contract (NOW)
**Work:** segregate superseded documentation, publish a single current authority, preserve H4–H8 tests/manifest and exact 9.0.2 address provenance; identify 12:10/12:53/13:18 regression facts. Distinguish planned Lua tail from actual engine queue tail.
**Exit:** current docs and docs/past_doc inventory complete, historical docs retained byte-identically, legacy contract adapted, reference-check CI green, no code or binary changed.
**Fallback:** if moving docs breaks a historical test, update only the explicit legacy-document lookup or packaging manifest; do not restore historic advice as current architecture.

## Stage 1 — Reverse the native queue advance decision (HIGHEST PRIORITY)
**Work:** follow Move/Attack native order paths, existing 16 hook source, queue read-only offsets and VTables; map completion predicate, OrderHead mutation, destructor/retire, next-order activation and execution timing; separate queued ingress from execution. Produce annotated callgraph, RVA/guard candidates, ABI, lifetime/thread model and alternative interpretations.
**Exit gate:** at least one independently checkable completion/advancement graph with exact 9.0.2 provenance; if no trustworthy single point exists, document this and compare ingress alternative B without pretending the target has been found.
**No-go:** no address guesses, no direct changes to root+0x2F8C, no live Hook patch on unproven site.

## Stage 2 — Formal single-authority model (P2 root fix)
**Work:** model an actual Native queue as the **sole** authoritative command order, with engine sequence/lifetime/revision and atomic head changes. Define source of truth when native i+1/i+2 runs before a Lua poll; define duplicate, cancellation, REPLACE, failed Native issue and what falls back to original engine behavior. Eliminate any need to restore a 'lost' native tail using nonqueued MOVE.
**Exit gate:** deterministic C++/Lua model tests show no double-writer, no skip i+1, no resurrection of cancelled generations, and Native queued tail is validated before/after transitions. Include model checker / exhaustive short traces for all two-/three-order permutations with injected errors.
**No-go:** never claim tail preservation based solely on the Lua array.

## Stage 3 — Design transition policies on the proven native boundary
**Work:** MOVE→MOVE smooth early steering and route-obligation geometry (including 90/135/180, 5m, U-turn and dense zigzag); MOVE→ATTACK terminal and native handoff without exclusive dependence on G11 deceleration; ATTACK→EXIT→ATTACK, 3s hold, target loss and cancellable commands. Reuse engine movement, physics and combat.
**Exit gate:** common native decision interface accepts exact i→i+1 identity and observable geometry, returns ALLOW / WAIT / FALLBACK / CANCEL with reason. Obligations are tracked without inventing physical waypoint arrival. Model tests prove liveness without arbitrary timeouts.
**No-go:** not a full pathfinding reimplementation or an unchecked native deque mutation.

## Stage 4 — Implement Native transition owner in an isolated integration branch
**Precondition:** Stages 1–3 passed. Hook point and ABI are proven at sufficient static level.
**Work:** use reversible, byte-guarded, thread-safe Native interception only at validated queue boundary. Retain Lua for MCT, diagnostics and non-authoritative observations; turn off competing Lua proactive/reassert writers within NQTR mode. Native commands retain real CA journal identity; transactions commit only once on native evidence.
**Exit gate:** synthetic Host/Native boundary tests cover target loss, queue overrun, mixed units, reorder prevention, literal head identity and pass-through under untrusted proof. Code review proves no hook/queue lifetime leaks, safe fallback and behavior unchanged when NQTR disabled.
**No-go:** never accept arbitrary future > i+1; no 'prevent all native queueing then emulate it in Lua' shortcut without a safe atomic plan.

## Stage 5 — P0 Native hook installer reliability / Windows isolation
**Work:** separately instrument byte-locked MinHook backend in an isolated Win64 test process; distinguish status9 allocation subcauses, nearest-executable-page pressure, failed first-hook retry and teardown. Inject failures at all 16 mandatory hooks and partial apply. Decide if a safe 'rollback to fully unhooked' retry is possible.
**Exit gate:** v142/MASM build; Native CTest baseline; proof of no partial hooks, no freed trampolines in flight, deterministic fail-closed errors. New Hook addresses not promoted until executable hash/bytes match.
**No-go:** never treat a 50ms Sleep or infinite retry as correctness.

## Stage 6 — Integrated offline acceptance & final WH3 gate
**Work:** CI runs existing regression and mutation suite plus NQTR queue/geometry and Native fault injection. Build reproducible normal and DEBUG PACK with full source archive, candidate EXE map, manifest hashes and known open limitations. Then perform ONE bounded final WH3 acceptance round covering startup, Shift MOVE/ATTACK/EXIT, normal RMB, multi-unit, Quit-to-Windows.
**Exit gate:** STATIC/MODEL/WINDOWS complete and WH3 outcomes separately verified; only then consider an explicit merge/release recommendation. If WH3 fails, reproduce the specific evidence as a *new deterministic fixture*, not a series of unguided user trials.
**No-go:** green CI by itself cannot authorize Steam publication.

## Critical path / dependencies
Stage 0 → Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 6.
Stage 5 can begin in parallel with Stage 1 but **must close before any in-process WH3 validation**. If no safe Native advancement interception can be proven, stop and document a decision between alternative ingress-level rewrite and abandoning direct engine queue changes rather than shipping a speculative Hook.

## Explicitly postponed work
User-visible MCT UI, historical D1 profile tuning, generic CA pathfinding rewrite, quarantined physical Entity research, arbitrary gameplay parameter search and Steam marketing are outside the NQTR core.
