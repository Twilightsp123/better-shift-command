# N1 — Native RMB reference: per-member target continuity and spatial projection

**2026-10-10, exact WH3 executable STATIC.** Target SHA256: `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`. All code addresses are RVA. Primary defect remains real observed soldier crowding during **native progressive Shift turns**, not mandatory full stops.

## Verified code-level findings

- RMB non-queue and queued MOVE share the original MOVE constructor `0x030090BC`, worker `0x03025D70`, and may feed the same mode-selected formation target generator; different order-queue semantics do **not** imply a separate normal-RMB soldier locomotion engine.
- Under the inspected `0x030C9A64 → 0x030DBFD4` strategy, first segment calls vtable `+0x38`, later segments call `+0x30 → 0x030DC2B4`, which fetches its own segment reference then invokes **the same** target-emission virtual `+0x38`. This does not prove which strategy the V3 unit actually selected.
- Original `0x030DC0A0` linear target segment calculates tangent/length/projection and carries an inter-target spacing remainder forward through `0x030DC25F–0x030DC270`. **Do not reset phase to zero at every internal leg.**
- Another original segment constructor `0x030C2074` deliberately applies an oriented half-width offset to its reference. An unequal next-leg reference alone is **not** evidence of erroneous discontinuity. Do not force reference coordinates equal.
- The original `0x030DBFD4` underfill path can duplicate its last 48-byte record via `0x030D1F60`; this path is shared across several strategy sinks and need not be Shift-specific. Never blindly delete records or global-hook `0x030D1F60`.
- After member target dispatch the common family reaches `0x03073224 → 0x0315EC98`. Within the inspected candidate branch, `0x0314E9A8 → 0x03150CBC` enumerates spatial support candidates, `0x018325EC → 0x0183B990` tests geometric inclusion, and `0x0314EA2E–0x0314EA62` computes a plane-derived positional scalar using coefficients `+0x6C/+0x74/+0x78/+0x70` before selecting an object. **This does not demonstrate soldier-soldier steering or a velocity detour.** `0x0315EC98` itself can write actor pose `+0x88/+0x90/+0xB0`; that is distinct from per-frame member rate writer `0x0315C1E4`.
- The separate `0x030C6788` same-`+0x80` exclusion is observed in a contact/bitset path, **not yet shown** to implement the movement solver for the user's queued Shift turn.

## Conditional offline differential, NOT WH3 simulation

A bounded `0x030DC0A0` **single-centerline straight-segment** abstraction compared ordinary straight RMB with a gradual Shift-style U-turn approximated by 24 short straight segments. 36 samples / spacing 0.85 / initial phase 0.4, and a descriptive close-opposing target-pair test: long RMB 0 pairs; short RMB can underfill 31 candidates; 90° turn 0; tight U radius 0.4 **21 pairs despite no cloned or duplicate goals**; wide U radius 2.5 0. The near-opposing radius 1 is NOT a native collision radius. This is conditional geometry only; it does NOT include the original multirow 48-byte layout, type-1 curved generator, identity assignment, native avoidance, or real V3 generated targets. **No actual V3 crossing or root cause is claimed.**

## Code and tests

- `maintenance_tools/native_shift_re/rmb_shift_target_continuity.py`: read-only original-EXE SHA verification, 44 opcode/scalar guards, 13 direct E8 targets, four vtable slots, synthetic original-linear-stage comparisons.
- `tests/test_native_shift_re_rmb_continuity.py`: 15 offline tests with the exact original EXE present, otherwise synthetic/negative tests and explicit skip for unavailable private EXE. GitHub Actions N1 contracts PASS (CI has no game EXE).
- The local complete evidence ZIP `BSC_RMB_SHIFT_TARGET_CONTINUITY_20261010.zip` includes tests, original-binary audit JSON, bounded original disassembly for spatial candidates and member pose, synthetic point CSV, Chinese reading notes, SHA256 manifest. User's game EXE is not redistributed.

**Engineering decision:** preserve native queued Shift, original progressive turns, per-segment target spacing and valid reference transforms. No global clone deletion, zero-phase reset, magic clearance parameter, or blanket state-handoff deletion. We have not proven the target records were actually discontinuous/overlapping in V3: do not treat the synthetic crossing as native proof. The next only relevant causal boundary is a **verified original local motion steering/avoidance vector producer and consumer**, compared under normal RMB and queued Shift; member `+0x2E0` may be a follower/attachment reference rather than every actor's motor. No Native Patch is authorized, Windows/WH3 NOT RUN, no user playtest requested.
