# BSC N1 第33轮 — A/B packet 最终进入同类型 member 位置写入者（2026-10-17）

固定用户原始 Win64 Warhammer3.exe SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，ImageBase `0x140000000`，地址为 RVA。离线审计 **88/88 全指令字节和 GNU objdump 真正指令起点、9/9 E8、5/5 branch、3/3 同一 member 虚表槽**，独立本地 **18/18 unittest PASS（含实际原始 EXE）**；无 EXE 17 PASS/1 SKIP。无本轮 Windows 游戏内事件、无 gameplay patch。

## 1. 已完成的类型化下游连接

旧 V3 实机命中的 MOVE 工作 `0x03025D70→0x0301287C→0x02F2C734` 的短任务回调可经 `0x02F56404 CALL 0x03279E40` 条件性选择 A (`0x03279EB3→0x030D554C→0x030D5490`) 或 B (`0x03279ED8→0x03263AB0`，后继 `0x03265B24`)。

A 在 `0x030D5509` 将 R8B 设为1，B 在 `0x03265D39` 把 R8D 清零；随后**两者均调用各自成员对象虚表+0x368**。成员的真正同类型表 `0x0390D4F8` 已由原始 .rdata 实际指针核对：`+0x368=0x0306B9F0`、`+0x100=0x03073568`、`+0xE8=0x03073224`。早期10月文档已有 A `+0xE8→0x03073224→0x0315EC98` 一段，本轮新增共用A/B入口、另一 `+0x100` 位置写者及条件优先级；不能重称旧路线首次发现。

## 2. 真正的条件门槛与 R8B 差异的边界

`0x0306B9F0` 首先调用 `0x02DC2E04` 检查模式，并独立检查 `packet+0x50 bit0x20`。如果模式结果=0且该 bit 清零，则在 `0x0306BA35..0x0306BA60` 建立内嵌任务并直接离开**当前**接收器；这是另一条延迟成员动作机制，而不是立即运行本轮两个位置写者。其它分支按**每名成员**的 `member+0x104` 状态：值为1/2进入 `virtual+0x100=0x03073568→0x0315F4E0`；其余值进入 `virtual+0xE8=0x03073224→0x0315EC98`。

**不可将 A/B 入参 R8B=1/0 直接认定造成不同士兵更新！** 它不参与上述首个模式+packet bit0x20 的判定；另外成员状态也会影响走哪个虚方法。更不能误判为 `R9B` 仅写8位却被 downstream R9 64位测试造成 CA bug：接收器 `0x0306BB0B mov r9b,r14b` 属 `virtual+0x100` 入口；复杂 `virtual+0xE8` 从栈第5实参转发该 byte，原 `R9` 还涉及另一目标引用，不能跨两条分支误做寄存器污点结论。这项本轮初步猜测已否定。

## 3. 类型化成员坐标和状态直接写入

`0x0315F4E0` 从 RCX 保存 member 指针在 RDI，并在 `0x0315F52C` 写 `member+0x88` 的8字节、在 `0x0315F53E` 写 `member+0x90` 的4字节。另一较复杂的 `0x0315EC98` 以 RSI 保存 member，按条件在 `0x0315F311/327` 写 `member+0x88`、在 `0x0315F33F` 写 `member+0x90`。这与上轮误命中的“另一个 component+0xE0”不同，**确定是同一类型成员的直接位置写者**。

两个具体代码段还更新 `member+0x108 = (old & 0xF7) | 0x02`：**清 bit0x08、设 bit0x02，却不清 bit0x04**。因此位置/姿态更新不等价于第25～26轮定义的成员动作 Tick 分支切换到邻近 steering；必须同时比较 bit0x04、member+0x324 和 B20 指针。上述位置改变可能是合法的 CA 同步动作，不等于已经观察到折返时瞬移或挤压。

## 4. 后续判定与停止条件

下一步针对真实 queued Shift 后继 MOVE 只考虑一条**可否证**假说：A/B packet 进入接收器时的模式 helper、packet+0x50 bit20、member+0x104 分支是否让某两个真实空间邻兵的**位置写入代际**早于/晚于各自目标与 steering 相位。先静态检查生命周期与可比快照，不要求用户反复安装未验证 Hook。如果实机没有命中这些写者，马上排除这条假说；即使命中，也须与普通 RMB 相同条件对照才能称异常。没有位置错误的同实例证据，绝不能对 `0x0315F4E0`/`0x0315EC98` 全局 nop 或 patch。

本轮维护：`maintenance_tools/native_shift_re/ab_member_mode_pins_20261017.txt`（88条完整 opcode，特别修复 objdump 多行拆开的3条8字节 MOVSD）、`audit_ab_member_mode_to_position_20261017.py`（原始 EXE只读审计）、`tests/test_native_shift_re_ab_member_mode_to_position_20261017.py`（19个仓库回归定义，私有EXE一项必须 skip）。完整本地资源包：`BSC_R33_AB_MEMBER_POSITION_NATIVE_AUDIT_20261017.zip`（本地18 PASS、字节证据、原生反汇编、前轮档案，不上传EXE）。

**状态：native_patch_authorized=false。** 仅研究分支 `research/n1-native-shift-behavior-patch-20261009`，不动 main、不修改原始 EXE、不用 Lua 取代 Shift，保留 CA 渐进转弯、避障、普通 RMB 和 Shift ATTACK。
