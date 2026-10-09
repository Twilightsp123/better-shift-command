# H2/H3 + WH3 9.0.2 Native integration — isolated WinX64 candidate

Date: 2026-10-09. Base H2/H3: `0f80b083bdf55a98c257d195c531e5b78ea2956f`.
9.0.2 original address branch: `maintenance/wh3-9.0.2-map-candidate`,
head `679c0e8aa2be959da89f3e2af0ae78ab69b679be`.
Working branch: `maintenance/t2move-h2h3-wh3-902-integration`.

## What went wrong in the first WH3 live run

The H2/H3 CI pack previously shipped the 9.0.1 Native DLL despite passing
controller and pack-format offline checks. WH3 successfully loaded
`better_shift_command.lua` and its DLL, but observer startup rejected
`OBSERVER_HOST_EXE_SHA256_MISMATCH`. This happened **before** MOVE simulation
or any active game control and is not an H2/H3 geometry failure.

## Existing 9.0.2 address work is reused, not re-derived

- Target EXE SHA256 `fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785`.
- 16 mandatory core Hook RVA/guard pairs, plus two optional disabled
  sites, originally reconstructed in `native_maps/wh3_9.0.2_fec656f4.json`.
- Full Move VTable `0x03913618` (not Simple/Intercept `0x03910438`);
  Attack VTable `0x03912988`.
- The existing H2/H3 branch already contained the L3 verified 9.0.2
  candidate `native_maps/candidates/wh3_9.0.2_fec656f4.json` and
  `native_maps/CANDIDATE`, plus staged build-local generated-header support.
  An added integration contract compares every RVA and guard, plus
  derived VTables, against the original 9.0.2 address branch byte strings.

The current `native_maps/CURRENT` deliberately stays at the last
WH3-runtime-validated 9.0.1 map. Do not promote it before 9.0.2 live smoke.
The new build feeds the 9.0.2 candidate through
`WH3_NATIVE_MAP_INCLUDE_DIR` to the Windows v142 compiler, validates the
generated include overlay and archives it with the compiled DLL.
The C++ runtime still fails closed on a wrong target EXE or guard bytes.

## Native and Controller version synchronization

- New diagnostic/ABI string: `1.0.18-corepath-wh3-fec656f4-map902`
  in `bridge_host.hpp`, Controller, fixture, packer, CorePath contract.
- `CMakeLists.txt` project version: 1.0.18, retaining the H2/H3
  **CXX-only** `/W4 /WX /EHsc` generator expressions so no
  `/EHsc` or `/W4` is wrongly passed to the MASM `ml64.exe` input.
- All H2/B/C/D/H3 route-policy changes remain as sealed in H2/H3,
  barring the Native Bridge version check. This avoids the historical
  9.0.2 address branch's older Controller overwriting later H2 changes.
- No silent SHA bypass and no dynamic runtime address scanner.

## Offline and Windows CI sequence

1. Linux: source/native-map contracts, H2 controller 7/7, H3 synthetic
   routes 9/9, Native parity 4/4, H2 mutants 5/5 CAUGHT,
   full 46-job maintenance and other address-pipeline regression tests.
2. Windows 2022: VS2022 generator x64 **v142**, MASM, build-local
   9.0.2 overlay header, `cmake --build`, then Windows Native CTest.
   Upload the actual compiled `wh3_native_bridge.dll` and header.
3. Linux packaging job consumes the DLL from the **successful Windows job**.
   `seal_h2h3_902.py` checks embedded 9.0.2 hash and version, rejects
   the known 9.0.1 binary, validates header parity and v142 PE metadata,
   builds/verifies ordinary+DEBUG deterministic PFH5 test packs and
   a full 9.0.2 integrated tracked-source ZIP with SHA256 manifests.
4. `GitHub Actions SUCCESS` means the binary is a Windows-built static
   test candidate. It does **not** prove the WH3 observer can attach to
   the real game process, that the game uses this exact binary, or that
   H2/H3 movement behavior is smooth.

## Real WH3 acceptance — UNTESTED

Install ONE experimental BSC test pack (prefer DEBUG) and disable
Steam Workshop/other BSC packs to avoid script/native shadowing.
Confirm `Warhammer3.exe` SHA256 is the map's exact target.
First smoke **only startup**: `BRIDGE_OK`, `OBSERVER_PREPARE`,
`OBSERVER_READY`, `START`, `READY`; ensure there is no
`HOST_EXE_SHA256_MISMATCH`, `HOOK_BYTES_MISMATCH`, fatal Native error
or game hang. Then issue normal RMB MOVE and ATTACK and verify V3
execution identity and correct event capture. Finally test Quit-to-Windows
safe-stop.

**Only after this startup/Native smoke passes**, execute
RT-TP-02/03 (Move→Attack) and RT-TP-04/05 (Move→Move,
90°/135°/180° foldback, dense short legs, stacked SC3 debts, multi-unit).
Keep logs and video, record both movement smoothness and waypoint
fidelity separately. No automatic Steam publishing or release promotion.

No WH3 executable is present on GitHub runners: game runtime validation
requires a local Windows WH3 session and returned logs.
