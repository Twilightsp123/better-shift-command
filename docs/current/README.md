# BSC — Native Queue Transition Redesign (NQTR)
Current documentation authority — 2026-10-09

**Read this folder first.** This is the only normative planning/documentation entry for the proposed native queue redesign. Work is documentation-only; NQTR runtime is NOT implemented, WH3 gameplay is NOT verified.

## Minimal reading order (do not read archives routinely)
1. PRODUCT_CONTRACT.md — what BSC must do and must never break.
2. CURRENT_BASELINE.md — exact source/branch and what has actually been verified.
3. NATIVE_RESEARCH_MAP.md — known Native entry points, missing proof, forbidden assumptions.
4. TARGET_ARCHITECTURE.md — proposed single authority and failure semantics.
5. IMPLEMENTATION_PLAN.md — build stages, ownership and acceptance gates.
6. VERIFICATION.md — offline/Windows/one final WH3 end-to-end verification.
7. RISKS_AND_DECISIONS.md — unresolved questions and decision register.
8. MAINTENANCE_RULES.md — how to update this set without reviving historical designs.

## Source-of-truth order
1. Frozen working code and exact build artifacts, with their hashes.
2. Current NQTR documents in this directory; label speculation as proposal.
3. Explicit test results with reproducible executable fixtures.
4. docs/past_doc only when a specific question needs historical evidence.
5. archive/ is historical and must never silently set current behavior.

**Do not use** the former README_FIRST/2026-09 maintainer reading list, D1/T1H design, 9.0.1 CURRENT_BUILD_MAP, or H1–H8 experiment writeups as a current implementation plan. They are retained in docs/past_doc, or pre-existing archive, for targeted forensic lookup only.

## Important status
- Formal mod version and Steam pack identity are release policy, not a proof of installed experimental controller revision.
- Current development starting point: H8 branch maintenance/t2move-h8-terminal-liveness-static, commit e711e716f2411599d75184618fc1ee5cb85bcd54.
- 9.0.2 experiment uses a separately overlaid static candidate map, NOT promoted native_maps/CURRENT.
- NQTR is not approved to replace the current Native bridge or ship to Steam.
- This branch must contain docs/metadata only; no player-facing behavior change.
