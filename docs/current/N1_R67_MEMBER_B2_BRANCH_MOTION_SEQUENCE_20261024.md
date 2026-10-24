# BSC R67 — typed B2 member branch and motion timing (2026-10-24)

**Scope:** read-only disassembly and test of the user-provided WH3 executable (SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`, size 232531920, ImageBase `0x140000000`). All addresses are RVAs. **No live-game hook, no Windows runtime patch, no root-cause proof.**

## New exact-code relationship

The B2 member receiver `0x03070A48` saves `RCX=member` as RDI at `0x03070A64` and `RDX=packet` as RBX at `0x03070A6A`. `0x03070B23` loads the current member's VTable. `0x03070B2F` reads `member+0x104`; `DEC/CMP 1/SETBE` gives the following distinct receiver paths:

| State at dispatch | Indirect site | ordinary member VTable `0x03912950` | Verified immediate significance |
|---|---|---|---|
| `member+0x104` equals 1 or 2 | `0x03070B66` calls `+0x100` | `0x030785AC → 0x0316460C` | Direct same-member XYZ and state writes |
| Other member states | `0x03070B9C` calls `+0xE8` | `0x03078268 → 0x03163DC4` | A different action/task path; conditional mode 6–9 cleanup |

Both sites first invoke `0x0312214C` to resolve a coordinate record. They do **not** establish an actual queued Shift hit. The derived member VTable `0x03AD3360` shares `+0x100 → 0x030785AC` but has a **different** `+0xE8 → 0x03077EE4`, so field/method semantics cannot be blindly merged.

`0x030785AC` calls `0x0316460C`; `0x03164626` preserves the same member, `0x03164658` writes member XYZ `+0x88/+0x8C`, and `0x0316466A` writes `+0x90`. This is a concrete conditional position synchronization path, **not** by itself proof of teleportation, Shift causation or a permissible patch. The helper also updates member state `+0x108/+0x155`.

## Timing cross-check

At a conditional branch of ordinary member Tick `0x03086F04`, member bits `+0x108` and `+0xB20` gate `0x03087349 → 0x03059BC8` Steering; it is not called unconditionally on every tick. Separately, ordinary member movement method `0x030592BC` dispatches to `0x03146FF0` or wrapper `0x0310006C`. On one guarded wrapper path, `0x0310014C` calls the integrator **before** `0x03100247` resolves the current `member+0x1E0` reference-aware world goal via `0x03121F54`. Goal writer `0x0311E5DC` has stores `0x0311E6CA` (`+0x1E0`) and `0x0311E6E8` (`+0x1F0`) under its own gates. The later goal read cannot be automatically labelled the goal consumed by the earlier integration.

## Verification and delivery

Local original EXE verification: **64/64 complete instruction bytes, 11/11 direct E8 targets, 2/2 virtual offsets, 8/8 typed VTable entries**. Original-EXE-backed local test suite: **15/15 PASS**. The published minimal public checks skip the real-EXE case when `BSC_WARHAMMER3_EXE` is not set. CI's synthetic checks cannot prove runtime WH3 behavior. Full local original-code excerpts, a separate 15-test checker and history R66 are in separately delivered `BSC_R67_MEMBER_B2_BRANCH_MOTION_SEQUENCE_20261024.zip`; this GitHub commit contains an independently executable smaller 64-pin checker and tests, not the commercial EXE.

**OPEN:** Whether normal queued Shift enters vtable `+0x100` or `+0xE8`; precise producer of `member+0x104` at B2 dispatch; same-task world-goal generation and time alignment; neighbour steering and physical squeezing causality. **Next bounded R68 target:** trace `member+0x104` writer and original queued MOVE's reachability to the two receiver branches. Stop if static evidence cannot establish a genuine Shift-specific instance. Do not patch all model coordinates, `+0x108` or cached actions.

`root_cause_proven=false`; `actual_shift_branch_hit=false`; `native_gameplay_patch_authorized=false`; `main_unchanged=true`.
