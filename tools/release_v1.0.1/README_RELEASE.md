# Better Shift Command v1.0.1 — Release Builder

This handoff freezes the runtime-successful TESTFIX B logic and only changes release metadata/logging.

## Functional delta from v1.0.0
- Native Bridge v0.5.1: per-command-kind calibration. MOVE can arm after a natural accepted MOVE without requiring ATTACK calibration first.
- Controller v0.2.6: native MOVE canonicalization no longer triggers a 5 cm hard-fail after strong issue/source/revision identity has already matched.

## Production-only cleanup
- build tag: `BETTER_SHIFT_COMMAND_V1.0.1`
- `DEBUG_TELEMETRY=false`
- per-order DISPATCH/ACK, PLAN_ACTIVATED, GEN_CANCEL, ATTACK_HOLD and related success traces are debug-only
- normal `NATIVE_EMBED_KEEP` is debug-only
- fatal/controller errors, refusal/degradation warnings, native component WRITE/verification, Bridge ABI/version success, and session-end diagnostics remain available

## Build
Run on the validated Windows machine with VS2019/v142 (or VS2022 + v142 toolset):

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\BUILD_RELEASE_V1.0.1.ps1 -GameDir 'C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III'
```

The Steam upload artifact is:

`output\ready_to_install\zzz_better_shift_command_steam.pack`

Do not upload an earlier TESTFIX A/B pack after this release build succeeds.
