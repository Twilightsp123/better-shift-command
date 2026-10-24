# BSC R68 — same-build member action-mode provenance (2026-10-24)

**Research-only. No live WH3 tracing, no runtime hook, no gameplay patch.** Exact user's Win64 Warhammer3.exe SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`, size 232531920, PE ImageBase `0x140000000`. Addresses below are RVAs.

## Relationship to prior work
Previous 9.0.3 study `N1_903_MEMBER_MODE_AND_LOCAL_PATH_INDEX.md` already showed `member+0x104` is an **actor action mode**, NOT the Shift waypoint index. However, that report used **another EXE SHA**, so its `0x0307897C` setter RVA must never be transplanted to the present version. R67 on the current version typed B2 receiver `0x03070A48` reading `member+0x104` and choosing member virtual `+0x100` for states 1/2 or `+0xE8` otherwise.

## R68 newly verified in the current binary
- Normal member vtable `0x03912950+0xE0` and derived member `0x03AD3360+0xE0` both resolve to **`0x0307D9C0`**; their `+0xE8` implementations differ. This establishes typed membership for the mode setter, not equality of all member methods.
- Setter `0x0307D9C4` reads `member+0x104` and `0x0307D9CA` compares requested EDX. Identical mode returns. `DEC EAX; CMP EAX,1` plus `TEST EDX,EDX` means **old mode 1 or 2 → requested mode 0** conditionally executes `0x0307D9D9 AND [member+0x23C],EDX` and `0x0307D9DF AND [member+0x1C8],EDX` (both clear to zero). `0x0307D9E5` writes the requested mode to `+0x104`; `0x0307D9F8` directly calls **`0x0307DB60`** for further state processing.
- Four **bounded example sources, NOT an exhaustive caller inventory:** `0x03071ECF` requests 3 under controller/state conditions; `0x0307FACC` requests 2 if an associated `member+0x2E8` controller passes conditions; `0x0316143F` requests 0 or 1 based on a boolean after same-member position and motion-state updates; `0x031647A4` optionally requests 0 after same-member XYZ and flag writes.
- Distinct member-local modes and route-level shared commands can coexist legitimately. **Neither the modes nor the reset are established as the cause of Shift crowding.** R67's B2 receiver reads existing per-member mode but this investigation does not establish the within-one-Shift-task temporal identity between a mode change, B2 dispatch, steering and integrator.

## Verification
Real-executable local audit: **56/56 original instruction byte pins and true GNU objdump instruction starts**, **8/8 constructor-associated vtable slots**, **1/1 direct E8 target**; 17/17 offline unit tests including the real original EXE. Public GitHub tests are intentionally synthetic/contract tests with a private-EXE SKIP; green CI cannot claim WH3 runtime or a newly proven causal link.

`maintenance_tools/native_shift_re/r68_member_mode_pins.json` carries all 56 exact opcode pins. `audit_r68_member_mode.py` can verify SHA, pins, vtable entries and direct-call identity when run with a privately held EXE; optional full local disassembly/test evidence and R67 history are in the separately delivered `BSC_R68_MEMBER_MODE_TRANSITION_STATIC_20261024.zip`. The EXE, third-party DLL and player pointer logs are not distributed.

**Next bounded R69 question:** one original-code continuation from `0x0307D9C0 → 0x0307DB60` to the nearest `member+0x23C/+0x1C8` reader, then stop and record whether mode-transition reset can actually affect motion/goal timing. No en-masse mode writes, no cache clearing, no Lua reissue, no gameplay patch.

`root_cause_proven=false`; `actual_shift_transition_hit=false`; `live_probe_authorized=false`; `native_gameplay_patch_authorized=false`; `main_unchanged=true`.
