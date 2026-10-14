# N1 9.0.3 — Direct member-index/formation-slot binding and geometric crowding counterexample

**2026-10-10 | EXACT EXE STATIC POSITIVE finding, conditional geometry; NOT a working Native patch.**

Research executable SHA256: `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, PE ImageBase `0x140000000`. 9.0.3 is user-labelled; VERSIONINFO unverified. User problem is same unit-card models travelling/turning inconsistently, crowding at chained Shift turns, **not native unit full-stop**.

## What is now traced from actual binary instructions

1. **Member identity order:** Native `0x0301B8E4` loops UnitRoot A-member array `root+0x188` (count `+0x184`) in pointer sequence (`0x0301B93D–0x0301B951`). Per element, `0x0301B946` calls `0x030E0460` which tail-jumps to `0x030C7420`. Its `0x030C7445` calls vector append `0x01325434`. That helper writes to `group_member_vector[count]` at `0x0132547C` or `0x013254B8`, then increases count at `0x013254BC`. **No sorting or distance-optimal identity assignment happens in these verified insertion functions.** Other engine code may still rearrange later; not globally excluded.
2. **Mode-3 target generation:** Constructor-backed formation strategy `0x030CA218` appends **48-byte records** through `0x030BE544` (`0x030CA5B5`). Separate grid-cell mapping stores each appended record's **index** (`0x030CA5E9` and three further grid writers). Helper `0x030DE274` reached at `0x030CAD0E` converts grid-record indices into **pointers to the same record vector** using 16-byte grid-cell stride and 48-byte record stride (`0x030DE2B4–0x030DE2D0`); traverses spatial neighbors via `0x030D1A80`; can mark `record+0x2C=1`. It **does not reorder the output record vector**.
3. **Direct native member/slot binding:** Original `0x030D5490` invokes one group strategy generator at `0x030D54CA`, then in the same loop takes `group_member[i]` (`0x030D54F0`) and `record_vector+48*i` (`0x030D54D9/0x030D54E6`). It constructs the native payload (`0x030D54FC`) with record facing `+0x22` and invokes this member's virtual `+0x368` (`0x030D550F`). **The group fanout in this path pairs equal list/record indices, not an on-the-fly shortest-distance member-target matcher.**
4. As earlier established, original member-local pose updater computes actual XYZ position differences and writes member `+0xE0/+0xE4/+0xE8` derivatives. Distinct instructions/targets can produce opposing member displacement vectors under one unit-level MOVE.

## Concrete falsifiable 180° collision-risk witness

In a **conditional** 3×3 square mode-3 slot arrangement, assume member IDs stay in same group index across the turn, new slot frame rotates 180 degrees, and all members move by synchronized *straight-line interpolation* without avoidance. Old slot `p_i=(x_i,y_i)` gets new `-p_i`, so **every member is at the formation center at progress 0.5**. A translation of the center does not change this convergence (center at the halfway translated origin). At 90 degrees, the same fixture has nine different midpoint positions. This is a mathematically reproducible **potential intra-formation crowding mechanism**, not evidence that WH3 chooses mode3 for ordinary Shift, linearly interpolates its paths or actually collides.

An additional **offline-only alternative** is a one-time, one-to-one mapping of *existing* member identities to *unchanged* destination slots using minimum squared travel distance (Hungarian assignment). On the fixed-center 3×3 /180° case, it preserves all nine goal coordinates but avoids all nine paths collapsing to the center. It changes slot identity and **is not a sanctioned gameplay algorithm yet**; rank identity, stable permutation across ticks, combat orientation, steering, and mixed paths require genuine native tests. Never recompute independent slot permutations each tick or force same velocity/heading.

## Decision and precise next original-code boundary

- **NEW confirmed original boundary:** unit-root member order -> group member vector -> mode-3 48-byte records -> per-index member task fanout. The grid topology postpass at `0x030DE274` is **not** a hidden optimal member-to-slot remapper.
- **First candidate for conditional modification, NOT authorized yet:** the member-index-to-record association *after* group strategy+0x48 generates the records and *before* `0x030D550F` issues them. Do not change the original queue, motor velocity, original path solver or Lua ATTACK.
- **Final causality blockers:** ordinary queued Shift's actual mode; stable model identity across commands; original avoidance/remapping downstream; thread/lifetime/ABI/disable safety; actual WH3 observed model collision. No exact version-guarded Hook is ready, and forcing remapping blindly is unsafe.

## Evidence and deliverables

Reproducible companion archive `BSC_N1_903_SLOT_MAPPING_CAUSAL_20261010.zip` (conversation attachment) contains **44 exact x64 instruction-byte guards, eight E8 targets**, direct EXE SHA and PE executable-section checks; eight bounded original LLVM disassemblies; per-record and group-index evidence JSON; Python **one-shot minimum-cost assignment counterexample**; **22/22 offline tests PASS**, including exact user EXE, 90°/180° geometric controls and wrong-binary rejection; SHA manifest. No game EXE, patching DLL or PACK. **STATIC PASS; OFFLINE PASS; WINDOWS/WH3 NOT TESTED; PLAYABLE FIX NOT COMPLETE.**
## 2026-10-10 cross-check of index stability and native counterpaths

[N1_903_SLOT_IDENTITY_POSITIVE_AND_NEGATIVE.md](N1_903_SLOT_IDENTITY_POSITIVE_AND_NEGATIVE.md) strengthens the **same fanout** `member[i] -> record[i]` proof, but now shows original `0x030E0460` detaches from old group and mode3 `0x030DD3F4` can swap-last on member removal. Different strategies have different removal index policies. This disproves any assumption of immutable group indices across *all* lifecycles; it does **not** establish that next MOVE's newly built group changes index when the UnitRoot source array is stable. Original group post-fanout `0x030E0AA8` also performs status/geometry updates, limiting claims of collision inevitability. Mode3 actual queued Shift activation and actual physical collision still unverified. **No patch authorized**.


## 2026-10-14 新的原生二次朝向/位置修正证据（覆盖旧“直通”推断）

原始 EXE 最新严格审计 `audit_packet_member_retarget.py` 实测 **84/84 opcode+objdump 指令起点、11/11 E8、3/3 类型化成员虚表、1/1 RIP 构造器、3/3 float32 常量** PASS；本地 **10/10** 单元回归通过。详见 `docs/current/N1_903_TYPED_MEMBER_PACKET_RETARGET_20261014.md`。

先前 `record[i]+0x22` 仅是 packet+0x40 **初始朝向种子**：原生 `0x02F5F868 → 0x02F72520 → 0x0307F478` 会根据成员 `+0x2E8` 的对象状态和本人 `+0x984`（满足条件时加 `(s-0.5)*0x4000` 的原生整数转化）覆盖 packet+0x40。原生成员接收器 `0x0306B9F0` 在 packet+0x51 bit2 分支还经 `0x0307F5C8 → 0x0307F690 → 0x0307F4E4` 进行个人位置偏移，并接触 `0x03107FD8` 路线/空间处理。真实成员构造器 `0x0304DAF8` 安装匹配虚表 `0x0390D4F8`，确证相关字段的类型来源。不可将初始阵型几何直接当最终 motor goal，也不可删除原生修正来做所谓 slot 修复。与排队 Shift 实际 state=1 实例身份及挤压因果的连接仍未证明，禁止发布 gameplay patch。
