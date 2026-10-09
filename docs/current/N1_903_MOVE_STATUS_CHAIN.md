# N1 — WH3 9.0.3 MOVE-object completion-status trace

**Static evidence only; no patch authorized.** Target EXE is user-provided 9.0.3-labelled Warhammer3.exe; SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`. Preferred image base `0x140000000`. Version resource has not been independently verified.

## Exact MOVE construction chain

- Original candidate Native MOVE issuer **RVA 0x030323C8** passes `root+0x278` into original allocator **0x02F50410** and gets a ring slot.
- It passes `slot+0x18` into constructor **0x030090BC**, callsite `0x030326E4`.
- Constructor invokes base constructor **0x03008814** and writes the original object's VTable pointer to **RVA 0x0390B4F0** (`0x030090D1`–`0x030090D8`).
- Base constructor initializes `object+0x18` from `slot+0x10`, initializes `object+0x20=0`, and marks `slot+0x118=1`. All are observed opcode writes.
- Actual original 9.0.3 VTable entries: virtual `+0x08` -> **0x03025D70**; virtual `+0x10` -> **0x030440F8**.

## Concrete virtual completion-status branch

The MOVE object's virtual `+0x10` implementation is a short native function:

```asm
0x030440F8  mov rax, [rcx+0x18]
0x030440FC  cmp dword ptr [rax+0x240], 0
0x03044103  sete al
0x03044106  mov byte ptr [rcx+0x20], al
0x03044109  ret
```

Thus this MOVE type's status byte at `object+0x20` is set from whether a *related state's* `+0x240` field is zero. **The native meaning of `+0x240` is NOT YET PROVEN.** It may be a subtask/count field, but it is not yet evidenced as path arrival, physical speed or a terminal stop.

The order-state processor **0x030433B0** calls **0x03043424** to update the selected slot; the latter makes conditional virtual calls at `+0x08` and `+0x10` on the object at `slot+0x18`. When that object is the recovered MOVE type, the virtual `+0x10` dispatch is to **0x030440F8**. Afterward **0x030433B0** checks `slot+0x118==1` and `slot+0x38!=0` (alias `object+0x20`), and under that branch calls the proven ring-pop routine **0x02F4FD10** at callsite **0x03043406**.

```text
Native MOVE issue 0x030323C8
 -> original order allocation 0x02F50410
 -> MOVE constructor 0x030090BC -> VTable 0x0390B4F0
 -> conditional unit/queue state processing 0x030433B0
    -> slot state update 0x03043424
       -> MOVE virtual [+0x10] 0x030440F8
          -> status = (related_state[+0x240] == 0)
    -> if slot valid & status != 0: queue pop 0x02F4FD10
```

This **establishes a native MOVE-object status propagation path toward original queue progression** for the identified object type; it does **not** establish that every vanilla Shift MOVE takes this path, what produces the count-like field, when terminal braking occurs, or how the next attack/move is activated. Do not directly set the status flag, write the head or bypass object cleanup.

## Next investigation

1. Trace writer/readers of the *specific* object behind `MOVE object+0x18`, particularly `related_state+0x240` and lifecycle.
2. Trace MOVE virtual `+0x08` **0x03025D70** to original steering, order execution, braking and path reset decisions.
3. Determine whether completion occurs before or after physical deceleration and whether the original next MOVE is already eligible; inspect target death, REPLACE and nonqueued RMB negative controls.
4. Repeat native VTable construction and status trace for the original ATTACK type.

**Evidence grade:** exact-binary static opcode and VTable pointer/dataflow chain; original movement/ATTACK behavior and safe Hook ABI are **not verified**. See [N1_903_ORDER_LIFECYCLE_STATIC.md](N1_903_ORDER_LIFECYCLE_STATIC.md) and [WH3_9_0_3_NATIVE_PATCH_DESIGN.md](WH3_9_0_3_NATIVE_PATCH_DESIGN.md).
