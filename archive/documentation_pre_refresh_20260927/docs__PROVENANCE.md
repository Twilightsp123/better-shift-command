# Provenance

## Upstream BSC behavior baseline

- Repository: `Twilightsp123/better-shift-command`
- Main commit frozen for this maintenance package: `0b690d59940e23e475de332a82cfecf072961977`
- Release identity: v1.2.2 / `V1_2_2`
- v1.2.2 was a Lua `math.huge` compatibility release over v1.2.1 SC6 behavior.
- Exact upstream controller/modules are preserved under `archive/upstream_v1.2.2/` and checked by SHA in `maintenance_tools/check_corepath_rc8.py`.

## Current WH3 maintenance line

- Target EXE SHA256: `6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297`
- RC5: current-build static map and first runtime gate candidate.
- RC6: command-root anchored physical-root discovery; demonstrated command root and physical candidate are independent.
- RC7: component-layout probe + safe observer stop. Runtime result preserved in archive: physical candidate bound, `slot_count=60`, component pair candidates `0`, safe-stop reported PASS.
- RC8: this package. Physical evidence is removed from the release-critical path; it remains archived/research code.

## Preservation policy

No historical physical code/test is presented as proven. Pre-CorePath tests that encoded Entity/physical semantics are preserved under `archive/legacy_physical_tests/`; active tests assert CorePath behavior instead. RC7 patch/summary/runtime instructions are preserved under `archive/rc7_component_layout_safe_stop/`.
