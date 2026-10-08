# T2-MOVE-B — mode-specific one-poll adopt-only shadow

**Status:** PURE OFFLINE SHADOW / NOT A GAMEPLAY PATCH.
**Baseline:** \`maintenance/t2move-a-shadow\` (A validated, Native MOVE adoption still closed).
**Current validation target:** 28 pure Lua fixtures, 20 independent mutations, unchanged controller blobs and existing full maintenance suite.

## Root cause

Current \`TransitionPolicy\` unconditionally closes the MOVE adopt envelope. SC6 can identify exact Native \`i+1 MOVE\` but therefore rolls back even when the transition corresponds to the next canonical waypoint. That is a policy asymmetry, not a Native-address problem.

## Stage B envelope: timing only, never route

The proposed ADOPT_ONLY window is not \`corner_window + distance\`. That would permit early folding on turns/hairpins.

A Stage-A cache is captured only while Native still executes exact CURRENT MOVE. It binds generation, unit lifetime, current/action IDs, canonical indices, the original shared Move->Move decision, and scalar geometry. Exact Native \`i+1 MOVE\` may consume that cache only within one **actual observed poll**. Anything at \`i+2\`, another lifetime, another action, or with stale timestamps fails closed.

For Stage B only, require:

- The captured shared evaluator returned \`route_ok=true\` but \`issue_window.open=false\`. If the issue window was already open, return Stage A's existing issue-proof preview unchanged.
- Route mode is \`PATH_SAFE\` or \`STEERING_CORNER\` (including SC4 stall-escape evidence).
- \`PATH_SAFE\` retains its original \`cut_error <= cut_safe_limit\`, strict minimum progress, adjacent-leg cap, and existing route reason.
- \`STEERING_CORNER\` retains the existing composed \`corner_window = max(base, early)\`, current remaining already **inside** that unexpanded corridor, minimum progress, and the both-adjacent-leg cap. SC4 requires its original stall-escape certificate.
- An unresolved earlier SC3 route debt is accepted only with the already-proven \`SOFT_PRESERVED\` corridor, debt count and error/limit; it is never forgiven.
- The previous and current **pre-promotion** position observations must match the cached sample timestamp and poll interval. The radial approach distance must be positive, bounded by actual ground travel, and agree with the frozen G1 observed one-poll distance (allowing only IEEE-754 arithmetic roundoff).

The existing proactive temporal frontier is reconstructed from **unchanged** legacy issue scalars:
\`\`\`
temporal_frontier = max(CFG.proximity, g.threshold)
if g.stall:
    temporal_frontier = max(temporal_frontier, CFG.stall_distance,
        min(CFG.lead_cap, g.threshold + CFG.brake_extra))
\`\`\`

If shared \`issue_window\` was closed but current remaining was already within that frontier, treat it as a contradictory proof and fail closed.

The shadow ADOPT_ONLY preview opens only when:
\`\`\`
temporal_frontier < cached_remaining
    <= temporal_frontier + min(measured_radial_travel, G1_one_poll_margin)
\`\`\`
There is **no change** to the proactive issue window, route corridor, short-leg cap or debt corridor. The one-poll band is an asynchronous time uncertainty only; the route must already have been legal at the exact-current pre-promotion observation.

## Credit semantics and future integration

- \`STEERING_CORNER\` => existing \`STEERING_CORNER_HANDOFF\` completion credit.
- \`PATH_SAFE\` => register current waypoint route obligation through existing T1.6 commit logic.
- SC3 earlier debt remains independently tracked and must not be paid by this credit.
- All shadow results have \`authoritative=false\`. They cannot send Native commands, advance the canonical index, or mutate transactions.

**No controller integration in Stage B.** A future joint T2-MOVE A+B+C controller candidate must consume the shared evaluator for both proactive/Native, use \`OBSERVED -> Core.commit_transition_edge()\` for exact Native promotion, preserve recovery budgets, and prove that no repeated Native advance -> rollback -> reassert oscillation remains. \`i+2\` remains hard rollback. The WH3 gate comes only after offline integration and is not currently available.

## Known conservative limitation

If the prior exact-current observation had not yet entered a legal SC1/SC2/SC3 route corridor, Stage B returns WAIT even if a one-poll extrapolation suggests CA might enter it later. This can leave some legitimate Native promotions unadopted; it is a deliberate false-negative until WH3 evidence justifies a *mode-specific route* proof. The algorithm must not trade waypoint fidelity for higher adoption counts.

## Freeze and gates

- Existing \`maintenance/t2b-terminal-attack\`: unchanged; T2-B RT-TP-02/03 remains **BLOCKED/DEFERRED**, not WH3-PASS.
- \`maintenance/t2move-a-shadow\`: independent research lane; source/src/template controller blobs remain unchanged.
- Stage A shadow: 20/20 Lua fixtures and 12/12 mutations.
- Stage B shadow: 28/28 Lua fixtures and 20/20 mutations (offline, subject to repository CI).
- T2-MOVE gameplay permission: **INACTIVE**. Native MOVE adopt hard-close remains present.
- Native/address, MCT and lifecycle: untouched.
