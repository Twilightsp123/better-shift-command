# NQTR Maintainer Protocol

## Start / reading budget
Read docs/current/README.md and only the current document required by the task. Old docs under docs/past_doc and archive are *not* default reading. Fetch them only by explicit case, with the exact file and reason recorded.

## Each modification must record
1. Exact baseline branch/commit and current executable hash; what source or memory layout is authoritative.
2. Which runtime trace / source establishes a FACT, and which inferences remain.
3. Target invariants in PRODUCT_CONTRACT.md, including speed-first cornering and Shift ATTACK.
4. Revised contract/model + adversarial negative fixture before changing Native Hook or issue privileges.
5. Changed/unchanged Native addresses, signatures, ABI, byte-locked DLL and pack file identities.
6. Phase-gate status (STATIC, MODEL, WINDOWS, WH3), not just generic PASS.
7. Open issues and impact on queue/tail ownership; exact procedure to roll back safely.
8. New meaningful decision in RISKS_AND_DECISIONS.md; update IMPLEMENTATION_PLAN and VERIFICATION.

## Git / deliverable safety
- Work in a bounded branch from an identified commit; do not rewrite past experimental branches or main.
- Batch read/build/push; if git/remote call stalls, stop and re-query state before retrying. Prefer connector/API for repository metadata rather than repeatedly cloning.
- No automatic merge or Steam publish; user review for release decisions.
- Never alter game EXE, claim gameplay tested from GitHub CI, or use stale 9.0.1 RVAs in 9.0.2.
- Keep complete source, WinX64 Native binary, normal/DEBUG PACK, source commit, SHA256 manifest, readme and offline evidence in each delivery stage when code actually changes.
- Documentation-only branch may contain a documentation ZIP or GitHub diff; do NOT generate installation PACKs on this branch.

## Historical archive preservation
- docs/past_doc preserves previous docs with original bytes/blobs and original relative path below past_doc; there is no normative guidance there.
- Existing archive/ and runtime_evidence/ are untouched and remain reference-only.
- Legacy documentation contract checks archived document identity/coverage but is no longer allowed to dictate current design.
- No redundant editable copies of an active plan. If current docs contradict actual code, correct the current doc with a visible open/blocked label; don't silently retrofit the archive.
