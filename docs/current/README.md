# BSC — Direct WH3 Native Shift Patch (NQTR documentation branch)
Current documentation authority — 2026-10-09

**Current target is WH3 9.0.3.** [WH3_9_0_3_NATIVE_PATCH_DESIGN.md](WH3_9_0_3_NATIVE_PATCH_DESIGN.md) defines version-specific research, candidate patch modules and proof gates. The 9.0.2 EXE hash, maps and N1 reports remain historical evidence only; **9.0.3-labelled EXE queue pop, MOVE task-status, state-object writeback and conditional successor transfer are instruction-backed; braking and general Shift behavior remain unknown**.

**N1 toolkit implemented:** [read-only 9.0.3 PE and Ghidra field-reference scouts](../../maintenance_tools/native_shift_re/README.md), with synthetic tests. Their own candidate exports do not by themselves prove native progression or install hooks; subsequent exact-file LLVM analysis independently established a ring-pop primitive.

**Read this folder first.** The decided objective is to **patch the game's existing native Shift behavior directly**, keeping its original input, order queue, locomotion and combat engine. We are NOT creating a Lua substitute, separate Native scheduler or second command queue. The NQTR label remains only as a branch/documentation identifier. This is still *research-only* (documentation plus static forensic tooling); no native patch exists or has passed WH3 validation.

## Minimal reading order (do not read archives routinely)
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

## Source-of-truth order
1. Frozen working code and exact build artifacts, with their hashes.
2. Current NQTR documents in this directory; label speculation as proposal.
3. Explicit test results with reproducible executable fixtures.
4. docs/past_doc only when a specific question needs historical evidence.
5. archive/ is historical and must never silently set current behavior.

**Do not use** the former README_FIRST/2026-09 maintainer reading list, D1/T1H design, 9.0.1 CURRENT_BUILD_MAP, or H1–H8 experiment writeups as a current implementation plan. They are retained in docs/past_doc, or pre-existing archive, for targeted forensic lookup only.

## Important status
- N1 source/map triage is recorded in N1_STATIC_FINDINGS.md for **historical 9.0.2** evidence. The user-supplied 9.0.3-labelled binary SHA and **original head/count pop writer** have now been statically identified in [N1_903_ORDER_LIFECYCLE_STATIC.md](N1_903_ORDER_LIFECYCLE_STATIC.md); original MOVE-completion/braking/next-activation semantics remain unverified. No patch authorized.
- Formal mod version and Steam pack identity are release policy, not a proof of installed experimental controller revision.
- Current development starting point: H8 branch maintenance/t2move-h8-terminal-liveness-static, commit e711e716f2411599d75184618fc1ee5cb85bcd54.
- 9.0.2 experiment uses a separately overlaid static candidate map, NOT promoted native_maps/CURRENT.
- N1 offline tooling includes a PE SHA/section guard scout, Ghidra scalar-offset candidate exporter and synthetic regressions; Ghidra integration remains **unperformed**, but the actual user-supplied EXE has undergone read-only LLVM disassembly/callgraph analysis.
- Direct Native Shift patch is NOT implemented, validated or authorized for release. The original Native Bridge may be reused only as an instrumentation/patch vehicle, not as an alternative executor.
- Research branch may contain read-only scripts/tests and docs, but no gameplay/native runtime modifications; no player-facing behavior change.
