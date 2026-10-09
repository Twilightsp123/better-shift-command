# N1 — 9.0.3 original special handoff: MOVE accepts, ATTACK rejects

**Read-only exact-file static evidence; not an executable patch.** Examined user-provided `Warhammer3.exe`: SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, PE image base `0x140000000`. Version 9.0.3 is user-supplied context. No runtime instrumentation, Ghidra database, game test or DLL.

## Verified original VTables and branch

The MOVE constructor `0x030090BC` writes original VTable **`0x0390B4F0`**; the ATTACK constructor `0x03008BC0` writes original VTable **`0x0390AC38`**. The latter occurs on the native ATTACK issuance path `0x03030760` (callsite `0x0303097E`).

| Virtual slot | MOVE type | ATTACK type |
|---|---|---|
| +0x08 | `0x03025D70` | `0x03025788` |
| +0x10 | `0x030440F8` | `0x03044258` |
| **+0x38 successor eligibility** | **`0x008D3350`** (mov al,1; ret) | **`0x008D3330`** (xor al,al; ret) |
| +0x40 current transfer provider | `0x03039FB0` | `0x008D32C0` |
| +0x48 accept transferred native state | `0x03040864` | `0x008D3280` (ret 0) |

In queue processor `0x0304433C` the original instruction path calls current virtual `+0x40` at `0x03044562`, tests that pointer, calls next virtual `+0x38` at `0x03044596`, tests AL, and **only when eligible** increments transferred object's reference count (`0x0304459D`), calls next virtual `+0x48` (`0x030445AB`), pops original ring head (`0x030445B1` -> `0x02F4FD10`) and invokes task cleanup (`0x030445BC` -> `0x02F4FD5C`).

**Strong, limited finding:** this *specific native special-transfer path* can admit a MOVE successor and explicitly rejects the inspected ATTACK successor; it is not a universal MOVE→ATTACK transition. It does **not** prove all queued MOVE→MOVE commands reach it, or that MOVE→ATTACK is broken without BSC. A separate native ATTACK activation path may exist.

## MOVE successor reuses a native state object (not second command issuing)

The real MOVE `+0x48` method at `0x03040864` receives the current transfer object in RDX, updates fields on **the same pointer**, and binds it to the successor MOVE:

```asm
0x030408CF  mov dword ptr [rdx+0x20], 1
0x030408EC  movups [rdx+0x120], xmm0
0x030408F8  movups [rdx+0x130], xmm1
0x030408FF  movups [rdx+0x140], xmm0
0x03040906  mov [r9+0xA0], rdx
```

Original current MOVE `+0x40` provider `0x03039FB0` first requires MOVE `+0xA0` nonnull, native transferred-object `+0x20==4`, flag checks, and group validator. Therefore this is *conditional ownership-controlled state transfer*, not a general shortcut that should be enabled globally. The recipient method sets state to 1 and updates a destination/task payload, but **what these states mean for physical braking/locomotion is still unknown**.

The MOVE `+0x08` work issuer `0x03025D70` maintains the `+0xA0` object, calls a native task/suborder collection allocator `0x02F2FFB0`, and passes parameters to a task constructor `0x02F2C734`. This extends [N1_903_SUBTASK_AND_HANDOFF.md](N1_903_SUBTASK_AND_HANDOFF.md) without establishing desired-speed or arrival behavior.

**Never** force the next ATTACK eligibility to true (its `+0x48` is an intentional noop), directly change the transferred-object state/refcount, mutate OrderHead, or bypass native cleanup. Such shortcuts violate the engine's own lifecycle.

## ATTACK status differs

ATTACK virtual `+0x10` `0x03044258` checks the same auxiliary task-count `+0x240`, but unlike MOVE's simple zero predicate it has additional conditions and possible side effects when zero. Do not treat MOVE's completion rule as interchangeable with ATTACK.

## N1 next decision gates

1. Recover producer, object type and lifetime contract for MOVE `+0xA0`; explain state values 1/4 and group-validation predicate.
2. Trace task constructor `0x02F2C734` and downstream speed/path/steering controls; determine physical deceleration before versus after transfer.
3. Trace **ordinary** MOVE→ATTACK activation outside this special-transfer path; compare normal RMB and target invalidation.
4. Only if native semantics validate an intermediate MOVE condition, propose a minimal original-predicate change. No Native runtime patch authorized now.

## Repeatable byte-level checks

Using exact SHA-gated, read-only PE parsing and executable section mapping: **10 VTable pointers**, **13 instruction byte guards**, **2 verified E8 direct-call targets**. Local synthetic parser tests: **6/6 PASS** (PE mapping, section typing, old/foreign SHA rejection, output protection). This is *static integrity*, not proof of gameplay smoothness, ABI safety or runtime Hook feasibility. Local proof outputs: `BSC_N1_903_special_handoff_evidence.json` and `verify_903_handoff.py`, retained outside GitHub until source is synchronized.
