# READ THIS FIRST — Better Shift Command v1.3.0

**Formal project version:** `v1.3.0`  
**Canonical Steam pack filename:** `zzz_better_shift_command_steam.pack`

This repository/archive is the long-term maintenance source for Better Shift Command. Internal labels such as `COREPATH-RC8`, `BSC-TPOL-D1`, `T1H`, and `movevtfix` are maintenance-history / architecture labels only. They are **not** the public Mod version.

## Important packaging rule

This archive does **not** generate or replace your already-renamed Steam pack. The canonical published/install filename is:

`zzz_better_shift_command_steam.pack`

The older installable T1H pack that existed before formal version normalization is preserved under:

`archive/pre_v130_installable_pack/`

It is historical/reference material and must not be mistaken for the formal v1.3.0 release artifact.

## Current runtime identity

- Mod/controller version: **v1.3.0**
- Upstream behavior ancestry: v1.2.2 + SC1–SC6 maintenance line
- Native Bridge compatibility/build ID: `1.0.17-corepath-wh3-6c104-movevtfix`
- Target WH3 SHA256: `6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297`
- Mandatory Native hooks: 16
- Physical evidence: **QUARANTINED**
- MCT UI: **not exposed yet**
- Hidden policy/profile interface: present
- Minimum Engagement Time default: **3.0 s**

The Native Bridge string is an internal compatibility/build identifier, not the Mod version.

## Mandatory maintainer reading order

1. `README_FIRST.md`
2. `README.md`
3. `docs/MAINTAINER_INDEX.md`
4. `docs/VERSION_POLICY.md`
5. `docs/ARCHITECTURE_STATUS_20260929.md`
6. `docs/OPEN_ISSUES.md`
7. `docs/ASSUMPTION_LEDGER.md`
8. `docs/TEST_MATRIX.md`
9. `docs/CURRENT_BUILD_MAP.md`
10. `docs/DECISION_LOG.md`
11. `docs/VERSION_LINEAGE.md`
12. `docs/PROVENANCE.md`
13. `docs/HISTORY_COVERAGE.md`
14. `docs/design/HIDDEN_MCT_INTERFACE_T1H.md`
15. `docs/design/MCT_POLICY_SCHEMA_D1.md`
16. `docs/design/BSC_TRANSITION_POLICY_ARCHITECTURE_D1.md`
17. `docs/DEVELOPMENT_HISTORY.md` only for historical context

## Current architecture status

The current runtime is **BSC-TPOL-T1.5 behavior-neutral** on top of the existing SC1–SC6 gameplay baseline. T1H provides the hidden immutable PolicyProfile/MCT adapter scaffold; T1 provides the shared `R1.TransitionPolicy.evaluate()` decision plane; T1.5 now separates original player-capture execution identity from BSC-issued/ACK identity and records the active execution lineage explicitly.

**T1.5 still intentionally does not change gameplay decisions.** Move→Attack remains strict until current Move semantic completion, an exact immediate future MOVE in SC6 still follows the legacy rollback behavior, and `ADOPT_ONLY` / hysteresis is not active. T1.5 is a structural prerequisite for T2 so Native-captured queue items and later BSC-issued commands cannot share an ambiguous identity slot.

The 2026-10-05 direct T2-B, T2-A, hairpin and native-passthrough builds are preserved as historical experiments/evidence only. They do not override the staged D1 migration or current runtime source.

The next gameplay work is therefore:

- T2-A immediate-successor MOVE policy through the shared evaluator;
- T2-B Move→Attack terminal handoff reintroduced through the shared evaluator, using the successful runtime experiment as evidence;
- T2-C separate issue/adopt hysteresis windows;
- later visible MCT wiring.

Battle teardown/hang remains a separate lifecycle stream and must not be mixed into transition-policy changes.
