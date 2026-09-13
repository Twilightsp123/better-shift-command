# Better Shift Command v1.0.0

Better Shift Command improves queued battle orders in Total War: WARHAMMER III.

## Features

- Smoother handoff between queued movement points.
- Predictive Move -> Attack transitions to reduce the vanilla stop-turn-attack pause.
- `Shift Move... -> Shift Attack -> Shift Move` can leave combat after about 3 seconds of observed melee contact with the intended target.
- `Right-click Attack -> Shift Move` supports the same timed disengagement behavior.
- A normal non-queued right-click always overrides the controller's current plan.

## Requirements

- Total War: WARHAMMER III on Windows x64.
- The supplied `wh3_native_bridge.dll` and `minhook.x64.dll` must be next to `Warhammer3.exe`.
- The `.pack` must be enabled through the game's Mod Manager (or a compatible WH3 mod manager).

## Install

### Easiest

Run `Install_Full.bat` and follow the prompt.

### Manual

1. Copy `data/better_shift_command.pack` to `<WARHAMMER III>/data/`.
2. Copy `wh3_native_bridge.dll` and `minhook.x64.dll` to the game root, next to `Warhammer3.exe`.
3. Enable `better_shift_command.pack` in the Mod Manager.

## Steam Workshop users

If you subscribed to the Workshop item, Steam already provides the `.pack`. Download the **Native Bridge Only** package from GitHub/Nexus and run its installer once.

## Uninstall

Run `Uninstall_Full.bat`, or remove the three files manually. The provided uninstaller only removes files matching this release's hashes and restores backups made by the installer when possible.

## Game updates

The native bridge uses guarded game addresses. A major WH3 update can make the bridge intentionally refuse to start until a compatible bridge update is published. This is a safety feature.

## Source and technical documentation

See the GitHub repository for source code, runtime validation notes, reverse-engineering documentation, and address-relocation guidance.
