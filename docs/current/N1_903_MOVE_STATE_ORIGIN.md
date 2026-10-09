# N1 — WH3 9.0.3 native MOVE state-object origin and transfer validity gate

**Status:** exact-file static code evidence; **NOT a playable patch**.  
**EXE SHA256:** `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`. User labels build as WH3 9.0.3; VERSIONINFO was not separately checked. Image base `0x140000000`.

## Key finding: original MOVE+0xA0 is populated through auxiliary-task writeback

We can now link the previously recovered original MOVE `+0x40` transfer provider's state pointer `MOVE+0xA0` to its **producer**, not just a consumer. In original MOVE `+0x08` (`0x03025D70`):

```asm
0x03025DD7 lea r14, [rbx+0xA0]     ; writeback address, rbx is MOVE
0x0302608D mov [rbp-0x70], r14     ; store into task-init data
0x03026091 call 0x02F2FFB0        ; allocate auxiliary task
0x0302609F lea r9, [rsp+0x40]     ; task-init data pointer
0x030260AF call 0x02F2C734        ; task constructor
```

The stack correspondence is **exactly instruction-derived**, not a guessed struct alias. If entry RSP is `S`, the original prologue gives `rbp=S-0xB8` and `rsp=S-0x1B8`. Thus `[rbp-0x70]` and `[r9+0x50]` both address `S-0x128`. The task constructor `0x02F2C734` calls a copy helper `0x02F2C834`, which copies input `+0x50` into `task+0x80` (QWORD at `0x02F2C8A7–0x02F2C8AB`). The resulting `task+0x80` contains **the address of the MOVE object's pointer field**, not the state object.

When its guarded initialization reaches `0x02F41644` (call at `0x02F2C81B`), native code:

```asm
0x02F41651 cmp qword ptr [rcx+0x80], 0
...
0x02F41669 call 0x0310ED2C        ; obtains original state object
0x02F4166E mov rcx, [rbx+0x80]     ; &MOVE+0xA0
0x02F41675 mov [rcx], rax          ; MOVE+0xA0 = engine state object
```

For a null task+0x80, it stores the returned pointer in local `task+0x98` instead (`0x02F4167F`). **The exact constructor/initialization branch is conditional; this does not prove every normal Shift MOVE acquires or retains such a pointer.**

## State enumeration: creation, eligible readiness and adoption

- Native allocator `0x0310ED2C` invokes original object constructor `0x030EE850`, which initializes `state+0x20=0` at `0x030EE88D`.
- The native state controller `0x0311DE74` includes a branch `0x0311E4A2` testing a state-related pointer. When null, `0x0311E4B1–0x0311E4B5` computes 4 and writes `state+0x20=4`. This proves a native path **produces** 4, not that 4 means physically moving or stopping.
- As shown in [N1_903_MOVE_VS_ATTACK_TRANSFER.md](N1_903_MOVE_VS_ATTACK_TRANSFER.md), successor MOVE `+0x48` at `0x03040864` receives that existing object, writes `state+0x20=1` (`0x030408CF`), updates payload, then writes it to successor `MOVE+0xA0` at `0x03040906`.
- Meanings of 0,1,4 and full thread/refcount/lifetime invariants remain **OPEN**.

## Separate native rejection gate: prior state is *not* retained unconditionally

Before submitting another auxiliary task, MOVE `+0x08` loads an existing `MOVE+0xA0` and can detach it. It tests `transfer+0x25`, calls `0x0311C634` and compares a scalar derived from `0x0301C1B4` with `transfer+0xA0/+0xA4`. The byte-level comparison uses original constants `0.0` (RVA `0x0391CBC0`) and approximately `0.01` (`0x0391CCFC`). The code compares an absolute difference and, if invalid, decrements `transfer+0x18` at `0x03025E35` and clears `MOVE+0xA0` at `0x03025E39`.

**Do not call this scalar elapsed time, arrival distance, physical speed, or a recommended tuning threshold without tracing its producer.** Its relationship to terminal braking is unknown. It is a native consistency/reuse gate.

Moreover, current-MOVE transfer provider `0x03039FB0` requires: pointer at `MOVE+0xA0`, `state+0x20==4`, `state+0x24!=0`, `state+0x158!=0` and group validation through `0x02D63794` (which checks group flags at `+0xA08` and sometimes `+0x928`). The existing handoff is therefore **far more conditional than “if next command MOVE, transfer state.”**

## Consequences for BSC

1. **Positive:** an original-engine MOVE task can obtain, retain, release and hand off original state without a BSC second command executor. This is a concrete original-code mechanism to investigate.
2. **Safety limitation:** clearing/overriding `MOVE+0xA0`, forcing `state==4`, bypassing group/consistency validation or changing reference counts risks native task lifetime and collision/formation semantics. **None is approved.**
3. **Critical remaining question:** do ordinary queued intermediate MOVE commands fail the transfer preconditions unnecessarily, or are these conditions required by native movement execution? Determine this before proposing a conditional patch.
4. **Separate ATTACK:** this particular successor-transfer path rejects ATTACK (original VTable +0x38 returns false), so ordinary native queued MOVE→ATTACK activation still requires separate tracing.

## Reproducibility and status

Against the exact SHA-matched original EXE, a local read-only evidence script checked **25 machine instruction-byte guards** and the two scalar constants. **8/8 offline tests PASS** for exact build gate, fields, non-executable section rejection and read-only evidence output. The accompanying local research bundle includes script, tests, JSON evidence, ten bounded LLVM disassembly extracts, SHA manifest and reports; the EXE is not redistributed. These are tool/byte checks only, not WH3 behavior tests.

**N1 remains OPEN:** original braking/desired-speed/route-reset causality, ordinary queued ATTACK handoff and proven narrow patch eligibility have **not** been established. No Hook, DLL, PACK or Steam release has been made.