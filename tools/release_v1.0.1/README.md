# v1.0.1 Release Builder

This directory reproduces the v1.0.1 Windows x64 self-contained Steam pack.

Requirements:

- Windows x64
- Visual Studio 2019/v142, or VS2022 with the v142 toolset installed
- CMake from the Visual Studio installation
- Python 3
- a local Total War: WARHAMMER III installation for the install step

Run `BUILD_RELEASE_V1.0.1.ps1` from this directory on the validated Windows build machine.
The script intentionally refuses v143-only builds because TESTFIX A demonstrated that changing the compiler/toolchain family at the same time as native logic changes introduced a new Hook-installation variable. TESTFIX B restored the runtime-successful v142 family.

The Steam upload artifact is generated as:

`output\ready_to_install\zzz_better_shift_command_steam.pack`

The builder embeds the compiled `wh3_native_bridge.dll` and the validated `minhook.x64.dll` as Lua binary payloads inside the PFH5 pack. The battle loader materializes them next to `Warhammer3.exe` only when the bytes differ from the embedded payload.
