# N1 — 9.0.3 Native MOVE state-machine rebase and eligibility conflict

**Date:** 2026-10-10. **Status:** exact-file **static instruction-level** finding only; no native patch authorized.

**EXE:** user-provided Warhammer3.exe, SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`; preferred image base `0x140000000`. WH3 9.0.3 is the user-supplied version label; VERSIONINFO not independently authenticated. Read-only LLVM disassembly. **44/44 selected machine-code guards and 5/5 relative branch targets checked**; 7/7 synthetic verifier-tool tests PASS. None proves game physics or hook stability.

## State dispatcher recovered

Function `0x0311DE74` reads state object `+0x20` and has original explicit cases:

| State | Basic-block RVA |
| --- | --- |
| 0 | `0x0311E6F8` |
| 1 | `0x0311E578` |
| 2 | `0x0311E462` |
| 3 | `0x0311E14C` |
| 4 | `0x0311DEE1` |
| other | `0x0311E7E0` exit |

These **must not** be called game states such as "moving"/"arrived"/"stopped" until their motor/path side effects are independently recovered.

### Exact safety distinction: entering 4 does not necessarily allow handoff

Under one original branch, `0x0311E4B5` writes `state+0x20=4` **and** `0x0311E4B9` clears `state+0x24=0`, then `state+0x28=2`.

But current MOVE's special state-transfer provider `0x03039FB0` requires **both** `state+0x20==4` (instruction `0x03039FC0`) **and** `state+0x24!=0` (`0x03039FC6`), plus `state+0x158` and group checks. Therefore merely forcing 4 would **not** establish valid eligibility and would risk bypassing original object lifetime. We still need to trace which writer can set `+0x24=1` under valid conditions.

## Original successor MOVE rebase is two-stage

The successor's original virtual receiver `0x03040864` uses the same transferred state object:
- `0x030408CF`: write `state+0x20=1`.
- `0x030408EC`, `0x030408F8`, `0x030408FF`: write next MOVE payload to `state+0x120/+0x130/+0x140`.
- `0x03040906`: bind this exact state pointer to successor `MOVE+0xA0`.

In state **1** branch of `0x0311DE74`, native code copies payload `+0x120/+0x130` to current-state `+0x60/+0x70` and `+0x80/+0x90`. Then instructions `0x0311E5FA–0x0311E618` copy three dwords:

```text
state+0xA0 <- state+0x140
state+0xA4 <- state+0x144
state+0xA8 <- state+0x148
```

A further native call `0x0311E80C` occurs before the state-1 path checks `state+0x24==1` at `0x0311E63B`. This confirms a **staged original state adoption and payload materialization**, not an independent BSC command scheduler. It does **not** prove motion continuity or a reset of velocity.

## Shared scalar source, with a mode-dependent branch

Both current MOVE's reuse check (`0x03025DD2`) and successor receiver (`0x030408AF`) call the exact same scalar accessor **`0x0301C1B4`**.

That accessor checks `MOVE+0x9A` bit `4`. When set it returns float `MOVE+0x80`; otherwise it follows `MOVE+0x10 -> +0x08 -> +0x270 -> +0x40`. The successor also uses related group floats `+0x1D0/+0x1D4` and a binary constant at `0x0391CBC8` while constructing transferred `+0x140..` payload.

The current MOVE reuse path calculates a scalar difference approximately `accessor_value - (state_float_A0 - state_float_A4)`, checks original constants at `0x0391CBC0/0x0391CCFC`, and can release its old state if mismatched. The relationship between successor `+0x140` writes, later state-1 rebasing to `+0xA0`, and current-MOVE reuse tests is now instruction-backed. **The physical meaning of the scalar and the ~0.01 constant is NOT proven** (not safe to describe as speed/time/arrival distance).

## Consequences for BSC and the next static proof

- The original engine *already supports* a two-stage state reuse mechanism for some MOVE successors.
- A simple patch setting `state=4`, `flag=1` or zeroing task counters would bypass original safety gates; **forbidden**.
- Highest-priority outstanding edge: where/why `state+0x24` becomes nonzero for transfer-eligible state 4, and which original path/motor function applies speed/path changes after state-1 rebase.
- Second priority: compare that eligible route to the ordinary queued MOVE completion and native ATTACK activation; avoid conflating special MOVE inheritance with normal ATTACK.
- No new RVAs proposed for direct patching. No EXE writes, DLL, PACK or gameplay tests performed.

**Repro:** local exact-SHA read-only `verify_903_state_rebase.py` checked 44 selected instruction guards plus five computed near conditional branch destinations; 7/7 synthetic tests passed. See separately supplied complete `BSC_N1_903_state_rebase_bundle_20261010.zip` (includes bounded disassembly, JSON evidence, verifier, tests and SHA manifest, no EXE). Tool successes are only **STATIC/OFFLINE**, not WINDOWS/WH3 proof.
\n**Follow-up 2026-10-10:** [N1_903_TRANSFER_FLAG_WRITER.md](N1_903_TRANSFER_FLAG_WRITER.md) resolves a native writer for `state+0x24`, with conditional validation output and separate state-2/state-4 paths. This does not prove reachable `state4 && flag1`. Full local research bundle now checks **68 exact instruction guards, 9 branch targets and 7 synthetic tool tests**.\n
**Follow-up correction (2026-10-10):** [N1_903_STATE4_GEOMETRY_BRANCH.md](N1_903_STATE4_GEOMETRY_BRANCH.md) proves that state4 is also written at `0x0311ED63` on a *different* path with no adjacent `state+0x24` clear. This prevents the mistaken universal conclusion that state4 always clears the flag; still no runtime proof of safe state4+flag1 handoff. State4 handler `0x0311F534` contains a geometric flag-conditioned early return; this is **not yet a proven braking branch**.
