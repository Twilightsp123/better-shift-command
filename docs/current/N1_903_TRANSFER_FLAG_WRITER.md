# N1 9.0.3 — original MOVE transfer flag writer and native callback gate

**Research status:** exact-EXE static evidence only, no executable behavior modified.

User-provided EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`; preferred image base `0x140000000`. 9.0.3 label from user, VERSIONINFO not independently authenticated. Analysis uses read-only LLVM machine disassembly. **68/68 selected byte guards, 9/9 conditional branch targets, 7/7 synthetic verifier tests PASS.** Not WH3 gameplay/Windows Hook evidence.

## Resolved the earlier missing writer

We previously found a native MOVE transfer provider `0x03039FB0` that only returns its current state when:
- `MOVE+0xA0` state pointer exists;
- `state+0x20 == 4`;
- **`state+0x24 != 0`**;
- `state+0x158` exists and a group validator permits it.

The native state driver `0x0311DE74` enters several branches, including a state-1 rebase that invokes **`0x0311E80C`**. In that callback, RSI holds the state object; the original instructions now identify **an actual writer** at `0x0311EB10`:

```asm
0x0311EAC7 call 0x0310F560          ; native validation/processing, meaning unknown
0x0311EACC mov r8b, al              ; preserve return flag
0x0311EAD4 test al, al
0x0311EAD8 cmp [rbx+0x4E4], 2       ; branch gate, field meaning unknown
0x0311EAE0 lea r9d, [rcx-1]         ; r9d=1 on that branch
0x0311EAE4 mov dl, r9b             ; dl=1 on that branch
0x0311EAE9 mov dl, dil             ; alternate dl=0
0x0311EAEC mov r9d,1
0x0311EB04 test r8b,r8b
0x0311EB07 je 0x0311EB10
0x0311EB09 test dl,dl
0x0311EB0B jne 0x0311EB10
0x0311EB0D mov dil,r9b             ; set 1 only if result and dl gate permit
0x0311EB10 mov byte ptr [rsi+0x24], dil
0x0311EB14 cmp dil,r9b
0x0311EB17 jne 0x0311EBD8
```

This proves `+0x24` is a **result of a conditional original native validation path**, not a distance parameter that BSC can safely tune.

## Important next-state distinction

- From the accepted `+0x24=1` branch, the original callback can assign **`state+0x20=2`** at `0x0311EBC2`.
- Separate exit paths assign **`state+0x20=4`** at `0x0311EC0E`.
- Another existing native state-4 writer `0x0311E4B5` explicitly **clears `+0x24`** at `0x0311E4B9`.

**Therefore it would be false to claim the first observed state=4 automatically makes a MOVE eligible for special transfer.** The exact history/path that establishes *both* state=4 and flag=1 remains unproven; the callback is complex and other paths could preserve prior flags.

The native callback compares two pairs of floats with group-associated bounds at `+0xD0/+0xD4/+0xD8/+0xDC`. These are **candidate spatial validation checks**, not yet proven arrival radius, braking distance or locomotion speed.

## Nearby native state-machine/rebase observations

- `0x0311DE74` dispatches on state+0x20 values 0,1,2,3,4.
- Successor MOVE `0x03040864` writes state=1 and next task payload at `+0x120/+0x130/+0x140`.
- State 1 branch `0x0311E578` transfers pending payload into current state `+0x60..` and `+0xA0..`, then calls `0x0311E80C`.
- Outgoing and incoming MOVE both use scalar accessor `0x0301C1B4`, with a mode-dependent source. It is a consistency/coordinate-reference candidate, **not** a proven speed/timing parameter.

## N1 remains open: which exact original code causes visible stopping?

Next inspect `0x0310F560` and its downstream native helpers; determine what its return means, whether `state+0x24` is ever *reused in state=4*, and which original native motion/path writer causes braking. Compare an intermediate queued MOVE and terminal/nonqueued MOVE in the original control flow. ATTACK remains separate through its ordinary head activation; do NOT force special ATTACK transfer.

**No patch authorized:** do not set `state+0x20`, `+0x24`, order head, virtual eligibility, task count, reuse tolerance, refcounts or write original queue data. Byte-guard proof does not establish runtime physics or thread safety.

Complete offline artifact (separately supplied): `BSC_N1_903_state_rebase_bundle_20261010.zip` contains exact-SHA read-only verifier, synthetic tests, bounded disassembly extracts, detailed state-machine report, machine-code guard JSON, evidence JSON and SHA manifest (no EXE).
