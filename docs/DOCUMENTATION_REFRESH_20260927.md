# Documentation Refresh — 2026-09-27

Scope: **documentation/navigation only**. No Lua, C++, ASM, test behavior, baseline DLL, or build-tool behavior is intentionally changed by this refresh.

## Added

- `docs/MAINTAINER_INDEX.md` — authority/read order and conflict rules.
- `docs/VERSION_LINEAGE.md` — separates independent version/RC streams.
- `docs/OPEN_ISSUES.md` — current unresolved work only.
- `docs/HISTORY_COVERAGE.md` — archive completeness, nested RC5/RC6 location, and known gaps.
- `docs/MAINTENANCE_PROTOCOL.md` — mandatory future handoff/update protocol.
- `docs/DOCUMENTATION_REFRESH_20260927.md` — this record.
- `maintenance_tools/check_documentation_contract.py` — fail-closed handoff/document consistency gate.

## Updated

- `README_FIRST.md` — mandatory reading order and current one-screen state.
- `README.md` — points maintainers to the authoritative navigation chain.
- `docs/DEVELOPMENT_HISTORY.md` — historical-authority warning, current baseline correction, and superseded physical-evidence wording.
- `docs/PROVENANCE.md` — archive-gap/nested-history notes.
- `docs/TEST_MATRIX.md` — document authority note and current-only wording.
- `docs/DECISION_LOG.md` — documentation-governance decision.
- `COREPATH_CHANGELOG.md` — records this documentation-only maintenance pass.
- `src/native_bridge/CHANGELOG.md` — adds a Native-only history warning and points to version-stream disambiguation.
- `RELEASE_MANIFEST.json` — adds documentation revision metadata only.
- `SHA256SUMS.txt` — regenerated after all documentation changes.

## Preserved pre-refresh copies

Original versions of the modified root/current docs are preserved under:

`archive/documentation_pre_refresh_20260927/`

## Runtime-source integrity

The refresh process performs a before/after SHA256 comparison for all files outside the documentation/metadata set. Any mismatch is treated as a packaging failure. The resulting audit is written to `reports/DOCUMENTATION_ONLY_INTEGRITY_AUDIT.txt`.
