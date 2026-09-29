# Better Shift Command — CorePath RC8 PREBUILD

This tree is the 2026-09-27 maintenance candidate for WH3 9.0.1. It is **not a published release and not an install-ready pack**.

The behavior baseline is upstream BSC v1.2.2 (`0b690d59940e23e475de332a82cfecf072961977`), including the v1.2.1 SC6 execution-identity behavior and the v1.2.2 `math.huge` Lua compatibility fix. CorePath RC8 changes the Native architecture: unverified physical Entity evidence is quarantined and cannot veto command behavior.

## Candidate identity

- Controller: `1.2.2-corepath-rc8`
- Run ID: `V1_2_2_COREPATH_RC8`
- Build marker: `BETTER_SHIFT_COMMAND_V1.2.2_COREPATH_RC8`
- Native Bridge: `1.0.16-corepath-wh3-6c104-rc8`
- Target WH3 SHA256: `6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297`
- Platform: Windows x64, VS2019 / MSVC v142 / MASM

## Architecture change

The mandatory native set is now **16 command/packet hooks**. ContactPair is retained as a separately mapped optional research site and is staged disabled. Smart Guard is also a separately mapped optional site and staged disabled.

Production V3 capabilities advertise execution identity when the build-locked core observer is active, but advertise `entity_snapshot=false`, `combat_groups=false`, `contact_pairs=false`, and `target_specific_physical_contact=false`. Production physical read/bind APIs fail closed with `PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8`.

SC5 retains bounded Exit recovery without Entity: exact current Exit MOVE identity + positive live enemy contact/proximity + near-zero speed + bounded no-progress window + shared recovery budget. SC6 remains exact-order authoritative.

## Validation

Run:

```bat
python maintenance_tools\check_corepath_rc8.py
python maintenance_tools\audit_evidence_wiring.py
python maintenance_tools\run_checks_corepath_rc8.py
python tools\prebuild_contract_check.py
```

Current portable result: controller jobs 19/19 PASS, mutations 40/40 caught, Native CTest 13/13 PASS, ASan/UBSan 13/13 PASS.

Windows BuildOnly and WH3 runtime CorePath smoke are still pending. Follow `ANTIGRAVITY_BUILD_ONLY.txt`. Do not publish/install this PREBUILD tree as a release.

See `README_FIRST.md`, `docs/ASSUMPTION_LEDGER.md`, `docs/PROVENANCE.md`, `docs/DECISION_LOG.md`, and `docs/TEST_MATRIX.md` before changing reverse-engineered fields.
