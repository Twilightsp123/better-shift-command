# BSC — Original WH3 Shift formation-coherence research (9.0.3)
Current documentation authority — updated 2026-10-10

> **PRODUCT CAUSE CORRECTION:** [PRODUCT_CAUSE_CORRECTION_20261010.md](PRODUCT_CAUSE_CORRECTION_20261010.md) is mandatory first reading. **Native Shift MOVE does not have a proven full-stop defect.** The user-observed issue is that **soldier models in one unit card turn/arrive asynchronously**, leading to mixed facing and internal crowding. The conspicuous MOVE→ATTACK pause was **our legacy Lua Controller regression**, not an established vanilla bug. Previous "braking-first" assumptions in older N1 reports are superseded as design priorities; their disassembly remains research evidence.

**Current target is WH3 9.0.3.** [WH3_9_0_3_NATIVE_PATCH_DESIGN.md](WH3_9_0_3_NATIVE_PATCH_DESIGN.md) defines version-specific research, candidate patch modules and proof gates. The 9.0.2 EXE hash, maps and N1 reports remain historical evidence only; **9.0.3 labelled EXE queue, task and transfer mechanisms are instruction-backed, but their role in per-model formation crowding is unverified**.

**N1 toolkit implemented:** [read-only 9.0.3 PE and Ghidra field-reference scouts](../../maintenance_tools/native_shift_re/README.md), with synthetic tests. Their own candidate exports do not by themselves prove native progression or install hooks; subsequent exact-file LLVM analysis independently established a ring-pop primitive.

**Read the corrected diagnosis and plan first.** The decided objective is to **patch the game's existing native Shift behavior directly**, keeping its original input, order queue, locomotion and combat engine. We are NOT creating a Lua substitute, separate Native scheduler or second command queue. The NQTR label remains only as a branch/documentation identifier. This is still *research-only* (documentation plus static forensic tooling); no native patch exists or has passed WH3 validation.

## Minimal reading order (do not read archives routinely)
- [PRODUCT_CAUSE_CORRECTION_20261010.md](PRODUCT_CAUSE_CORRECTION_20261010.md) — primary problem diagnosis, Lua regression separation, evidence boundaries.
- [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) — corrected product requirements and formation-level acceptance.
- [WH3_9_0_3_NATIVE_PATCH_DESIGN.md](WH3_9_0_3_NATIVE_PATCH_DESIGN.md) — updated model/formation RE architecture.
- [NATIVE_RESEARCH_MAP.md](NATIVE_RESEARCH_MAP.md) — prioritized missing formation/model-level functions.
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — corrected N1–N6 stages.

### Prior exact-binary research (mechanism evidence; not demonstrated bug cause)
0. [WH3_9_0_3_NATIVE_PATCH_DESIGN.md](WH3_9_0_3_NATIVE_PATCH_DESIGN.md) — **current 9.0.3 design**; lifecycle, braking, ATTACK transition, evidence gates and no-go rules.
1. [N1_903_ORDER_LIFECYCLE_STATIC.md](N1_903_ORDER_LIFECYCLE_STATIC.md) — actual user-supplied 9.0.3-labelled EXE: ring pop and callers.
2. [N1_903_MOVE_STATUS_CHAIN.md](N1_903_MOVE_STATUS_CHAIN.md) — MOVE constructor/VTable and status-to-pop path.
3. [N1_903_SUBTASK_AND_HANDOFF.md](N1_903_SUBTASK_AND_HANDOFF.md) — exact-file proof that +0x240 counts auxiliary tasks and that conditional successor transfer exists; NOT general Shift lookahead.
4. [N1_903_MOVE_VS_ATTACK_TRANSFER.md](N1_903_MOVE_VS_ATTACK_TRANSFER.md) — original state transfer: MOVE successor eligible, ATTACK successor excluded on this path.
5. [N1_903_MOVE_STATE_ORIGIN.md](N1_903_MOVE_STATE_ORIGIN.md) — original MOVE+0xA0 state producer/writeback, native state 4 source and reuse invalidation gate.
6. [N1_903_ORDINARY_ATTACK_DISPATCH.md](N1_903_ORDINARY_ATTACK_DISPATCH.md) — generic native ATTACK head activation is distinct from MOVE's special state inheritance.
7. [N1_903_STATE_MACHINE_REBASE.md](N1_903_STATE_MACHINE_REBASE.md) — explicit 0–4 native state dispatcher, staged MOVE payload rebasing, transfer flag conflict; motor/brake meaning OPEN.
8. [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) — what BSC must do and must never break.
9. [CURRENT_BASELINE.md](CURRENT_BASELINE.md) — exact source/branch and what has actually been verified.
10. [NATIVE_RESEARCH_MAP.md](NATIVE_RESEARCH_MAP.md) — known Native entry points, missing proof, forbidden assumptions.
11. [N1_STATIC_FINDINGS.md](N1_STATIC_FINDINGS.md) — source-verified N1 findings, negative evidence, and exact missing EXE/disassembly inputs.
12. [N1_EXECUTABLE_RE_PLAN.md](N1_EXECUTABLE_RE_PLAN.md) — executable acquisition, xref/dataflow procedure, causal hypotheses and N1 pass/no-go gates.
13. [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md) — the original-engine patch boundary and non-goals.
14. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — reverse the original Shift braking/handoff paths before patching native functions.
15. [VERIFICATION.md](VERIFICATION.md) — offline/Windows/one final WH3 end-to-end verification.
16. [RISKS_AND_DECISIONS.md](RISKS_AND_DECISIONS.md) — unresolved questions and decision register.
17. [MAINTENANCE_RULES.md](MAINTENANCE_RULES.md) — how to update this set without reviving historical designs.

**Latest N1 finding:** [N1_903_TRANSFER_FLAG_WRITER.md](N1_903_TRANSFER_FLAG_WRITER.md) identifies original `state+0x24` writer and branches into state 2/4; no verified braking patch point.\n\n**N1 route-gate update (2026-10-10):** [N1_903_ROUTE_GATE_ANALYSIS.md](N1_903_ROUTE_GATE_ANALYSIS.md) — original 0x0310F560 performs stateful route processing, and 0x0311EB10 flag is jointly gated by AL and native mode. Braking/physical timing remains unknown; patch not approved.

**New state-4 / geometry finding:** [N1_903_STATE4_GEOMETRY_BRANCH.md](N1_903_STATE4_GEOMETRY_BRANCH.md) — distinguishes two genuine native state-4 paths and identifies a gated geometry early exit; no braking function proven.

**N1 further bounded proof (2026-10-10):** [N1_903_STATE4_ROUTE_SETUP_DIFF.md](N1_903_STATE4_ROUTE_SETUP_DIFF.md) shows the state-4 geometric early-exit bypasses guarded route-pointer setup; no proven velocity/desired-speed writer, no Hook.

**N1 formation entry update (2026-10-10):** [N1_903_FORMATION_ENTRY_CALLGRAPH.md](N1_903_FORMATION_ENTRY_CALLGRAPH.md) — exact-file same-unit update sequence: position-bearing member aggregation, group coordinate update, native queued-order processing. Member object type and model turn/arrival are still unverified. [Read-only audit](../../maintenance_tools/native_shift_re/audit_903_formation_entry.py), 23 opcode guards/6 calls, 8 synthetic tests. No patch.

**N1 object-type correction:** [N1_903_MEMBER_LAYER_TYPE_GAP.md](N1_903_MEMBER_LAYER_TYPE_GAP.md) verifies two distinct UnitRoot pointer/count vectors and a further nested child-object array; do **not** equate position aggregation with per-soldier route progress. [SHA-gated verifier](../../maintenance_tools/native_shift_re/audit_903_member_layers.py), 23 exact bytes / 4 calls / 8 independent local tests.

**Direct MOVE→unit route evidence (2026-10-10):** [N1_903_MOVE_TO_UNIT_ROUTE_DIRECT.md](N1_903_MOVE_TO_UNIT_ROUTE_DIRECT.md) proves two MOVE original callsites reach route configurator 0x0301287C and write root+0x270 through original branches. [Read-only verifier](../../maintenance_tools/native_shift_re/audit_903_move_unit_route.py) (23 machine guards + 7 calls). A separate member-related virtual +0xC8 dispatch is documented, but its type/callchain is not yet proven. No Hook.

**Priority root-cause distinction:** [N1_903_SHARED_ORDER_GROUP_ARRIVAL_HYPOTHESIS.md](N1_903_SHARED_ORDER_GROUP_ARRIVAL_HYPOTHESIS.md) — same unit-level Shift order may be promoted at different per-model *arrival decisions*. Test whether models have independent leg-phase state versus sharing group phase but having different physical steering. **Do not presume different Shift commands or wait-for-all.**

**New exact-file N1 result (2026-10-10):** [N1_903_MEMBER_STATUS_AND_SPATIAL_CONSUMER.md](N1_903_MEMBER_STATUS_AND_SPATIAL_CONSUMER.md) — one native original unit-route callback bulk-resets **all** A-member state bits; another native subsystem measures spatial envelopes and compares member pairs. [SHA-pinned verifier](../../maintenance_tools/native_shift_re/audit_903_member_status_spatial.py): 38 original instruction guards, 13 actual E8 calls; 9 local synthetic tests. These two native subsystems have NOT been causally connected to ordinary Shift turn desynchronization; no Hook.

**New original MOVE→member fanout (2026-10-10):** [N1_903_NATIVE_MOVE_MEMBER_FANOUT.md](N1_903_NATIVE_MOVE_MEMBER_FANOUT.md) — direct original MOVE issuer → route update → UnitRoot A-member group → group-generated 0x30-stride records → per-member virtual +0x368. Original instruction guards 38/38 and 9 E8 calls matched, 10 local offline tests. **Member virtual completion/turn code still unknown; NO patch.**

**N1 resolved original member receiver (2026-10-10):** [N1_903_MEMBER_VIRTUAL_RECEIVER_RESOLVED.md](N1_903_MEMBER_VIRTUAL_RECEIVER_RESOLVED.md) traces +0x368 into shared native handler `0x0306B9F0`, then +0xE8/+0x100 member methods and actual per-member coordinate/orientation writes. **38 real VTables identified with constructor references, 16 original byte guards, 7 local exact-EXE/offline tests.** [Pinned proof script](../../maintenance_tools/native_shift_re/audit_903_member_virtual_receivers.py). Arrival phase still unknown; no Hook.

**N1 causal audit correction — stronger negative evidence:** [N1_903_LAYOUT_COUNT_NOT_ARRIVAL_DISCONFIRMATION.md](N1_903_LAYOUT_COUNT_NOT_ARRIVAL_DISCONFIRMATION.md) identifies group strategy `+0x20` as formation-size/layout-number computation (sqrt(n), min(13,n), table) cached at task+0xB8, **NOT waypoint-completion status**. Separate group object `+0x20` is a different function. One group target generation precedes batch dispatch; per-member receiver branches by `member+0x104`. Exact-SHA proof [script](../../maintenance_tools/native_shift_re/audit_903_layout_vs_arrival.py). No safe repair site established.

**Positive member-direction result (2026-10-10):** [N1_903_PER_MEMBER_DIFFERENT_HEADING_PROOF.md](N1_903_PER_MEMBER_DIFFERENT_HEADING_PROOF.md) traces ONE original MOVE through a selectable grid formation strategy to **different per-member 16-bit facing codes**, each carried into original native member +0xB0. Real 3×3 corner slots can differ by 0x8000 cyclic code. The result proves assigned orientations can differ, not actual velocity/crowding or a safe patch. Downloadable exact-SHA forensic bundle: 42 machine guards / 6 calls / 8 tests.

**New causally relevant strategy source:** [N1_903_FORMATION_MODE_AND_MODEL_MOTION_RULES.md](N1_903_FORMATION_MODE_AND_MODEL_MOTION_RULES.md) traces exact original MOVE's **`[[UnitRoot+0x3D48]+0x248]`** formation selector into `0x030C7D18` mode 0..12 strategy dispatch, then actual per-member target/facing generation. Mode 3's divergent heading result is conditional on a unit *using that strategy*; next distinguish pose from velocity and group phase from local trajectory. Read-only 22 exact opcode guards, 5 direct calls, 8 local tests. No Native patch.

**Native model displacement-rate evidence (2026-10-10):** [N1_903_MEMBER_POSE_DISPLACEMENT_DERIVATIVE.md](N1_903_MEMBER_POSE_DISPLACEMENT_DERIVATIVE.md) — exact original member pose updater `0x0315C1E4` computes XYZ displacement rates at `member+0xE0/+0xE4/+0xE8` and angular rate `+0xEC`; member tick `0x03060700` supplies target from its own controller `+0x2E0`, then advances local controller after updating member pose. Native mode3 record helper `0x030BE544` only appends 48-byte records, not avoidance. **52 exact opcode guards, 5 E8 calls, 18 offline tests** verified; actual WH3 collision/patch still unknown.

**N1 native slot binding evidence (2026-10-10):** [N1_903_GROUP_INDEX_TO_SLOT_COLLISION_CAUSAL.md](N1_903_GROUP_INDEX_TO_SLOT_COLLISION_CAUSAL.md) — original group members appended in source order, mode3 target records appended in 48-byte order, grid indices mapped back to records without vector permutation, then native fanout pairs `member[i]` with `record[i]`. Conditional 3×3/180° straight-travel counterexample converges all members at midpoint; offline bijective slot-matching candidate preserves target set but is **not** proven safe in WH3. 44 machine guards, 8 calls, 22 tests. No DLL.

**2026-10-10 direct positive AND negative slot-index evidence:** [N1_903_SLOT_IDENTITY_POSITIVE_AND_NEGATIVE.md](N1_903_SLOT_IDENTITY_POSITIVE_AND_NEGATIVE.md) confirms original group fanout pairs member[i] with generated target[i], while native old-group removal *can* reindex a member through swap-last (mode3) or strategy-specific replacement (+0x60/+0x70); source-root stable ordering could still make new groups stable. After fanout there is native group geometry/status processing, so actual collision is unproven. Exact-SHA 45 machine guards + 9 calls + 8 vtables + 15 offline tests in chat evidence archive; no Hook.

**Slot identity / CA avoidance cross-check (2026-10-10):** [N1_903_MODE_AND_DIRECTIONAL_AVOIDANCE_CROSSCHECK.md](N1_903_MODE_AND_DIRECTIONAL_AVOIDANCE_CROSSCHECK.md) — old-group swap-last is removal maintenance, not normal corner-turn slot optimization; MOVE gets *dynamic* unit formation mode; mode3/mode5 target generator paths do not show a global minimum-travel matcher, mode0 delegates to further strategy virtuals; separate native actor-interaction code computes relative-position·displacement-rate sign, but normal Shift reachability is NOT proven. Full offline SHA-gated audit: 45 opcode guards, nine E8 edges, three strategy VTables, 12 local tests. **No gameplay fix**.

**Binding proof standard (real WH3, 2026-10-10):** [N1_903_PROGRESSIVE_SHIFT_TURN_REAL_BASELINE.md](N1_903_PROGRESSIVE_SHIFT_TURN_REAL_BASELINE.md) accepts within-card crowding under CA's *progressive* Shift turn as a CONFIRMED user-observed defect. V3 real unit route sweeps ~179° from 35–43s while 29/40 member-sample frames show spacing<1.0. NO requirement to make normal RMB follow the same geometric path or to prove the defect's existence again; focus on actual executed MOVE→member target/steering causal site and later SAME-Shift before/after efficacy. No current gameplay fix.

**V3-active MOVE task followed (2026-10-10):** [N1_903_ACTUAL_MOVE_TASK_MEMBER_TIMING.md](N1_903_ACTUAL_MOVE_TASK_MEMBER_TIMING.md) — active `0x03025D70` constructs task whose `+0x10` executes `0x02F561E8`, conditional once-only native group member broadcast `0x030D52B4` invokes member `+0x360` (38/38 tables → `0x0306B878`). Gated per-member state event `0x02F5F5AC` uses 0–2 native-tick randomized deadline at original scalar100, and later dispatches `0x81` status via member `+0x528`; **not proven actual route/velocity correction**. Local pinned EXE verifier: 21 guards/4 calls/38 tables/8 tests, no patch.

## Source-of-truth order
1. Frozen working code and exact build artifacts, with their hashes.
2. Current NQTR documents in this directory; label speculation as proposal.
3. Explicit test results with reproducible executable fixtures.
4. docs/past_doc only when a specific question needs historical evidence.
5. archive/ is historical and must never silently set current behavior.

**Do not use** the former README_FIRST/2026-09 maintainer reading list, D1/T1H design, 9.0.1 CURRENT_BUILD_MAP, or H1–H8 experiment writeups as a current implementation plan. They are retained in docs/past_doc, or pre-existing archive, for targeted forensic lookup only.

## Important status
- N1 source/map triage is recorded in N1_STATIC_FINDINGS.md for historical 9.0.2 evidence. The user-supplied 9.0.3-labelled binary's queue pop and some state handoff mechanisms have instruction evidence. **The soldier-level formation divergence responsible for crowding remains unidentified; earlier braking pursuit is de-prioritized.** No patch authorized.
- Formal mod version and Steam pack identity are release policy, not a proof of installed experimental controller revision.
- Current development starting point: H8 branch maintenance/t2move-h8-terminal-liveness-static, commit e711e716f2411599d75184618fc1ee5cb85bcd54.
- 9.0.2 experiment uses a separately overlaid static candidate map, NOT promoted native_maps/CURRENT.
- N1 offline tooling includes a PE SHA/section guard scout, Ghidra scalar-offset candidate exporter and synthetic regressions; Ghidra integration remains **unperformed**, but the actual user-supplied EXE has undergone read-only LLVM disassembly/callgraph analysis.
- Direct Native Shift patch is NOT implemented, validated or authorized for release. The original Native Bridge may be reused only as an instrumentation/patch vehicle, not as an alternative executor.
- Research branch may contain read-only scripts/tests and docs, but no gameplay/native runtime modifications; no player-facing behavior change.

**V3 active-cohesion tool update (2026-10-10):** [N1_903_ACTIVE_COHESION_LINK_AUDIT.md](N1_903_ACTIVE_COHESION_LINK_AUDIT.md) — new exact-SHA read-only bounded x64 call inspector across real MOVE work, mode0 target delegation, member pose and native group distance readiness. Nine prior direct-call anchors are rechecked on an available original EXE; 8 synthetic tests and linked GitHub CI pass. The original EXE and V3 raw logs were not available in this handoff turn, so **no new exact-game readout, patch, DLL or WH3 result**. Do not infer absent indirect links from E8 output.

**2026-10-10 active task→member bridge:** [N1_903_REAL_MOVE_CONDITIONAL_MEMBER_BRIDGE_20261010.md](N1_903_REAL_MOVE_CONDITIONAL_MEMBER_BRIDGE_20261010.md) — exact original EXE conditionally connects V3-hit native MOVE+task to previously zero-hit group member fanout, 36 native member vtables and common member pose target handler. Full exact-SHA verifier and offline CI tests landed in `maintenance_tools/native_shift_re/audit_903_real_move_conditional_fanout.py`. Runtime branch taken and locomotion cause still OPEN; no DLL, PACK or gameplay fix authorized.

**2026-10-10 actual native C++ experimental patch (NOT GAME FIX):** [RMB-style fresh continuation prototype](../../src/native_bridge/experiments/fresh_continuation/README.md) provides exact-EXE-guarded opt-in WinX64 DLL source. At native queued MOVE→MOVE handoff RVA `0x0304459D`, the reversible `E9 0C000000` skips shared-state inheritance and leaves the original queue pop / MOVE execution intact. Includes original-instruction x64 execution/rollback fixture and Windows private-process hash refusal test. This may alter CA progressive turns and has **no gameplay success proof**; default OFF, no Steam release.

**2026-10-10 original RMB reference audit:** [N1_903_RMB_REFERENCE_MEMBER_TARGET_CONTINUITY_20261010.md](N1_903_RMB_REFERENCE_MEMBER_TARGET_CONTINUITY_20261010.md) — exact original EXE confirms shared target generator, native cross-segment spacing carry and valid segment-reference transforms; synthetic 36-target U-turn exposes close-opposing candidates without duplicate goals. Downstream spatial fallback resolves geometry/plane projection, NOT a proven soldier-soldier avoidance solver. Read-only SHA-pinned verifier + 15 tests in `maintenance_tools/native_shift_re/rmb_shift_target_continuity.py`; no gameplay patch or extra user test.

**2026-10-10 RMB/Shift actor motion and contact lifecycle split:** [N1_903_RMB_SHIFT_MEMBER_MOTION_CONTACT_SPLIT_20261010.md](N1_903_RMB_SHIFT_MEMBER_MOTION_CONTACT_SPLIT_20261010.md) — original actor+0x18 update type census (38 vtables), child pose-rate calculation and `0x03081EB4 → 0x0308489C → 0x030C6788` contact-bitset producer, `0x030E0AA8 → 0x030D3D7C` counter rollover/clear consumer. New exact-SHA verifier & CI tests. These are NOT proven same-unit steering avoidance or a safe native fix; no gameplay test requested.
