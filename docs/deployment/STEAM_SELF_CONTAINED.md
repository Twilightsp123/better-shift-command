# Steam Self-Contained Windows x64 Deployment

## Why this exists

v1.0.0 required Steam to provide the `.pack` while users separately installed `wh3_native_bridge.dll` and `minhook.x64.dll` next to `Warhammer3.exe`.

v1.0.1 adopts the established WH3-style native-module deployment pattern: native PE bytes are embedded in Lua payload files inside the PFH5 pack, materialized at battle load, then loaded through the existing Lua C-module entry point.

This changes deployment, not the Controller's pathfinding model: CA still owns locomotion/pathfinding.

## Pack contents

Generated PFH5 contains:

```text
script\battle\mod\better_shift_command.lua
script\better_shift_command\bin\bridge_Windows_NT-x64.lua
script\better_shift_command\bin\minhook_Windows_NT-x64.lua
script\better_shift_command\licenses\MINHOOK_LICENSE.txt
script\better_shift_command\licenses\THIRD_PARTY_NOTICES.txt
```

Each binary payload Lua file returns the exact prebuilt PE bytes as a Lua string.

## Battle-load flow

```text
battle loads Controller
-> read embedded MinHook payload
-> compare with .\minhook.x64.dll
-> keep if byte-identical, otherwise write + verify
-> read embedded Bridge payload
-> compare with .\wh3_native_bridge.dll
-> keep if byte-identical, otherwise write + verify
-> package.loadlib(.\wh3_native_bridge.dll, luaopen_wh3_native_bridge)
-> Bridge ABI/version checks
-> Controller starts in same battle
```

The DLL is not compiled at runtime. It is materialized from exact bytes that were compiled during the release build.

## Workshop updates

If a user already has an older Bridge:

```text
Steam updates .pack
-> next clean game launch / battle load
-> embedded Bridge bytes differ from disk
-> NATIVE_EMBED_WRITE
-> exact-byte verification
-> current Bridge loads in that same battle
```

Therefore Workshop can update old users' native Bridge automatically.

Do not design around hot-replacing a DLL already loaded in the same running `Warhammer3.exe` process. The supported update path is: exit game -> Steam update -> relaunch -> enter battle.

## Security / transparency

The self-contained format is a deployment mechanism, not a method to hide native code. Source, build recipe, MinHook license and native documentation remain public in this repository.

## Build

See `tools/release_v1.0.1/README.md`.
