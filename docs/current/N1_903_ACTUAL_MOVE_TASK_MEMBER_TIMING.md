# N1 9.0.3 — Actually used MOVE task: shared readiness and per-member delayed event

**Exact user EXE SHA256:** `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`. PE image base `0x140000000`. **Only exact-binary static evidence; no playable patch.** This investigation started from **V3-captured native MOVE worker `0x03025D70`**, NOT the separate `0x0302DB44 → 0x030D5490` member fanout, which had zero V3 hits.

## Verified chain

1. `0x03025D70` at `0x030260AF` creates native task `0x02F2C734` with VTable RVA **`0x03ABBE18`**, virtual `+0x10 → 0x02F561E8`. Original per-unit task processor `0x03043520` calls this `+0x10` while processing tasks.
2. The task `0x02F561E8` checks a **shared native route-state object**: `state+0x20==4`, `state+0x24!=0`; one path sets `task+0xA0=1`. Under a different non-ready/one-shot path, if `task+0xA2==0` and `task+0xA4>=5`, E8 at `0x02F564A5` calls **`0x030D52B4`** with group pointer and byte argument zero; then sets `task+0xA2=1`. This is a conditional broadcast, NOT a proven per-soldier Shift waypoint completion rule.
3. `0x030D52B4` loops group `+0x24` members at `+0x28`, calls each member VTable **`+0x360`**. Checked **38 constructor-referenced original member VTables**, and **all 38 resolve this virtual to `0x0306B878`**.
4. `0x0306B878` checks native membership/mode and member-local subobject states. Only when its gates allow, E8 `0x0306B8E7` constructs member-local task **`0x02F5F5AC`**. The new task's VTable `0x03906130` has `+0x08→0x02F736EC` (which jumps to `0x02F6B0F0`) and `+0x10→0x02F83B04`.
5. With broadcast argument zero, the constructor uses float **200.0** and game-global integer **initial value 100** to calculate `ceil(200/100)+1=3`, calls original PRNG **`0x01BA9CD8`** (modulo 3) and adds result **0/1/2 native ticks** to task `+0x44` deadline. The bound may differ if runtime global integer changes. Member code does not necessarily pass all gates or receive an event.
6. `0x02F6B0F0` checks native context `+0x98` current tick against deadline; when ready, issues code **`0x81`** through member virtual **`+0x528`**. Among the same 38 member types, +0x528 maps to `0x03069DA0` for 36, with two special handlers. In the common receiver, `0x03069DA0` constructs/updates a member-local action subobject `+0x328`; it **does not directly write desired velocity or waypoint index** in the examined instruction span.

## Causal implications and firm negative boundary

- Unlike previous mode3 grid simulations, the *actual MOVE-created task VTable* is followed into a group-wide readiness/state branch and member-specific timed actions. One high-level MOVE can therefore have **a shared route-state progression plus asynchronous member action events**.
- These random offsets alone **cannot be identified as the cause** of the real 35–43s progressive Shift crowding: the V3 collector did not hook this task's per-frame virtual, and an action event is not the same thing as changed locomotion. The random delay is bounded to 0..2 native ticks under file-initial scalar, while observed crowding spans seconds. Nonqueued MOVE may use the same path.
- **Do not Hook:** the global PRNG, all-member VTable+0x360, forced `task+0xA0`/shared state4, or blindly erase delayed member status. Those alter unrelated engine lifecycles without proven benefit.
- This closes a concrete **observed execution-path gap**: previous focus `0x0302DB44 → 0x030D5490` was not even captured during the user's ordinary/queued comparison. Future specific repair work must trace the *real task's native local-motion output*, not assume mode3 target slot permutation under the observed mode0 unit.

## Reproducibility

Local complete archive **BSC_N1_903_ACTIVE_MOVE_MEMBER_TIMING_AUDIT.zip** contains `verify_active_move_task.py`, frozen 38 VTable RVAs, `evidence.json`, eight synthetic/EXE tests, Chinese report and SHA256 manifest. On the exact SHA: **21 opcode guards**, **4 E8 targets**, **38/38 member VTable+0x360**, two native task VTables and 36 common +0x528 handlers pass. **8/8 tests PASS**. No WH3 executable redistributed; no game patch produced.

**N1 status:** direct original MOVE task's shared-vs-member event semantics now grounded; **a particular locomotion target/avoidance predicate explaining the observed 35–43s compression has not been located**. Do not call static proof a completed BSC repair.
