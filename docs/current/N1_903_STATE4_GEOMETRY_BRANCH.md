# N1 9.0.3 — state-4 transfer reachability and geometry early-exit candidate

**2026-10-10 | STATIC proof only | no Native patch authorized.**

Target: user-provided `Warhammer3.exe`, SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`; AMD64, image base `0x140000000`. The game's displayed 9.0.3 version was supplied by the user; VERSIONINFO was not independently verified. Read-only LLVM instruction inspection: **25 exact original machine-code guards, 4 decoded relative control-flow edges, 6/6 offline verifier tests (including the target EXE)**. No Windows Hook or WH3 play test.

## Correction: state 4 does not always clear transfer flag

Previous research identified one state-4 entry `0x0311E4B5` that **also** clears `state+0x24` at `0x0311E4B9`. That is *not the only original transition*.

A separate original helper `0x0311EC28`, called from state-2 processing at `0x0311E56E` under nested state conditions, checks `state+0x24` at `0x0311ED2C` and sets `state+0x20=4` at `0x0311ED63` **without any adjacent flag reset**. It can take a side path calling native code `0x0303750C`, and it invokes other helpers, so preservation across *all* indirect calls is not proven.

Thus there exists a **plausible engine-controlled path** that sets state 4 after an existing flag-1 check. We **cannot** assert ordinary queued MOVE reaches `state4 && flag1` from static code alone. Do not force either state or flag.

The two distinct original transitions make any raw “set state=4” or “set flag=1” fix especially unsafe.

## A more precise motion-path research candidate

State-4 handler `0x0311DE74` calls `0x0311F534` at `0x0311DEF2`. The latter reads an inner object via `rsi=[state+0x160]`, derives an XY geometric magnitude (`sqrtss xmm7,xmm1` at `0x0311F7D1`), and in one guarded branch:

```asm
0x0311F8AE cmp byte ptr [rsi+0x6C],1
0x0311F8B2 movss xmm0,[r14+0xA8]
0x0311F8BB minss xmm0,xmm8           ; xmm8 is loaded with 1.0 from RVA 0x0391CBC4
0x0311F8C2 comiss xmm7,xmm0
0x0311F8C5 jae 0x0311F8E5
0x0311F8C7 mov byte ptr [rsi+0x6C],dil  ; DIL was initialized to zero
0x0311F8CB jmp 0x0311FC5B              ; early function return path
```

Native route-rebuild logic separately sets inner `+0x6C=1` at `0x0311FC4A`. This is an instruction-backed, **geometry/flag-conditioned early exit**; it does **not** directly show a change to velocity or desired speed. The length is derived from local geometric vectors, not proven to be distance from a unit to a clicked waypoint. We must not label it terminal-braking or adjust its `1.0` constant without downstream motor dataflow.

## Next required proof before any BSC patch

1. Follow early-exit and non-exit paths of `0x0311F534` to the **same original motor/desired-speed writer**. Demonstrate a *causal* link to stopping, not just a geometric comparison.
2. Establish nested flag `+0x6C` object meaning, normal route refresh vs terminal arrival, and relation to original MOVE command completion.
3. Confirm valid state4+flag1 can survive native helper calls and still allow legitimate same-owner successor MOVE transfer.
4. Check ordinary right-click REPLACE/HALT and ATTACK negative controls. If proof does not support a local change, mark patch NO-GO instead of expanding the Lua Controller.

No change to the EXE, Native Bridge, H8, flags, OrderHead or queued commands. No DLL/PACK. Downloadable offline evidence bundle `BSC_N1_903_state4_geometry_evidence_20261010.zip` contains exact-SHA verifier, 6 tests, JSON report, bounded LLVM disassembly and SHA256 manifest (excluding game EXE).

**N1 status:** new exact native state/geometry control-flow evidence, but original stop-and-go causal predicate and patch ABI/lifetime still **UNPROVEN**.
