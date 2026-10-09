# GitHub maintenance guide — Better Shift Command v1.3.0

## Purpose

This repository/archive is intended to be sufficient for future investigation, repair, refactoring, WH3-version relocation, and release work without depending on the original chat history.

## Start here

1. `README_FIRST.md`
2. `docs/MAINTAINER_INDEX.md`
3. `docs/VERSION_POLICY.md`
4. `docs/ARCHITECTURE_STATUS_20260929.md`
5. `docs/OPEN_ISSUES.md`
6. `docs/ASSUMPTION_LEDGER.md`
7. `docs/TEST_MATRIX.md`
8. `docs/CURRENT_BUILD_MAP.md`

Only after those should a maintainer read `DEVELOPMENT_HISTORY.md` or `archive/`.

## Repository areas

- `source/` — canonical controller source used for pack construction.
- `src/` — working source tree, including Native Bridge C++/ASM.
- `tests/`, `steering_tests/` — controller and mutation regressions.
- `src/native_bridge/tests/` — Native identity/packet/evidence/build fixtures.
- `maintenance_tools/`, `tools/`, `controller_tools/` — validation/build tooling.
- `docs/` — current authority, design, decisions, assumptions, build map, static audit.
- `runtime_evidence/` — real WH3 logs and Windows build/delivery evidence.
- `archive/` — historical snapshots, old patches, rejected research, nested RC5/RC6/RC7 evidence.
- `release_artifacts/` — current validated binary resources and future intentional release artifact location.

## Rules for future changes

1. Keep the formal Mod version simple (`v1.3.x`, `v1.4.0`, etc.).
2. Keep public pack filename fixed at `zzz_better_shift_command_steam.pack`.
3. Internal architecture labels belong in provenance/history, not the formal version.
4. Do not rewrite archived logs/patches to match current naming; historical bytes/claims must remain historical.
5. Any reverse-engineered semantic claim must be recorded in `ASSUMPTION_LEDGER.md` with evidence grade before becoming release-critical.
6. Gameplay changes should be single-variable/staged and update `DECISION_LOG.md`, `TEST_MATRIX.md`, and `OPEN_ISSUES.md`.
7. Do not reintroduce quarantined physical evidence as a CorePath prerequisite without an explicit promotion decision.
8. Keep lifecycle/teardown work separate from Transition Policy smoothness work unless evidence proves they are inseparable.

## Transition Policy / MCT direction

The hidden profile interface already reserves the future user controls documented in `docs/design/MCT_POLICY_SCHEMA_D1.md`.

The key user-facing concepts are:

- Movement Cornering;
- Attack Handoff;
- Route Fidelity;
- Native Successor Tolerance;
- Minimum Engagement Time (default 3.0 s);
- Disengage Priority.

Visible MCT registration is intentionally deferred. Future UI must feed immutable per-battle policy values through the existing profile/compiler boundary rather than mutating scattered runtime constants directly.

## WH3 update / address relocation

When `Warhammer3.exe` changes, do not re-prove all gameplay behavior by default. Use the current build map/provenance to relocate the mandatory CorePath sites, validate local semantics/guards, rebuild the Native Bridge, and run focused runtime regression. If a structure/dataflow assumption changes, update the static audit and Assumption Ledger explicitly.
