# Better Shift Command

Smooth queued movement, predictive Move->Attack handoffs, and timed disengagement for Total War: WARHAMMER III.

**Current validated baseline:** v1.0.0 / Controller P2B-HF5 0.2.5 / Native Bridge 0.5.0.

## Players

Use the GitHub/Nexus release package. Steam Workshop distributes the `.pack`; the native bridge files must be installed next to `Warhammer3.exe` once.

## Developers / future maintainers

- **Returning after months?** Read [`docs/00_CURRENT_STATUS.md`](docs/00_CURRENT_STATUS.md), then [`docs/01_COLD_START_RECOVERY.md`](docs/01_COLD_START_RECOVERY.md).
- **CA update broke native guards?** Read [`docs/native/ADDRESS_RELOCATION_PLAYBOOK.md`](docs/native/ADDRESS_RELOCATION_PLAYBOOK.md) and [`docs/native/HOOK_AND_GUARD_TABLE.md`](docs/native/HOOK_AND_GUARD_TABLE.md).
- **Want to understand what was reverse engineered and why public Lua was insufficient?** Read [`docs/native/REVERSE_ENGINEERING_HANDOFF.md`](docs/native/REVERSE_ENGINEERING_HANDOFF.md).
- **Do not repeat disproved approaches.** Read [`docs/history/FAILED_APPROACHES.md`](docs/history/FAILED_APPROACHES.md).

## Architecture

CA public Lua -> reverse-engineered native semantics -> guarded Native Bridge -> HF5 Lua Controller.

The native bridge exists because the public battle Lua surface does not reliably expose queued-vs-replace semantics, exact revision/self provenance, or the durable mixed command chronology required after scripted takeover. Public Lua is still used for engagement state where it is appropriate.

## Repository map

```text
src/lua/                 production Controller source
src/native_bridge/       frozen Bridge C++ source + tests/tools
docs/                    authoritative recovery / RE / controller contracts
release/                 Workshop production pack
release_assets_for_upload/ GitHub/Nexus binary release assets
third_party/             third-party license notices
```

## Safety / compatibility

Windows x64 only. Native hooks are byte-guarded. On an incompatible CA update, the bridge is designed to refuse unsafe activation rather than blindly use stale addresses.

## License

Project license is intentionally not selected in this template. Choose it before public source publication. MinHook retains its own BSD license under `third_party/`.
