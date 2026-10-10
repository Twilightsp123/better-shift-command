# BSC — corrected verification and evidence gates

**First read [PRODUCT_CAUSE_CORRECTION_20261010.md](PRODUCT_CAUSE_CORRECTION_20261010.md).** The vanilla Shift MOVE issue is **asynchronous individual soldiers within a unit arriving/turning into one another**; native full-stop at intermediate waypoints is **not** an established defect. MOVE→ATTACK pausing was a legacy **Lua Controller** regression.

## Evidence tiers

- **STATIC:** exact-file disassembly, original function/dataflow, group/formation slot and per-soldier pointer provenance, ownership/ABI. Native ring pop or route-processing instructions alone do not establish model-level behavior.
- **OFFLINE:** only evidence-derived differential tests of a localized original engine predicate; synthetic model tests cannot prove actual soldier formation quality.
- **WINDOWS:** exact-hash guarded runtime patch installation, ABI, call-through, fault cleanup and disable/quit safety; never silently retry forever.
- **WH3:** one consolidated final in-game test. Required to assert that *soldier models* turn together better, avoid intra-unit crowding, or that Lua regression is absent.

## Static and offline regression matrix

1. **Formation allocation:** trace one unit MOVE command through original formation target/pivot/slot assignment to individual soldier destination and turn/arrival logic. Ensure same-card soldier identity and model lifetime.
2. **Model phase coherence:** same unit's leading vs trailing soldiers on straight, 90°,135°,180° turns, dense short zigzags; verify native branch invariants for early turn/target promotion vs mixed model phases.
3. **Blocked/late model cases:** path obstruction, variable model speed, collision/avoidance, incomplete formation, terrain and casualties; localized patch must not deadlock whole unit waiting for an absent model or ignore route bends.
4. **Formation semantics:** maintain unit facing, relative slot assignment, steering/turn ability, collision behavior and recovery, without implementing our own physics solver.
5. **Queue invariants:** original head/count, sequence/identity, i+1/i+2, future tail, CANCEL/REPLACE/HALT and non-queued RMB remain engine owned; do not inject extra MOVE/ATTACK.
6. **Lua attack regression isolation:** with old BSC control reissue/rollback disabled in new mode, original MOVE→ATTACK activation/target identity cannot be overwritten by BSC. Separate original-engine ATTACK Hook needs independently evidenced native defect.
7. **Optional ATTACK→EXIT→ATTACK:** if implemented by proven native semantics, check engagement minimum, exit route, target viability and cancellation; otherwise mark DEFERRED rather than spoofing commands.
8. **Lifecycle/Win64:** thread ownership, reference counting, entity lifetime, model/formation restructuring, MinHook allocator failures, partial installation and quit; do not automatically require legacy 16-hook host.
9. **Fail closed:** unsupported EXE, missing ABI, invalid formation state or disabled patch preserves original WH3 behavior; no half-patched engine.
10. **Historical counterexamples:** H8 12:53 rollback and prior Lua route debt remain regressions to prevent in *new BSC*, not evidence of native model-level crowding mechanics.

## Final WH3 physical acceptance (only once after prior gates)

Observe and record soldier-level relative position, headings, assigned slot deviation and crowding in one card before/at/after queued guidepoint turns. Distinguish mixed soldier headings from legitimate temporary differential turning caused by obstacle avoidance. Aggregate unit velocity alone is insufficient. Test no extra pause/reissued commands in MOVE→ATTACK with legacy Lua Controller absent, then REPLACE and unit combat/cancel. Report STATIC/OFFLINE/WINDOWS/WH3 status separately, plus source, DLL/PACK and SHA manifest only after they actually exist.

**Current status:** N1 model/formation execution path unknown; no patch-ready exact RVA/ABI, no Windows or WH3 behavior pass. No repeated user gameplay testing during research, no premature Steam publication.
