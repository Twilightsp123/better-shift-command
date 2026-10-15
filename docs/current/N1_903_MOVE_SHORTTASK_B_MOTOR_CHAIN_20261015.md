# BSC N1 — 第 10 轮：MOVE shortTask → 普通 B → 成员运动目标静态闭环

## 原始二进制与证据等级

用户提供的原始 Windows x64 Warhammer3.exe，SHA256：`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，PE32+ ImageBase `0x140000000`。全文地址均为 RVA。

在同一个原始 EXE 上独立完成 **218/218 个不重复机器码及 GNU objdump 指令起点、28/28 个真实 E8 目标、10/10 个类型化虚表槽**，以及三处 RIP-relative 构造器 vtable 安装、两个无 unwind 叶函数尾部和成员接收器真实 E9 目标。分段原始审计为 96 + 58 + 70 共 224 项，有 6 处重复，故只有 **218 个唯一地址**。完整本地离线 **30/30 测试 PASS**（包含完整原始 EXE 证据），公开 CI 没 EXE 时必须跳过原始文件测试。属于 EXACT_ORIGINAL_EXE_STATIC 和 SYNTHETIC_CONTRACT，**绝非实机动态命中或 gameplay patch**。

## 新证据：真正的 MOVE shortTask 与普通 B 分发存在条件性连接

- 原生构造器 `0x02F2C734` 保存 `shortTask+0x08=UnitRoot`，设置 vtable `0x03ABBE18`，该表 `+0x10=0x02F561E8`。构造器经 `shortTask+0x7D` 条件，还可能从 `0x02F2C822` 调用 `0x02F4F514`。
- `0x02F561E8` 在关联大任务状态的特定分支检查 **`bigTask+0x20==4`、`bigTask+0x24==0`、`bigTask+0x28==3`**，才于 `0x02F56479` 走 `0x02F4F514`。其它分支可走 `0x02F56404 → 0x03279E40`，这是**不同分发入口**。
- `0x02F4F514` 从 `shortTask+0x08` 获取 UnitRoot，在 `0x02F4F625` 读当前 `UnitRoot+0x32F8` group，按条件建立普通路线，再于 `0x02F4F62C` 调 `0x03279EE8`。
- `0x03279EE8` 通过 `[[group+0x10]+0x440]+0x150` 调原生 mode helper `0x02DC2E04`。**mode helper 非零**进入 `0x030D554C` 直接发包分支；**返回零**才经 `0x03263EC4` 构造普通 B 辅助对象 vtable `0x03AE00E8`。
- 普通 B `+0x08=0x03271B0C` 能在条件满足时创建普通节点 `aux+0x78`；`+0x10=0x03281520` 在节点有效时通过 `node+0x70 → 0x03265B24` 发包。带旧大任务的另一类型 `0x03AE0128/aux+0x58` **不是**本对象。

**这个发现把原生 MOVE shortTask 与普通 B 的来源真实连接起来，但不能把此处 state=4 同时当作继承式 queued MOVE 的 state=1。**

## 新证据：record kind → packet → action → motor goal 写入器

`0x03265B24` 以 `0x30` 步长配对 `record[i]/member[i]`。只有发送上下文允许时，`record+0x2C` 的 `5/6/7` 对应 **`0x67/0x68/0x69`**，`8/9` 对应 `5/6`；原生另一标志可把高 kind 抑制为零。具体复制链：

`0x03265C3F R9D → 0x0326A3A0 R14D→R8D → 0x02F5F8DC packet+0x34 → 0x02D99F74 → inline task+0x74`。

普通 B 指定 caller 可产生 `packet+0x50=0x07 或 0x0E`（均无 bit 0x20）。成员接收器 `0x0306B9F0` 在 mode helper 返回 0 且缺 bit0x20 时构造 `member+0x4A8` 内联任务，随后 **`0x0306BA60 E9 → 0x0306BBDA` 结束本次接收**，跳过后续直接姿态处理；这不意味着物理运动必然暂停。

内联任务 `0x03905E18+0x10=0x02F83B24` 在 kind、flags、进度等 gate 通过后，经 `0x02F79FF0→member virtual+0x580=0x0306A990` 安装 `member+0x328` 动作 vtable `0x03913808`。成员 Tick `0x03081EB4→0x03080F4C` 可调用这个**动作**的 `+0x10=0x0325E294`，后者在条件分支进入 `0x03071E04` 写 `member+0x7F8/+0x818`，`0x03071F20` 又可调用 `0x0311954C` 写 `member+0x1E0` 运动目标。**动作 +0x10 与内联任务 +0x10 属于不同类型，调度不能混同。**

## 哪些条件仍未找到

1. 没有实际证明玩家某次 **Shift 继承 MOVE state=1** 如何在另一生命周期时刻进入上述 state=4 分支，也没有证实玩家当时的 group mode 为零。
2. 没有证明同组相邻两成员收到不同 packet kind、不同动作生效代际，或此差异恰好造成 180° 折返的目标冲突。最终目标写入仍受其他原生 gate 约束。
3. 没有 Native gameplay 补丁、游戏实测、用户新折返要求。不能全局改公共构造器或破坏旧方向投影、RMB MOVE、避障和 Shift ATTACK。

## 源码、验证与下一处施工

- `maintenance_tools/native_shift_re/audit_move_to_motor_goal_bridge.py`：SHA 与原码、真实起点、E8、类型化 vtable、RIP 构造器指针、E9 目标只读验证。
- `maintenance_tools/native_shift_re/move_to_motor_goal_manifest.txt`：218 唯一指令及 28 E8、10 vtable 的脱敏原码清单。
- `tests/test_native_shift_re_move_to_motor_goal_bridge.py`：公开 CI 7 PASS / 1 SKIP，私有原始 EXE 8 PASS。
- 本地还有独立的 96/58/70 指令分段审计，综合 30/30 PASS。不得上传 EXE、含运行时指针的原始日志。

下一步优先把 **继承式 state=1 的大任务状态变化**精确追到同一个短任务后续 state=4、group generation、member goal 安装时刻。如静态确实无法区分实例，再仅设计一次精准的只读、可撤销动态取样，不重复证明用户已确认的缺陷。
