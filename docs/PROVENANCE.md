# Provenance

## Current formal project identity

- Formal maintained version: **v1.3.0**
- Canonical Steam pack filename: `zzz_better_shift_command_steam.pack`
- The Native `1.0.17-...` string is an internal compatibility/build identifier, not the Mod version.


## Upstream BSC behavior baseline

- Repository: `Twilightsp123/better-shift-command`
- Main commit frozen for this maintenance package: `0b690d59940e23e475de332a82cfecf072961977`
- Historical upstream release identity: v1.2.2 / `V1_2_2`
- v1.2.2 was a Lua `math.huge` compatibility release over v1.2.1 SC6 behavior.
- Exact upstream controller/modules are preserved under `archive/upstream_v1.2.2/` and checked by SHA in `maintenance_tools/check_corepath_rc8.py`.

## Current WH3 maintenance line

- Target EXE SHA256: `6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297`
- NATIVE-MAP-RC5: current-build static map and first runtime gate candidate.
- NATIVE-MAP-RC6: command-root anchored physical-root discovery; demonstrated command root and physical candidate are independent.
- NATIVE-MAP-RC7: component-layout probe + safe observer stop. Runtime result preserved in archive: physical candidate bound, `slot_count=60`, component pair candidates `0`, safe-stop reported PASS.
- COREPATH-RC8: this package. Physical evidence is removed from the release-critical path; it remains archived/research code.

## Preservation policy

No historical physical code/test is presented as proven. Pre-CorePath tests that encoded Entity/physical semantics are preserved under `archive/legacy_physical_tests/`; active tests assert CorePath behavior instead. RC7 patch/summary/runtime instructions are preserved under `archive/rc7_component_layout_safe_stop/`.


## History coverage notes

- BSC R1/R2 complete maintenance narratives are **not present** in this ZIP; only surviving code/test lineage remains.
- BSC-CONV-RC1/RC2 is represented by the consolidated failure summary in `DEVELOPMENT_HISTORY.md`; original RC1/RC2 packages/patches are not present here.
- RC5 and RC6 primary patch/summary material is preserved **inside** `archive/rc7_component_layout_safe_stop/RC7_PREBUILD_ORIGINAL.zip` under `history/` and `history/rc6_root_discovery/`.
- See `HISTORY_COVERAGE.md` before concluding that an older artifact is missing.


## 2026-09-29 Transition Policy D1 design provenance

Runtime/source baseline copied byte-for-byte from:

- `BSC_COREPATH_RC8_MOVE_VTABLE_FIX_PREBUILD.zip`
- SHA256 `39ea75ecb6c370a0fd896a4a5ea9205733597f89c27544f872981ccd7a9e63ad`

Windows delivery retained as runtime-build evidence under `runtime_evidence/20260929_transition_policy/`:

- `BSC_COREPATH_RC8_WINDOWS_DELIVERY.zip`
- SHA256 `972a45164f1ae037927aad71b0ef6a28bc8dfecb53c25ae129f9b9b4cdf562ed`

Gameplay evidence retained:

- `script_log_290926_1818.txt` SHA256 `491bb0594f34fc5bacdde7f3de9eec4e3ec6e8d63e455c1b4d5a888b7a0d4f32`
- `script_log_290926_1833.txt` SHA256 `eec2efe0b23a7a2fc6519b3ed21f460203b27c854eb5b9f8cfa0dc4d49c42a7c`

These logs motivate the D1 transition-policy design; they are not reverse-engineering evidence and do not alter the locked Native build map.

## TPOL-T1H provenance

T1H controller/source begins from `BSC_TRANSITION_POLICY_ARCHITECTURE_D1`, whose runtime source matched the CorePath RC8 Move-VTable Fix baseline. Native bridge binary/source is unchanged at `1.0.17-corepath-wh3-6c104-movevtfix`. The installable T1H pack reuses the previously Windows-validated bridge DLL and changes only the embedded controller Lua/profile scaffold.
