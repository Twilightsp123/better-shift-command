# N1 / WH3 9.0.3 — MOVE 队列到成员可选几何分支的类型门槛（2026-10-13）

## 核心结论：相同队列布局已经对上，实际 MOVE 类型被 +0xB8 门槛排除

本轮使用用户提供、SHA256 完全匹配的原始 EXE 进行 PE、unwind、GNU objdump 静态审计。独立原始 EXE 实测 94/94 opcode 及真实指令起点、17/17 直接 E8、5/5 vtable 间接分发、4/4 MOVE 类型槽守卫；本地 9/9 回归 PASS（含精确原始 EXE）。不是实机分支命中或 gameplay patch。

此前 docs/current/N1_903_VIRTUAL388_STACK_PACKET_20261013.md 把 0x030A48A4 笼统描述为上游几何数据来源，现更正：调用前已经构造了栈上的动作记录，0x030A48A4 是一层带成功状态的额外参数计算；不能把它当作路段几何来源。

### 1. MOVE 队列对象和下游查询函数的结构对照

0x030323EE 将 MOVE 命令对象置于 RBX。0x030326B4 用 LEA [RBX+0x278] 取得队列；0x030326BE CALL 0x02F50410。队列内部使用 +0x10 起始包装槽位，单槽跨度通过 (index+index*8)<<5 = 0x120；0x030326CE 在返回的包装槽位 +0x18 构造真实 MOVE 槽位，0x030090D1/0x030090D8 安装 vtable 0x0390B4F0。

另一方面，0x03039C7C 读取传入上下文 [RCX+0x28] 作为队列根对象，以 root+0x2F88 判断计数、root+0x2F8C 读取 active index，从 root+0x2A0+index*0x120 得到嵌入式多态槽位。

| 同一类根对象偏移 | MOVE 命令发放者 | 成员查询路径 |
| --- | --- | --- |
| root+0x278 | 嵌入式 queue | 下游依次访问同一布局 |
| root+0x288 | queue wrapper 第一个槽位 | - |
| root+0x2A0 | wrapper+0x18 的实际 MOVE slot | active subslot+index*0x120 |
| root+0x2F88 | queue+0x2D10，槽位计数 | 与零比较 |
| root+0x2F8C | queue+0x2D14，active index | 读索引 |

这个对照建立了完全一致的对象布局，而不是仅凭相同 stride 推断两个独立队列。它仍不证明某次玩家 RMB/Shift 操作的具体 root 指针与当前 callback_owner+0x28 完全相同；实例关联尚无有效现场命中。

### 2. MOVE 子类并不满足可选目标查询

精确 MOVE vtable 0x0390B4F0 的 +0xB0 和 +0xB8 都指向 0x008D3330。该短函数字节为 32 c0 c3（xor al,al; ret），固定返回 false。0x03039C7C 首先调用 active slot virtual+0xB8；返回 false 时走 0x03039CDF 的回退路径，将 float32(0,0,0) 写到三个位置。0x03039D14 / 0x03039C20 亦以 +0xB8 为门槛，0x03039BC4 以 +0xB0 为门槛，因此对于上述 MOVE 具体类，它们不会从这些可选槽位返回真实的特殊来源。

不能因此断言所有 MOVE 运动不会运行 0x03010724：该函数仍存在 fallback / 特殊状态进入条件。但必须停止声称 +0x388 对所有 Shift MOVE 无条件执行。

### 3. 局部记录的第五参数来源已明确

0x03045F80 经 0x03039C7C 得到三维向量，将向量写入调用者 [RSP+0x40..0x48]，并将该局部向量地址写为第 5 个参数 [RSP+0x20]，于 0x0304601A CALL 0x03010724。后者以 RBP = entry RSP-0x128 设栈帧，所以 [RBP+0x150] = entry RSP+0x28 = caller [RSP+0x20]，R13 据此取得本地三维坐标指针。不得把这个 RBP+0x150 或 RBP+0x158 当作 native MOVE task+0x150 / +0x158。

### 4. 两种记录构造器和五处分叉

| 构造器 | 调用点数量 | 后继方法 |
| --- | ---: | --- |
| 0x02F5FCAC | 4 | 分别可进入 v+0x388 或 v+0x380 |
| 0x02F5FE28 | 1 | 通过 0x03010D71 helper 后可进 v+0x388 |

0x030A48A4 在 0x03010724 中有 5 处 E8 调用，分别是 0x03010AE4、0x03010BEE、0x03010D71、0x0301104D、0x030111AF。前三条 v+0x388 分发地址是 0x03010B0F、0x03010DAE、0x03011078；另两条分发 v+0x380 地址 0x03010C43、0x03011203。这些不是无条件的 5 次成员安装。

两种 packet 构造器都把 +0x58 初值设置为 float32(-1.0)。helper 0x030A48A4 返回低 32 位浮点数与高位状态字节组合；有条件设置有效位后，调用者将浮点值写入栈记录 +0x58 并 OR +0x6C 的 0x20 标志。helper 其中一条分支把来源对象 +0xE0 的整数经过浮点转换乘以精确常量 0x0391CEB4 = 0.01745329238474369（约 pi/180），但未定型该来源整数的最终业务含义。不得把 +0x58 当成员 X/Z 世界坐标修改。

### 5. 下一步修复定位（有目的地收敛）

现有证据否定了『直接在所有 Shift MOVE 的成员 v+0x388 / 栈记录 +0x58 施加统一转向补丁』的安全性。优先回到真正由 MOVE task 激活的 0x03025D70 → 0x0301287C 和 0x030D5490 typed member+0x368 命令发包链，定位后继 MOVE state=1 的旧方向参考何时变成逐成员目标、排序或索引。要保留原生队列、渐进转弯、避障、RMB MOVE、Shift ATTACK；没有同一对象实例与错误条件的充分证据，不发布 Native gameplay patch。

工程产物：audit_move_queue_member_gate.py、test_native_shift_re_move_queue_member_gate.py、脱敏静态 JSON、本文及 AI handoff 纠错。未提交游戏 EXE、玩家原始 JSONL；未修改 main。
