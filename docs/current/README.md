# BSC — Direct WH3 Native Shift Patch (NQTR documentation branch)
Current documentation authority — 2026-10-09

**Read this folder first.** The decided objective is to **patch the game's existing native Shift behavior directly**, keeping its original input, order queue, locomotion and combat engine. We are NOT creating a Lua substitute, separate Native scheduler or second command queue. The NQTR label remains only as a branch/documentation identifier. This is still documentation-only; no native patch exists or has passed WH3 validation.

## Minimal reading order (do not read archives routinely)
1. [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) — what BSC must do and must never break.
2. [CURRENT_BASELINE.md](CURRENT_BASELINE.md) — exact source/branch and what has actually been verified.
3. [NATIVE_RESEARCH_MAP.md](NATIVE_RESEARCH_MAP.md) — known Native entry points, missing proof, forbidden assumptions.
4. [N1_STATIC_FINDINGS.md](N1_STATIC_FINDINGS.md) — source-verified N1 findings, negative evidence, and exact missing EXE/disassembly inputs.
5. [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md) — the original-engine patch boundary and non-goals.
6. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — reverse the original Shift braking/handoff paths before patching native functions.
7. [VERIFICATION.md](VERIFICATION.md) — offline/Windows/one final WH3 end-to-end verification.
8. [RISKS_AND_DECISIONS.md](RISKS_AND_DECISIONS.md) — unresolved questions and decision register.
9. [MAINTENANCE_RULES.md](MAINTENANCE_RULES.md) — how to update this set without reviving historical designs.

## Source-of-truth order
1. Frozen working code and exact build artifacts, with their hashes.
2. Current NQTR documents in this directory; label speculation as proposal.
3. Explicit test results with reproducible executable fixtures.
4. docs/past_doc only when a specific question needs historical evidence.
5. archive/ is historical and must never silently set current behavior.

**Do not use** the former README_FIRST/2026-09 maintainer reading list, D1/T1H design, 9.0.1 CURRENT_BUILD_MAP, or H1–H8 experiment writeups as a current implementation plan. They are retained in docs/past_doc, or pre-existing archive, for targeted forensic lookup only.

## Important status
- N1 source/map triage is recorded in N1_STATIC_FINDINGS.md. The WH3 9.0.2 native completion/braking/queue-head writer has **not** been located; matching executable disassembly is still required. No patch authorized.
- Formal mod version and Steam pack identity are release policy, not a proof of installed experimental controller revision.
- Current development starting point: H8 branch maintenance/t2move-h8-terminal-liveness-static, commit e711e716f2411599d75184618fc1ee5cb85bcd54.
- 9.0.2 experiment uses a separately overlaid static candidate map, NOT promoted native_maps/CURRENT.
- Direct Native Shift patch is NOT implemented, validated or authorized for release. The original Native Bridge may be reused only as an instrumentation/patch vehicle, not as an alternative executor.
- This branch must contain docs/metadata only; no player-facing behavior change.
