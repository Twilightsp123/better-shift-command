# N1 9.0.3 — state-4 early-exit versus route setup differential

**Date:** 2026-10-10. **Status:** exact-file static evidence; **NO PATCH AUTHORIZED**.

**EXE:** user-provided `Warhammer3.exe`; SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`; image base `0x140000000`. User describes build as WH3 9.0.3, version resource not independently established. Local LLVM disassembly and SHA-pinned read-only test performed.

## New narrow finding: geometry path bypasses route setup

In original state-4 function `0x0311F534`, after a nested flag and geometric comparison:

```asm
0x0311F8AE cmp byte ptr [rsi+0x6C],1
0x0311F8B2 movss xmm0,[r14+0xA8]
0x0311F8BB minss xmm0,xmm8
0x0311F8C2 comiss xmm7,xmm0
0x0311F8C5 jae 0x0311F8E5
0x0311F8C7 mov byte ptr [rsi+0x6C],dil  ; DIL=0 in function entry
0x0311F8CB jmp 0x0311FC5B
```

That identified short-geometric branch **jumps directly to common cleanup** and therefore bypasses later code on the continuing branch. The alternate path at `0x0311F8E5` may perform route-related calls including:
- `0x0311F8FC` -> `0x030F9C5C` and `0x0311F9E2` -> `0x030C2274`;
- `0x0311FC22` -> `0x0312D088` (route-pointer retrieval/wrapper), followed by `0x0311FC27` assigning the pointer into nested `+0x40`;
- `0x0311FC4A` writing nested `+0x6C=1`.

The **relative branch/call targets and exact bytes are verified** for this EXE, not an inferred universal engine behavior. The continuing path has additional guards and does **not always** reach all these calls/writes.

The `0x0312D088` wrapper calls `0x0311D0CC` and then dispatches via `0x0312D0D0`; the obtained pointer is not yet proven to represent speed/velocity.

## Hypothesis, NOT result

Does the geometry-gated route-setup skip cause a later MOVE to lose motion continuity? **Unknown.** The observed early branch clears a nested flag and skips work in this function, but does not directly write a verified desired-speed or unit-velocity field. A forced branch/flag change could break path-object lifetime or create duplicate route objects and is therefore forbidden.

## Next exact static gate

1. Follow the **object identity, lifetime and consumer** of nested `+0x40` output from `0x0312D088`.
2. Locate an instruction that writes a proven **actual speed, velocity target or locomotion reset**; connect this route path to that write by native dataflow or falsify the hypothesis.
3. Compare queued intermediate MOVE vs final MOVE and ordinary RMB; preserve original queue/head/task/ATTACK.
4. Only after causal and ABI/thread safety evidence propose an original-function-local modification, offline differential test, Win64 hook validation and **one** bounded in-game acceptance.

No guessed new Hook address. No code modification, DLL, PACK or Steam upload.

## Bounded offline checks

The reproducible local bundle `BSC_N1_903_state4_path_divergence_20261010.zip` contains `verify_branch.py`, `test_verify_branch.py`, JSON evidence, this report and SHA manifest. **15 exact opcode guards / 5 branch-call edges checked; 6/6 unit tests passed**, including one read of exact SHA-matched EXE. `runtime_patch_authorized=false`. This is code/fixture evidence only, not gameplay testing. The binary itself is not redistributed.
