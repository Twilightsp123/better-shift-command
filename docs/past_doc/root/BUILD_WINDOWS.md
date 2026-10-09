# Windows build — Better Shift Command v1.3.0

This is the current build entrypoint for future maintainers.

## Requirements

- Windows x64
- Visual Studio 2019 / MSVC v142
- MASM / ml64
- CMake
- current build-locked `Warhammer3.exe` matching `docs/CURRENT_BUILD_MAP.md`

## Pre-build checks

Run from the repository root:

```text
python maintenance_tools/check_corepath_rc8.py
python maintenance_tools/audit_evidence_wiring.py
python maintenance_tools/check_tpol_t1h.py
python maintenance_tools/check_documentation_contract.py
python tools/prebuild_contract_check.py
```

All must pass before compiling.

## Build Native Bridge

Use the existing `src/native_bridge/CMakeLists.txt` with an x64 VS2019/v142 configuration. The resulting binary must be:

`wh3_native_bridge.dll`

Run the existing Windows CTest suite and retain `backend_private_process`, `module_private_process`, and `mid_function_hook_smoke` coverage.

## Build pack

The canonical output filename is always:

`zzz_better_shift_command_steam.pack`

Example:

```text
python maintenance_tools/build_corepath_rc8.py build_win/Release/wh3_native_bridge.dll output/zzz_better_shift_command_steam.pack
python maintenance_tools/verify_corepath_rc8.py output/zzz_better_shift_command_steam.pack build_win/Release/wh3_native_bridge.dll
```

The tool filenames retain `corepath_rc8` because they enforce the current CorePath architecture contract. That is an engineering implementation name, not the Mod version.

## Delivery naming

Use a stable release-oriented name, for example:

`BetterShiftCommand_v1.3.0_Windows_Delivery.zip`

Do not encode RC/D1/T1H/native-fix suffixes into the formal release version or public pack filename.
