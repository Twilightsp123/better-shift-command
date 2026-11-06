# BSC R93 — 原生 Group A/B 模式谓词与 Packet/积分器位置更新门槛（2026-11-06）

## 0. 成功标准对照

**本轮属于 R92 约定的 S3 静态门槛核查，不是寻找更多函数。** 原版 `Warhammer3.exe` 232531920 bytes，SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`，PE AMD64/ImageBase `0x140000000`，所有地址为 RVA。没有操作游戏进程、没有 Hook、没有 gameplay 补丁。

- `S3_STATIC_GROUP_SELECTOR = PROVEN`：给出 A/B 分支的完整原生谓词和精确字段路径。
- `S3_STATIC_PACKET_INTEGRATOR_GATE = PROVEN`：给出两类 Packet 更新设置状态位、积分器拒绝正常 XYZ 累加的原生条件。
- `S3_ACTUAL_SHIFT_ACTIVATION = NOT_PROVEN`：没有同一玩家 Shift 任务/Group/member/Tick 的真实命中记录。
- `SEARCH_CANDIDATE = NOT_YET_MET`；`ROOT_CAUSE_PROVEN = false`；`GAMEPLAY_FIX_PROVEN = false`。本轮**完成一项基础数据判别条件，且排除一个无条件叠加的旧猜测**，不是达到根因定位成功。

## 1. Group A/B 的模式判别已经从黑箱变成可计算谓词

`0x0327ECA4` 的入口 `RCX=Group`，`0x0327ECAE` 读取 `Group+0x10` 上下文 C，`0x0327ECB8` 读取 `[C+0x440]`，`0x0327ECBF` 读取 `[G+0x150]` 作为模式控制对象 Q，`0x0327ECC6 E8→0x02DC7E30`。

`0x02DC7E30` 是一个可完全列出真值表的叶函数：

- `0x02DC7E30: MOV EAX,[RCX+0x28]`，读取 `Q+0x28` DWORD，视为 unsigned。
- `0x02DC7E33/36: CMP EAX,5; JA false`。
- `0x02DC7E38/3D: MOV ECX,0x29; BT ECX,EAX`，测试第 0、3、5 位。
- `0x02DC7E40: JAE false`，成功 `0x02DC7E42: MOV AL,1; RET`；否则 `XOR AL,AL; RET`。

即 **`A_mode = (Q.mode ∈ {0,3,5})`**。其余 DWORD 值均返回 false。

在 `0x0327ECCD` 判定后，true 路径调用 `0x0327ED17 E8→0x030DA5D8`（研究命名 A），false 路径调用 `0x0327ED3C E8→0x03268920`（B）。**0/3/5 是当前内存状态的数值分组，不是已认证的 Shift 或 RMB 类型标识。**

成员 Packet 接收器 `0x03070A48` 在 `0x03070A60/6D/74` 通过 `[member+0x58] → [C+0x440] → [G+0x150]` 调用同一个 `0x02DC7E30` (`0x03070A7B`)。若该门槛为 true，或者 Packet+0x50 bit 0x20 为真，才进入相关目标/位置接收阶段；随后 `member+0x104 == 1 or 2` 时选择普通 member virtual+0x100，否则走 virtual+0xE8。R78 在普通 member vtable `0x03912950` 中已证明 +0x100→`0x030785AC`、+0xE8→`0x03078268`；两个包装器分别调用 `0x0316460C`、`0x03163DC4`。

**可证伪的新观察要求：** 在同一 Root/同一原生路段/可信同步窗口内，分别读取 Group 的 C 指针与成员的 C 指针、两侧 `Q+0x28`。若同一个 C 实例且字段未变化，二者使用相同纯函数，A/B 选择应该一致。若读数不同，先排除成员归属错误、非原子采样与运行期上下文重绑定，不能立刻归咎于 Shift bug。提供 `tools/r93_mode_alignment.py` 对已有 JSONL 样本分类；这是一个输入协议校验器，**不是运行时观测器**。

## 2. 明确排除“Packet 与积分器无条件同时写位置”

**直接 Packet XYZ 路径** `0x0316460C`：`0x03164658` 写 `member+0x88/+0x8C`，`0x0316466A` 写 `+0x90`；`0x03164670/76/7F/81` 保留部分标志并设置 `member+0x108` 的 `0x02` 位。之后还可能执行其它函数或虚方法，不能假设该位永久保持。

**另一个 Packet XYZ 路径** `0x03163DC4` 的特定后半段：`0x0316443D` 或 `0x03164453` 写成员实际 `+0x88/+0x8C`，`0x0316446B` 写 `+0x90`；`0x03164471/77/80/82` 同样将 `member+0x108` bit `0x02` 置位。该函数自身存在多个前置条件，其 XYZ 写入不是对任意来电必然发生。

**原生成员积分器** `0x03146FF0`：`0x031471A9` 读取 `member+0x108`；`0x031471B5 TEST DL,0x02`；`0x031471B8 JNE 0x0314738F`，直接越过正常 XYZ 累加语句 `0x0314720B/23/3B`。如果 bit `0x02` 为 0，还存在 `member+0x155` 以及其它状态条件限制，因此 **bit 清零并不保证正常积分一定发生**。

**旗标并非永久保护**：普通成员 vtable +0xF0 精确指向 `0x03164710`，其 `0x03164776 AND [member+0x108],0xF5` 明确**清除 bit 0x02**（同时清 bit 0x08）。在下一次进入积分器前，它是否被调用、是否出现其他修改，尚无可信时序。两 Packet 路径在置位后仍会调用其它函数；不能从静态先后推出整个 Tick 中互斥。

因此以下旧假说已遭**具体条件反证**：*Packet 位置写入之后，即使 flag 不变，积分器也总会无条件叠加同样的 XYZ 位移*。此说法是错误的。真正需要检查的 H3 缩小为“flag 被重置的时刻和成员运动代际如何交接”；目前既无事实证明该交接有 bug，也没有安全的补丁点。不要修改 `0x031471B8` 来强行跳过正常物理积分，这样会严重影响普通移动。

## 3. S3 确认后研究优先级更新

R92 的四类假说 H1–H4 仍未获实例级因果证据。R93 使 H3 的“无条件双写者竞争”版本失去根据，但 H3 的**有条件状态交接**仍需证实才可继续。优先级建议：

1. **S1 Root/Group/member 身份闭合。** 建立稳定单位获取途径，核实 `Root+0x32F8` 指向的 Group 及 `Group+0x24/+0x28` 成员枚举的生命期和同一游戏 Tick 同步性，不得仅凭相同偏移强行认定实例。
2. **S2 世界目标转换。** `member+0x1E0/+0x1F0` 有参考框架；必须在与当前世界 XYZ 同一时间系内解析后，才能分析是否目标先汇聚。这比继续泛扫物理 writer 更直接对应挤压根因。
3. **仅在有可信样本时检验模式一致性**：Group 的 `Q.mode` 与同一兵牌成员的 `Q.mode` 是否一致，是否存在模式在一次转向中重绑定。缺少实际样本不等于已经证明不一致。

**两次实机机会的上限继续有效**；未完成 S1/S2、安全观察合同前，不把任何新测试要求交给玩家。外部观测没有证明的函数命中、写者时序、route generation 一律 UNKNOWN。

## 4. 验证和证据范围

- 当前原始 EXE **64/64 完整机器码**与 LLVM 指令起点匹配；4/4 直接 E8 目标、5/5 Jcc 目标、3/3 普通成员虚表入口；6 个 PE unwind 函数范围，其余 8 个 pin 属无 unwind 函数（包括叶谓词），不冒充有 unwind。
- 本地 Python **22/22** 单元测试通过，其中 2 项直接使用原始 EXE；公共环境 **20 PASS / 2 SKIP**，另有跨 256 个状态字节的合成 bit 操作表和模式真值表。不能将合成模拟计为真实 Shift 修复。
- 可复验脚本 `tools/r93_s3_audit.py` 使用精确 SHA/PE/ImageBase、原始字节和 LLVM 真指令起点 fail-closed；`evidence/` 保存 7 段原始反汇编、冻结机器码清单、真实 EXE / 公共模式测试日志。
- 没有用户 Windows 游戏运行会话；未验证具体 Root、Unit 或 Shift route 的实例身份，也没有任何 Hook 安装/游戏补丁授权。资源包不分发商业 EXE。

**最终状态**：`S3_STATIC_BRANCH_GATE=PASS`；`S3_SHIFT_INSTANCE=UNKNOWN`；`MODE_DIVERGENCE_OBSERVED=false`；`H3_UNCONDITIONAL_DOUBLE_WRITE=REFUTED`（限于保护位保持期间的正常积分器 XYZ 指令）；`SEARCH_CANDIDATE=false`；`ROOT_CAUSE_PROVEN=false`；`GAMEPLAY_FIX_PROVEN=false`。