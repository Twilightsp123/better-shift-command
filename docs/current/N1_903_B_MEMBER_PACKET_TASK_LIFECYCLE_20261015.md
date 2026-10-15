# BSC N1 — 第 3 轮：普通 B packet 与成员内联任务生命周期

**原始 EXE 静态验证：84/84 机器码与指令起点、23/23 E8、8/8 类型化虚表；本地 11/11 回归通过（包含原始 EXE）。**

## 主要发现

1. 普通 B 发包的具体调用者 `0x0326A3A0` 通过不同原生条件构造出 **`0x07` 或 `0x0E`** 的 packet flag，二者都缺 `0x20`。不能把 `0x02F5F8DC` 错称为固定发出 `0x06`；也不能默认同一兵牌两人同时得到不同标志。
2. 在 mode helper 为零且 flag 不含 `0x20` 时，`0x0306B9F0` 清理并安装 **`member+0x4A8`** 的内联任务，其 holder 是 **`member+0x490`**，有效标记是 **`member+0x5C0`**。这些不同于 `member+0x328` 动作槽。
3. 任务真实虚表 `0x03905E18+0x10=0x02F83B24`。条件性分支能通过具体成员的虚方法 `+0x5B0/+0x580/+0x568` 进入 **`member+0x328`** 子动作更新，但仍没有证明最终 **`member+0x1E0`** 主运动目标改变，也没有证明这些路径在玩家 Shift 折返时实际命中。
4. 在 `0x03081EB4` 的成员更新中，检测有效位后调用的是该任务 **virtual+0x80**，不是上面的 **+0x10**。因此真实 +0x10 调度调用点仍待类型化查证。
5. 构造器 `0x02F5F7C8` 还有 `0x02ECA999`、`0x02F448FC` 两处不同对象布局的已验证调用；**不能全局修改它来模拟 Shift 专用修复**。

**新增原始机器码正证据（本轮继续）：** `0x03905E18+0x80 = 0x008F4DD0` 只取 `task+0x90` 的 bit `0x10`（`0x008F4DD0/0x008F4DD7/0x008F4DDA`）。`0x02D99F74` 将输入 packet 的 bit `0x10` 复制至 task 字段；`0x03082353/0x03082356` 在成员 Tick 比较其返回值是否为 1。因此**对刚构造且标志未发生后续变化的普通 B `0x07/0x0E` 任务，此查询返回零**。这一点是具体位逻辑，不代表成员不会移动，也不代表与 queued Shift 实机发生次序已接通。

## 必须保留的证据边界

上面全部是固定 SHA 原始机器码与离线分支反例。尚未完成同一 queued inherited MOVE `state=1` 的真实群组和成员身份连接；普通 B 虚表 `0x03AE00E8` 不能与继承大任务 B 虚表 `0x03AE0128` 混为同类；没有 gameplay patch，没有 Windows 游戏测试，更没有宣称问题已修复。

对应源码在 `maintenance_tools/native_shift_re/audit_b_member_packet_task_lifecycle.py`，测试在 `tests/test_native_shift_re_b_member_packet_task_lifecycle.py`。下一步直接追内联任务 +0x10 调度者与 `member+0x328 → motor goal`，保留 CA 原生队列、渐进转弯、寻路避障与 Shift ATTACK。

---

# BSC N1 — Member packet and task lifecycle (2026-10-15)

## Verified static evidence

Target: original Windows x64 Warhammer3.exe SHA256 518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a; PE ImageBase 0x140000000. All addresses are RVAs.

Exact local verification: **84/84 machine-code and decoded instruction starts, 23/23 E8 call targets, 8/8 typed vtable slots; 11/11 local regression tests including the private original EXE**. These checks do not establish a runtime Shift execution path or a gameplay repair.

## Ordinary B packet flag branches

The conditional ordinary-B chain goes through 0x03265C69 to 0x0326A3A0 and back to member virtual +0x368. In this specific caller, 0x0326A423 passes boolean inputs 0/0 to constructor 0x02F5F8DC, then ORs 0x08 into the result, producing packet flag **0x0E**. The other branch at 0x0326A466 passes 1/0 and produces **0x07**. Both lack bit 0x20. This corrects the prior oversimplification that all packets made by 0x02F5F8DC have constant flag 0x06; other callers are not covered by these two outcomes.

## Typed receiver and inline task

In 0x0306B9F0, when the mode helper returns 0 and packet flag 0x20 is absent, 0x0306BA5B constructs an inline task at member+0x4A8, with its holder at member+0x490. Base initialization marks member+0x5C0 active; holder cleanup clears it. The constructor installs the independently verified vtable 0x03905E18, whose +0x10 method is 0x02F83B24.

The updater has conditional action paths including 0x02F7A578 and 0x02F79FF0. For the concrete member vtable 0x0390D4F8, virtual methods +0x5B0, +0x580 and +0x568 point to 0x0306AD00, 0x0306A990 and 0x0306A8FC. These interact with member+0x328 local action state. They have not been proved to replace the final member motor goal.

Member update 0x03081EB4 checks member+0x5C0 and calls the inline task's virtual +0x80 method; that is NOT proof it invokes the +0x10 updater every tick.

## Scope boundaries

Constructor 0x02F5F7C8 has separately validated direct call sites at 0x02ECA999, 0x02F448FC and 0x0306BA5B with differing object layouts. It is not exclusive to Shift MOVE. Ordinary B vtable 0x03AE00E8 and inherited-bigTask B vtable 0x03AE0128 remain different native types.

Still unknown: the scheduler calling task vtable +0x10, the precise transition from member+0x328 action to main motor goal, and which of these branches actually runs in an inherited queued Shift MOVE instance. No gameplay fix is authorized or claimed.

## Reproduction

The read-only verifier is at maintenance_tools/native_shift_re/audit_b_member_packet_task_lifecycle.py, with tests at tests/test_native_shift_re_b_member_packet_task_lifecycle.py. It checks exact binary SHA, opcode bytes, decoded starts, typed virtual tables and call destinations, rejecting mismatches. Public CI must not contain the original game EXE.

Full Chinese technical findings are provided in the independently generated Round 3 local audit archive. No original EXE or runtime pointer logs were committed.
