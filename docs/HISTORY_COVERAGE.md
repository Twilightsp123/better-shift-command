# History Coverage and Archive Gaps

This document answers a different question from `DEVELOPMENT_HISTORY.md`: **how much primary evidence for each era is actually present in this ZIP?**

Do not fill an archive gap by inferring from variable names or later summaries.

## Coverage matrix

| Era / stream | Coverage in this package | Primary locations | Known gap / caution |
|---|---|---|---|
| Native 0.1.1 / v0.2.x observer | PARTIAL | `src/native_bridge/tests/original/queue_probe_v02.lua`, `queue_probe_v021.lua`, Native changelog references | no complete early handoff bundle or full run logs in top-level archive |
| Native 0.4.1–0.4.9 | GOOD narrative | `src/native_bridge/CHANGELOG.md` | detailed historical runtime bundles mentioned by changelog are not all surfaced as top-level files here |
| Native v0.5.0 runtime closeout | SUMMARY present | `src/native_bridge/CHANGELOG.md` | changelog says exact PASS evidence was archived in the historical project; this PREBUILD ZIP does not expose a top-level `evidence/runtime_v050_pass/` tree |
| BSC R1 / R2 | WEAK | surviving `R1.xxx` code/tests and `r1_v3_*` modules | no complete R1/R2 maintenance narrative or original package in this ZIP |
| BSC R3 / R3.1 / R3.2 | GOOD narrative | `docs/DEVELOPMENT_HISTORY.md`, archived pre-CorePath history | original stage-by-stage raw bundles are not all retained here |
| BSC R4 Evidence V3 | GOOD historical narrative | `docs/DEVELOPMENT_HISTORY.md`, `archive/pre_corepath_local_tree/` | semantic conclusions are historical; RC8 retracted/quarantined key parts |
| BSC-CONV-RC1 / RC2 | SUMMARY ONLY | `docs/DEVELOPMENT_HISTORY.md` | no original RC1/RC2 patch/runtime package in this ZIP; cannot reconstruct exact code delta from this package alone |
| SC1–SC6 | GOOD consolidated narrative/tests | `docs/DEVELOPMENT_HISTORY.md`, current tests, upstream v1.2.2 archive | many one-off phase docs/diffs were intentionally removed during public-tree cleanup; use older release/Git archives for raw archaeology |
| v1.2.0 / v1.2.1 / v1.2.2 | GOOD | development history, `archive/upstream_v1.2.2/`, pre-CorePath local tree | v1.2.2 is current upstream behavior baseline; old v1.2.1 manifest is historical only |
| NATIVE-MAP-RC4 | GOOD summary | Native changelog / current source history | runtime specifics should not be conflated with RC8 |
| NATIVE-MAP-RC5 | NESTED evidence | inside `archive/rc7_component_layout_safe_stop/RC7_PREBUILD_ORIGINAL.zip` → `history/SOURCE_FIX_RC4_TO_RC5_6C104.patch`, validation | easy to miss because it is nested, not top-level |
| NATIVE-MAP-RC6 | NESTED evidence | same RC7 original ZIP → `history/rc6_root_discovery/` | easy to miss because it is nested |
| NATIVE-MAP-RC7 | STRONG | `archive/rc7_component_layout_safe_stop/` plus original RC7 ZIP | RC7 safe-stop success and physical-pair failure are separate outcomes |
| COREPATH-RC8 | STRONG historical/current-architecture lineage | root docs, patches, validation, current source | architecture lineage under formal v1.3.0; no longer a release version |

## Nested RC5/RC6 archive map

The following evidence is **inside** `archive/rc7_component_layout_safe_stop/RC7_PREBUILD_ORIGINAL.zip`:

```text
history/
  SOURCE_FIX_RC4_TO_RC5_6C104.patch
  SOURCE_PATCH_VALIDATION_RC5_6C104.txt
  rc6_root_discovery/
    RC6_CHANGE_SUMMARY.txt
    SOURCE_FIX_RC5_TO_RC6_ROOT_DISCOVERY.patch
    SOURCE_PATCH_VALIDATION_RC6_ROOT_DISCOVERY.txt

audit_reference/WH3_6C104A63_RELOCATION_AUDIT_PHASE62/
  01_current_exe_identity.txt
  ...
  16_phase62_prebuild_conclusion.txt
```

A maintainer researching RC5/RC6 should inspect that nested archive before concluding the records are absent.

## Known hard gaps

1. **BSC R1/R2:** lineage survives in code/test names, but the complete problem→experiment→result history is not present.
2. **BSC-CONV-RC1/RC2:** only the consolidated failure summary is present; original packages/patches/logs are missing from this ZIP.
3. Some early Native changelog entries refer to archived runtime evidence that is not directly surfaced in this PREBUILD package.

These gaps should be stated explicitly in future handoffs. Do not invent missing evidence to make the history look continuous.


## Transition Policy D1 additions

| Material | Coverage | Location |
|---|---|---|
| pre-D1 maintenance docs | COMPLETE SNAPSHOT | `archive/transition_policy_design_pre_d1/` |
| corrected Move-VTable Windows delivery | NESTED BUILD EVIDENCE | `runtime_evidence/20260929_transition_policy/BSC_COREPATH_RC8_WINDOWS_DELIVERY.zip` |
| 2026-09-29 smoothness/lifecycle runtime logs | DIRECT | `runtime_evidence/20260929_transition_policy/` |
| D1 architecture/MCT/migration/test design | COMPLETE DESIGN SET | `docs/design/` |


## 2026-10-05 transition-policy additions

| Material | Coverage | Location |
|---|---|---|
| BSC-TPOL-T1 pre-shared-evaluator controller | COMPLETE SOURCE SNAPSHOT | `archive/tpol_t1_pre_shared_evaluator/source/` |
| direct T2-B/T2-A/hairpin runtime observations | DIRECT LOG EVIDENCE | `runtime_evidence/20261005_transition_policy_experiments/` |
| direct T2-A/hairpin test artifacts | HISTORICAL / SUPERSEDED | `archive/legacy_move_scheduler_tests/` and Git history |
| native Move passthrough diagnostic | HISTORICAL / REJECTED AS PRODUCT ARCHITECTURE | `archive/tpol_t2_experiments/` + Git commit `e9306614156d39ac5e9778fe18d234703bbd7a44` |

## T1.5 coverage addition

| Material | Coverage | Location / caution |
|---|---|---|

| BSC-TPOL-T1.5 execution lineage | SOURCE + TEST + DECISION coverage | current controller, `archive/tpol_t15_pre_execution_lineage/`, `tests/test_execution_lineage_t15_*`, Decision Log | behavior-neutral structural stage; no WH3 gameplay claim |

- 2026-10-05 T1.6 committed-edge transaction: **fully preserved** in current source/tests/docs plus `archive/tpol_t16_pre_transition_transaction/`.
