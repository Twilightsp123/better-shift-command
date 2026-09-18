# Better Shift Command v1.2.0

Better Shift Command is a Windows x64 battle-control mod for **Total War: WARHAMMER III** that improves Shift-queued movement and Attack→Move transitions without replacing the game's locomotion system.

## What v1.2.0 changes

The release consolidates the tested movement work into one production branch:

- **Steering-aware Move→Move handoff** — intermediate waypoints can hand off before vanilla arrival braking turns every point into a visible stop.
- **Early predictive cornering** — safe corners may transition earlier while remaining bounded by the current and next route legs.
- **Soft route debt** — an earlier waypoint obligation can remain tracked in the background when the successor path still crosses its corridor; deviations remain hard-blocked.
- **Bounded stall escape** — when a unit begins braking just outside an otherwise valid turn corridor, a tightly limited escape prevents the unit from waiting until speed reaches zero.
- **Attack→Move Exit recovery** — if the Exit MOVE was accepted but the unit is still physically stuck in real enemy contact with little progress, the controller can reassert the same Exit MOVE within a bounded recovery budget.
- **Sticky melee state is not treated as physical contact** — `melee=true` alone never authorizes Exit reassert.

## Release logging / performance

`DEBUG_TELEMETRY` defaults to **false** in v1.2.0.

High-frequency ORDER/ACTION/FEG/contact/scheduler/heartbeat diagnostics are gated **before string formatting**, so the production build avoids both file-output cost and most debug-string construction cost. Pure test-only generation observers are also disabled when telemetry is off.

The following remain enabled because they are runtime logic, not logging:

- Native order observation and command identity tracking;
- ContactPair tracking and evidence sampling;
- the controller's 100 ms decision poll;
- route-safety / waypoint-debt checks;
- steering, stall escape, FEG and Exit recovery.

Sparse startup and true fault/recovery logs are retained so real failures can still be diagnosed.

## Version identity

- Controller: `1.2.0`
- Run ID: `V1_2_0`
- Build marker: `BETTER_SHIFT_COMMAND_V1.2.0`
- Native Bridge ABI: `1.0.15-r4-evidence-v3-validated-userdata-root`
- Platform: Windows x64

The Native ABI intentionally remains on the validated R4 value because the v1.2.0 release cleanup changed controller identity/logging only; it did not change Native Bridge behavior.

## Repository layout

```text
baseline/            Frozen MinHook runtime, license and self-contained bootstrap
controller_tools/    Deterministic pack helpers and analysis/install test helpers
maintenance_tools/   v1.2.0 release check, build, verify and regression runner
source/               Authoritative Lua controller sources
src/                  Synchronized controller copy + Native Bridge source/tests
steering_tests/       v1.2.0 mutation gate
tests/               Release regression suites
 tools/               Windows PE/toolchain verifier + read-only PE inventory helper
 docs/                One consolidated development/maintenance history
```

Historical SC1–SC5 build instructions, intermediate diffs, one-off package-check files and reverse/research notes are intentionally **not** kept as loose public files. Their durable conclusions are consolidated in `docs/DEVELOPMENT_HISTORY.md`.

## Build v1.2.0 on Windows

Requirements already expected by this project:

- Visual Studio 2019 Build Tools
- MSVC v142 x64
- MASM / `ml64`
- CMake
- Python 3

No extra runtime DLL is manually installed into the game directory; the final `.pack` embeds the Bridge and frozen MinHook payload.

```bat
python maintenance_tools\check_release_v120.py
cmake -S src\native_bridge -B build_win -G "Visual Studio 16 2019" -A x64 -T v142
cmake --build build_win --config Release
ctest --test-dir build_win -C Release --output-on-failure
python tools\verify_pe_toolchain.py build_win\Release\wh3_native_bridge.dll
python maintenance_tools\build_release_v120.py build_win\Release\wh3_native_bridge.dll output\better_shift_command_v1.2.0.pack
python maintenance_tools\verify_release_v120.py output\better_shift_command_v1.2.0.pack build_win\Release\wh3_native_bridge.dll
```

The Native build must assemble/link `contact_pair_hook_x64.asm` and pass the Windows CTest suite before the pack is considered a release build.

## Run the release regression gate

From the repository root:

```bat
python maintenance_tools\run_checks_v120.py
```

The frozen v1.2.0 source gate is expected to cover controller identity/quiet logging, FEG gates, Evidence V3 handoff/recovery/contact behavior, second-charge behavior, route/block regressions, tooling, PE inventory and the SC5-derived mutation suite.

## Install the built pack

After all build and verification steps pass, copy only:

```text
output\better_shift_command_v1.2.0.pack
```

to the WH3 data directory as:

```text
zzz_better_shift_command_steam.pack
```

Do **not** copy `wh3_native_bridge.dll` or `minhook.x64.dll` separately into the game directory; the pack is self-contained.

## v1.2.0 release notes

v1.2.0 is the production consolidation of the tested SC1–SC5 movement line. The release itself adds no new gameplay algorithm beyond the validated SC5 behavior. Its final cleanup:

- renames controller/release identity to v1.2.0;
- disables high-frequency telemetry by default;
- short-circuits debug log construction when telemetry is disabled;
- disables pure test-only generation observation in release mode;
- retains the validated Native Bridge / ContactPair / MASM implementation and ABI.

For the reasoning behind the architecture and the development path from Evidence V3 through SC1–SC5, see [`docs/DEVELOPMENT_HISTORY.md`](docs/DEVELOPMENT_HISTORY.md).

## Third-party component

The self-contained release uses a frozen x64 MinHook runtime. Its license is preserved in `baseline/MINHOOK_LICENSE.txt` and embedded into the generated pack.
