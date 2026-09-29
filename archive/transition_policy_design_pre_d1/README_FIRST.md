# READ THIS FIRST — BSC CorePath RC8 PREBUILD

> **Document navigation rule:** do not begin maintenance by reading `DEVELOPMENT_HISTORY.md` or a random `RCx` file. Historical documents intentionally preserve old assumptions that may now be retracted. Start from the current-state chain below.

This archive is a **maintenance/prebuild candidate**, not a Steam/GitHub release and not an install-ready pack.

## Mandatory reading order

Read these in order before changing code or asking for a new probe:

1. `README_FIRST.md` — package identity, current stage, forbidden shortcuts.
2. `docs/MAINTAINER_INDEX.md` — document authority and where each version line belongs.
3. `docs/ARCHITECTURE_STATUS_20260927.md` — current production architecture only.
4. `docs/OPEN_ISSUES.md` — what is actually unfinished now.
5. `docs/ASSUMPTION_LEDGER.md` — proven / unverified / retracted reverse-engineering facts.
6. `docs/TEST_MATRIX.md` — which gates have really passed and which remain pending.
7. `docs/CURRENT_BUILD_MAP.md` — current WH3 build-locked static map.
8. `docs/DECISION_LOG.md` — architecture decisions and accepted trade-offs.
9. `docs/VERSION_LINEAGE.md` — separates BSC R/SC/release versions, Native versions, WH3-map RCs, and Smart Guard RCs.
10. `docs/PROVENANCE.md` + `docs/HISTORY_COVERAGE.md` — source/archive coverage and known historical gaps.
11. `docs/DEVELOPMENT_HISTORY.md` — historical narrative. **History is not current authority.**
12. `src/native_bridge/CHANGELOG.md` and `archive/` — detailed archaeology only when needed.

If two documents conflict, follow the authority order in `docs/MAINTAINER_INDEX.md`; do not average the claims together.

## Current candidate in one screen

- Upstream behavior baseline: **BSC v1.2.2**.
- Controller candidate: `1.2.2-corepath-rc8`.
- Native Bridge candidate: `1.0.17-corepath-wh3-6c104-movevtfix`.
- Target WH3 SHA256: `6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297`.
- Mandatory native set: **16 command/packet hooks**.
- ContactPair: optional static research site, **STAGED_DISABLED**.
- Smart Guard: separate optional site, **STAGED_DISABLED**.
- EntitySnapshot / MovementComponent / Entity Alive / ContactPair physical evidence: **QUARANTINED** in production.
- SC1–SC6 command/route behavior remains the gameplay baseline.
- RC7 safe-stop is retained only for explicit **Quit to Windows**.
- 2026-09-29 static outcome audit: top-level Full Move VTable is **`0x03910AA8`**; prior `0x0390E248` top-level claim is retracted (it is Simple/Intercept Move).
- Allocator return ABI is proven unchanged: RAX = exact `slot_base`; R1/R2/R3 experimental outcome resolvers are withdrawn.

## Why RC8 exists

The inherited physical model used names such as `Entity`, `MovementComponent`, and `Entity::is_alive`. One key claimed proof was retracted: the old `Entity +0x18 = MovementComponent*` attribution was actually a `ResultRecord +0x18 = Controller*` access. RC7 runtime also found a 60-member physical candidate but zero valid Entity→Component back-reference pairs.

Those facts do **not** prove physical research is useless. They prove it is not safe to make it a BSC release prerequisite. RC8 therefore keeps the research source/history while removing it from CorePath authorization.

## Current validation

Portable/offline status already present in this archive:

- Controller source jobs: **19/19 PASS**
- Mutation gate: **40/40 CAUGHT**
- Portable Native CTest: **13/13 PASS**
- ASan/UBSan Native CTest: **13/13 PASS**
- Prebuild source contract: **PASS (16 core + 2 optional sites)**

Still required before any install/test pack:

1. Windows VS2019 v142 x64 + MASM BuildOnly.
2. Pre/post-build EXE inspection: SHA match + **16/16 mandatory core guards**; optional sites reported separately.
3. Windows CTest including backend/module/**mid-function hook smoke**.
4. PE toolchain verification.
5. Deterministic candidate pack build and embedded DLL/MinHook SHA verification.
6. WH3 runtime CorePath smoke: Move→Move, Move→Attack, Attack→Exit Move, Exit→Attack, RMB cancel, SC5 fallback, SC6 rollback/adopt, multi-unit, second battle, and Quit-to-Windows safe stop.

## BuildOnly rule

Do not ask a build agent to redesign, refactor, or “fix” source during BuildOnly. Use `ANTIGRAVITY_BUILD_ONLY.txt` exactly. A BuildOnly failure is evidence to classify first, not permission to change unrelated gameplay code.

## Documentation rule for future handoffs

Before producing the next maintenance ZIP, follow `docs/MAINTENANCE_PROTOCOL.md`. Every new package must make the current state readable without requiring the maintainer to reconstruct it from old RC archives.
