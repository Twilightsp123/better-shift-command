# Better Shift Command v1.2.1

Better Shift Command is a Windows x64 battle-control mod for **Total War: WARHAMMER III** that improves Shift-queued movement and Attack→Move transitions without replacing the game's locomotion system.

## What v1.2.1 fixes

v1.2.1 keeps the SC1–SC5 movement behavior from v1.2.0 and adds **SC6: V3 Execution Identity Reconciliation**.

A field reproduction showed that Lua could still believe the current action was an Exit MOVE while CA's Native active order had already advanced to a future queued ATTACK. The command line remained visible, but the unit continued fighting until a normal RMB MOVE replaced the Native ATTACK.

SC6 fixes that execution-state split:

- V3 active-order identity is the production-authoritative execution source.
- Exact matching uses order kind, engine sequence, accepted journal receipt, unit lifetime, and target/destination identity.
- If Native advances to an immediate successor ATTACK before the Exit obligation is transferable, the controller rolls back to the current Exit MOVE.
- If Native overruns to a later canonical action, the controller does not skip intermediate actions; it restores the current MOVE and keeps the Lua suffix for later re-issue.
- `current_target()` remains diagnostic only and cannot authorize cursor advancement.
- SC5 physical Exit recovery runs only when the exact current Exit MOVE is still the Native active execution.
- Retired V2 evidence readers remain exported for API compatibility but fail closed with `V2_RETIRED_USE_V3`.

The temporary RMB differential instrumentation used to diagnose and validate the bug is **not included** in this release.

## Field validation

The v1.2.1 candidate was tested against the same trigger pattern that produced the earlier failure: a future Shift ATTACK was appended while an Exit MOVE was still under `EXIT_ROUTE_PROTECT`. In the validation log the Native active order remained the current MOVE until `ROUTE_NODE_PASSED`, after which the controller dispatched the queued ATTACK normally. The old `CURRENT_TARGET_IS_NOT_ACTION_ID` failure did not recur.

## Release logging / performance

`DEBUG_TELEMETRY` defaults to **false**. High-frequency ORDER/ACTION/FEG/contact/scheduler diagnostics remain gated before string construction. Runtime observers, V3 execution identity, ContactPair tracking, route checks, steering, FEG, SC5 and SC6 remain enabled because they are behavior, not debug logging.

## Version identity

- Controller: `1.2.1`
- Run ID: `V1_2_1`
- Build marker: `BETTER_SHIFT_COMMAND_V1.2.1`
- Native Bridge ABI: `1.0.15-r4-evidence-v3-validated-userdata-root`
- Platform: Windows x64

The ABI string is intentionally unchanged. The Native Bridge does contain a compatibility hardening change: retired V2 evidence reader names now fail closed instead of silently reaching live V3 readers.

## Repository layout

```text
baseline/            Frozen MinHook runtime, license and self-contained bootstrap
controller_tools/    Deterministic pack helpers and analysis/install test helpers
maintenance_tools/   v1.2.1 release checks, evidence wiring audit, build and verify tools
source/               Authoritative Lua controller sources
src/                  Synchronized controller copy + Native Bridge source/tests
steering_tests/       SC1–SC6 mutation gate
tests/                Release regression suites, including V3 execution identity
tools/                Windows PE/toolchain verifier + read-only PE inventory helper
docs/                 Consolidated development/maintenance history
```

## Build v1.2.1 on Windows

Existing project requirements:

- Visual Studio 2019 Build Tools
- MSVC v142 x64
- MASM / `ml64`
- CMake
- Python 3

```bat
python maintenance_tools\check_release_v121.py
python maintenance_tools\audit_evidence_wiring.py
cmake -S src\native_bridge -B build_win -G "Visual Studio 16 2019" -A x64 -T v142
cmake --build build_win --config Release
ctest --test-dir build_win -C Release --output-on-failure
python tools\verify_pe_toolchain.py build_win\Release\wh3_native_bridge.dll
python maintenance_tools\build_release_v121.py build_win\Release\wh3_native_bridge.dll output\better_shift_command_v1.2.1.pack
python maintenance_tools\verify_release_v121.py output\better_shift_command_v1.2.1.pack build_win\Release\wh3_native_bridge.dll
```

The Windows build must assemble/link `contact_pair_hook_x64.asm` and pass the Native CTest suite, including the mid-function hook smoke.

## Run the release regression gate

```bat
python maintenance_tools\run_checks_v121.py
```

Expected source-side result for this frozen tree: **19/19 jobs PASS** and **40/40 mutations caught**.

## Install the built pack

Copy only:

```text
output\better_shift_command_v1.2.1.pack
```

to the WH3 data directory as:

```text
zzz_better_shift_command_steam.pack
```

Do not copy `wh3_native_bridge.dll` or `minhook.x64.dll` separately; the pack is self-contained.

## Third-party component

The self-contained release uses a frozen x64 MinHook runtime. Its license is preserved in `baseline/MINHOOK_LICENSE.txt` and embedded into the generated pack.

For the full development path from Evidence V3 through SC1–SC6, see `docs/DEVELOPMENT_HISTORY.md`.
