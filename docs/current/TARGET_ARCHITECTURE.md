# Proposed Target Architecture — single transition authority

**Status: proposal, not an implemented or verified Native behavior.** Do not claim that current hooks can change WH3 native queue advancement.

## Desired execution pipeline
Player Shift/normal command → WH3 native input capture + exact identity → WH3 native queue → **Native BSC transition decision at verified engine completion/advance boundary** → WH3 native locomotion/attack executor.

Lua role: settings, diagnostics, user-facing state, optional high-level route policy, NOT a second writer that predicts and overwrites the game's active queue. Native transition layer role: decide whether/when a *canonical next command* becomes current, preserve atomic identity and cancellation invariants; do not implement physical steering or fake arrival.

## Ownership contract (proposed)
- One authoritative order queue, identified by engine sequence and verified unit lifetime.
- Player REPLACE owns the generation boundary and cancels stale planned transitions, including already-scheduled BSC callbacks.
- BSC may only influence the exact next queue edge, not manufacture independent permanent orders without a bounded transaction.
- A change to a queue head must have a commit/abort model with observed before/after head identity and native outcome.
- If the hook cannot safely express a request, pass through unmodified original behavior rather than attempt Lua rollbacks of unproven Native queued tails.
- No handler may silently consume an external attack, no double-advance and no reordering across independent units.

## Behavior policies
- MOVE→MOVE: permit **bounded early steering** for approximate guidepoints; preserve a physical-route obligation or prove that a rounded segment is acceptable. U-turn, zig-zag and short-leg cases must have deterministic geometry, not fixed arbitrarily tuned timeouts.
- MOVE→ATTACK: accept completion or native execution transition based on exact edge/target plus valid terminal evidence. G11 coherent braking remains one signal, not a globally mandatory predicate.
- ATTACK→EXIT MOVE: require existing positive engagement / minimum engagement time and explicit exit-route semantics. Next ATTACK only after valid exit transition. No inferred attack from a near target alone.
- Native i+2 promotion: never infer that i+1 is paid just because i+2 appears as active.
- Long-running/missing proof: model must be explicit (wait, fall back native, cancel/recover, or diagnosed hard-fail); cannot wait forever and cannot roll back indefinitely.

## Architecture choices that are NOT yet resolved
A. Engine completion/advance hook (preferred if proved): modify transition timing at source while CA still owns queue.
B. Ingress queue policy rewriting (backup): requires proof that serialized/queued command semantics remain valid.
C. Dual Lua/Native queues (current architecture): to be retired from command authority, NOT promoted as default.
D. Replace engine pathfinding: excluded.

Gate to select A vs B: actual 9.0.2 dataflow proof and deterministic 'same queue in / changed transition only' fixture; do not choose solely from attractive diagrams.
