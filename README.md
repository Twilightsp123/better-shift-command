# Better Shift Command

Smooth queued movement, predictive Move->Attack handoffs, and timed disengagement for Total War: WARHAMMER III.

**Current release baseline:** v1.0.1 / Controller P2B-HF5 derivative 0.2.6 / Native Bridge 0.5.1-per-kind-calibration.

## Players

**Windows x64 only.** The Steam Workshop build is now self-contained: subscribe and enable the mod. On battle load, the `.pack` verifies/materializes the embedded `wh3_native_bridge.dll` and `minhook.x64.dll` next to `Warhammer3.exe`. If an older Bridge is present, the new pack replaces it when the embedded bytes differ, so Workshop updates can carry Native Bridge updates as well.

The GitHub repository remains the technical/source-of-truth archive. Standalone release packages may still be published for manual installation or troubleshooting, but Steam users no longer need a separate Native Bridge download for the self-contained build.

## What v1.0.1 fixed

- **Per-command-kind calibration:** MOVE can arm after a natural accepted MOVE without first requiring ATTACK calibration. ATTACK still requires its own accepted ATTACK evidence before scripted ATTACK issue.
- **Native Move canonicalization tolerance:** after strong issue/source/unit/revision identity closes, a small CA rewrite of the accepted destination no longer kills the whole Controller with `OWN_MOVE_PAYLOAD_MISMATCH`; the accepted native destination becomes authoritative. Non-finite payloads still fail closed.
- **Validated v142-family build requirement:** the release builder refuses a silent v143-only toolchain. A v143 TESTFIX A build loaded but failed `MH_CreateHook`; TESTFIX B built with the original validated v142 family restored real-game Hook installation.
- **Self-contained Steam deployment:** Bridge + validated MinHook are embedded in the PFH5 pack and materialized only when missing or byte-different.
- **Production logging cleanup:** per-order dispatch/ACK, plan, cancel and hold-success traces are debug-only; fatal/refusal/deployment-update diagnostics remain.

## Developers / future maintainers

- **Returning after months?** Read [`docs/00_CURRENT_STATUS.md`](docs/00_CURRENT_STATUS.md), then [`docs/01_COLD_START_RECOVERY.md`](docs/01_COLD_START_RECOVERY.md).
- **CA update broke native guards?** Read [`docs/native/ADDRESS_RELOCATION_PLAYBOOK.md`](docs/native/ADDRESS_RELOCATION_PLAYBOOK.md) and [`docs/native/HOOK_AND_GUARD_TABLE.md`](docs/native/HOOK_AND_GUARD_TABLE.md).
- **Need the v1.0.1 Steam deployment model?** Read [`docs/deployment/STEAM_SELF_CONTAINED.md`](docs/deployment/STEAM_SELF_CONTAINED.md).
- **Want to understand what was reverse engineered and why public Lua was insufficient?** Read [`docs/native/REVERSE_ENGINEERING_HANDOFF.md`](docs/native/REVERSE_ENGINEERING_HANDOFF.md).
- **Do not repeat disproved approaches.** Read [`docs/history/FAILED_APPROACHES.md`](docs/history/FAILED_APPROACHES.md).

## Architecture

CA public Lua -> reverse-engineered native semantics -> guarded Native Bridge -> appendable HF5-derived Lua Controller.

The Native Bridge exists because the public battle Lua surface does not reliably expose queued-vs-replace semantics, exact revision/self provenance, or the durable mixed command chronology required after scripted takeover. Public Lua is still used for engagement state where it is appropriate.

The v1.0.1 Controller does **not** replace WH3 pathfinding or locomotion. It chooses when to hand the next Move/Attack back to CA's native systems.

## Repository map

```text
src/lua/                   production Controller source + self-contained template
src/native_bridge/         Bridge C++ source + tests/tools
scripts/docs               (none; documentation is under docs/)
docs/                      authoritative recovery / RE / controller / deployment contracts
release/v1.0.0/            historical v1.0.0 Workshop pack
release_assets_for_upload/ historical v1.0.0 GitHub/Nexus upload assets
tools/release_v1.0.1/      reproducible v1.0.1 self-contained Steam builder
third_party/               third-party license notices
```

## Safety / compatibility

Windows x64 only. Native hooks are byte-guarded. On an incompatible CA update, the Bridge is designed to refuse unsafe activation rather than blindly use stale addresses.

The self-contained loader compares exact bytes before writing native components. Normal battle loads keep identical files; an updated Workshop pack can replace an older embedded Bridge when the payload changes.

## License

Project license is intentionally not selected in this archive. Choose it before granting general reuse rights. MinHook retains its own BSD license under `third_party/`.
