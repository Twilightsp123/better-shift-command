# Better Shift Command v1.2.2

Better Shift Command is a Windows x64 battle-control mod for **Total War: WARHAMMER III** that improves Shift-queued movement and Attack→Move transitions without replacing the game's locomotion system.

## What v1.2.2 changes

v1.2.2 is a **Lua compatibility release** on top of the validated v1.2.1 SC6 behavior baseline.

A field log showed that some WH3 Lua environments can expose `math.huge` as `nil`. In v1.2.1 that caused the controller to fail during startup in `finite()` before any battle command plan was processed. v1.2.2 uses a local `BSC_HUGE` sentinel: it uses `math.huge` when available and falls back to `1e300` when the host does not expose that field.

This release does **not** change SC1–SC6 movement/attack behavior, Native Bridge hooks, ContactPair ASM, hook RVAs, MinHook, or the Native ABI. It also does not mutate the global Lua `math` table.

## Field validation

The original failing environment produced `EARLY_BASELINE_UNAVAILABLE` followed by `CONTROLLER_FAIL` because `math.huge` was `nil`.

After the v1.2.2 compatibility fix, `script_log_200926_1849.txt` showed the controller entering battle normally and continuing into live SC6 execution-identity reconciliation (`NATIVE_FUTURE_OVERRUN` / `NATIVE_SUCCESSOR_ROLLBACK`) with no recurrence of the `math.huge` startup failure. Result: **PASS**.

The source regression gate also includes `missing math.huge host field does not disable controller`; the current source suite passes **19/19 jobs** and the mutation gate catches **40/40 mutations**.

## v1.2.1 behavior baseline retained

v1.2.1 added **SC6: V3 Execution Identity Reconciliation** on top of the SC1–SC5 movement baseline:

- V3 active-order identity is the production-authoritative execution source.
- Exact matching uses order kind, engine sequence, accepted journal receipt, unit lifetime, and target/destination identity.
- If Native advances to an immediate successor ATTACK before the Exit obligation is transferable, the controller rolls back to the current Exit MOVE.
- If Native overruns to a later canonical action, the controller does not skip intermediate actions; it restores the current MOVE and keeps the Lua suffix for later re-issue.
- `current_target()` remains diagnostic only and cannot authorize cursor advancement.
- SC5 physical Exit recovery runs only when the exact current Exit MOVE is still the Native active execution.
- Retired V2 evidence readers remain exported for API compatibility but fail closed with `V2_RETIRED_USE_V3`.

## Release logging / performance

`DEBUG_TELEMETRY` defaults to **false**. High-frequency ORDER/ACTION/FEG/contact/scheduler diagnostics remain gated before string construction. Runtime observers, V3 execution identity, ContactPair tracking, route checks, steering, FEG, SC5 and SC6 remain enabled because they are behavior, not debug logging.

## Version identity

- Controller: `1.2.2`
- Run ID: `V1_2_2`
- Build marker: `BETTER_SHIFT_COMMAND_V1.2.2`
- Native Bridge ABI: `1.0.15-r4-evidence-v3-validated-userdata-root`
- Platform: Windows x64

The Native ABI is intentionally unchanged because v1.2.2 does not modify Native Bridge behavior.

## Repository layout

```text
baseline/            Frozen MinHook runtime, license and self-contained bootstrap
controller_tools/    Deterministic pack helpers and analysis/install test helpers
maintenance_tools/   v1.2.2 release checks, evidence wiring audit, build and verify tools
source/               Authoritative Lua controller sources
src/                  Synchronized controller copy + Native Bridge source/tests
steering_tests/       SC1–SC6 mutation gate
tests/                Release regression suites, including math.huge and V3 execution identity
tools/                Windows PE/toolchain verifier + read-only PE inventory helper
docs/                 Consolidated development/maintenance history
```

## Source validation

```bat
python maintenance_tools\check_release_v122.py
python maintenance_tools\audit_evidence_wiring.py
python maintenance_tools\run_checks_v122.py
```

Expected source-side result: **19/19 jobs PASS** and **40/40 mutations caught**.

## Build v1.2.2 on Windows

A pack rebuild is required only when producing a distributable v1.2.2 `.pack`. Existing project requirements:

- Visual Studio 2019 Build Tools
- MSVC v142 x64
- MASM / `ml64`
- CMake
- Python 3

```bat
cmake -S src\native_bridge -B build_win -G "Visual Studio 16 2019" -A x64 -T v142
cmake --build build_win --config Release
ctest --test-dir build_win -C Release --output-on-failure
python tools\verify_pe_toolchain.py build_win\Release\wh3_native_bridge.dll
python maintenance_tools\build_release_v122.py build_win\Release\wh3_native_bridge.dll output\better_shift_command_v1.2.2.pack
python maintenance_tools\verify_release_v122.py output\better_shift_command_v1.2.2.pack build_win\Release\wh3_native_bridge.dll
```

The Windows build must assemble/link `contact_pair_hook_x64.asm` and pass the Native CTest suite, including the mid-function hook smoke, before a distributable pack is published.

## Install the built pack

After building and verifying a distributable pack, copy only:

```text
output\better_shift_command_v1.2.2.pack
```

to the WH3 data directory as:

```text
zzz_better_shift_command_steam.pack
```

Do not copy `wh3_native_bridge.dll` or `minhook.x64.dll` separately; the pack is self-contained.

## Third-party component

The self-contained release uses a frozen x64 MinHook runtime. Its license is preserved in `baseline/MINHOOK_LICENSE.txt` and embedded into the generated pack.

For the full development path from Evidence V3 through SC1–SC6 and the v1.2.2 compatibility fix, see `docs/DEVELOPMENT_HISTORY.md`.
