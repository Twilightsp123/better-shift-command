# BSC N1 · 第26轮：member+0x108 与 member+0x324 的同类型状态转换（2026-10-16）

## 本轮固定原始证据

用户原始 Windows x64 EXE SHA256：`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，PE32+ ImageBase `0x140000000`，全部地址为 RVA。独立离线审计 **142/142 原码和 GNU objdump 真正指令起点、15/15 E8、14/14 条条件/无条件跳转及 5/5 同一个成员虚表的真实 64 位方法指针**，本地 **18/18 测试 PASS**（包含真实原始 EXE、错误 SHA 和 Python -O fail-closed）。GitHub 源码版本设有19个回归用例，其中原始 EXE 检查在公开 CI 应 skip；目前不能声称远端 CI PASS。

## 一、两个字段的写入者确实同属原生成员类型

真实原生成员 vtable `0x0390D4F8` 中：

| slot | 函数 | 独立证实的作用 |
|---|---|---|
| +0x128 | `0x0307FB0C` | `0x0307FB40 OR BYTE [member+0x108], 0x06`，**设置 bit4 和 bit2** |
| +0x130 | `0x0307FC3C` | `0x0307FC77/79/7B` **清 bit4、设 bit2**，其它位保持 |
| +0x138 | `0x0307FB50` | `0x0307FB5A/6E` 清 bit4，OR 0x0A；同时**保留/设置 bit8** |
| +0x538 | `0x0306A100` | `0x0306A111` 设置 `member+0x324=4` |
| +0x550 | `0x0306A53C` | `0x0306A6BA` 在分支门槛后设置 `member+0x324=16` |

这些是同一类型的**不同**虚方法，不意味着一次 queued Shift 命令必然同时执行两种设置。动作4设定器有真实 E8 入口 `0x03117226`；其邻接源码遍历成员及动作状态，**还未绑定到 Shift 后继 MOVE**。三个 flag 方法没有找到直接 E8 入口，属于真实 vtable 方法；不能把其它类型同偏移的虚方法错接过来。

## 二、`0x03068154` 清状态有多条门槛

在原生 `0x03068154..0x030682E4` 的完整函数内，`0x03068235/6B/93/AF` 共四条 `AND DWORD [member+0x324],0`，各自仅在通过前置状态检查时执行，并非每次 Tick 都清零。

它在 `0x030681A4` 读取 `member+0x108 bit4`，bit4 **为零**时才直接调用成员虚表+0x488；该函数本体不能简单概括为“清 bit4 开关”。因此 `member+0x324=0` 并不充分保证下一 Tick 进入邻近运动：bit8 仍可能优先执行 vtable+0x498，bit4 仍置位时可能走其它动作条件，`member+0xB20` 非空又会改走 vtable+0x490。

尤其是 vtable+0x138 退出方法**清 bit4 但同时设置 bit8**，本身可能直接转到另一个 Tick 分支而不是邻近运动。这是本轮最有价值的原码反例。

## 三、不能倒置同一个 Tick 内的时间顺序

在 `0x03081EB4` 本体中，`0x03082268/7D/81` **先读取** flag/state 选路：

- bit4置位且状态4/16：`0x030822D2→0x03080F4C` 处理内嵌 action，`0x030822E4 JMP 0x030823A9` 跳过邻近运动。
- bit4为零且 `member+0xB20=NULL`：`0x030822F9→0x03054B84` 邻近处理，`0x03082301→0x03088808`。
- **只有该后一分支及额外的对象/动作条件通过后**，才可能 `0x03082399 CALL 0x03068154`，在其中有条件清零状态。此写入发生在该 Tick 已经选定运动分支**之后**，不能反过来证明先前为何选路。

`0x03068154` 还有多个其它直接调用者，故以上只描述这个已核对的单次 Tick 顺序，不能宣称全系统只能在下一帧清状态。

## 四、下一步与停止条件

接下来优先只追 queued MOVE 激活后**哪条类型化成员动作包**会调用 vtable+0x128/130/138/538/550，以及是否同一 UnitRoot、group generation、两相邻 member 的阶段实际错位。静态类型闭环不是实机发生证据。如果找不到 queued Shift 到该状态机的同实例桥，就停止继续泛查 flag 写者，转向已定位的世界目标/实际速度和避障输出。

用户已确认原生 Shift 连续折返兵牌内部穿插，不需要再次证明。没有 root cause 或 Native gameplay patch；必须保留 CA 原生排队、渐进转向、寻路与避障，且不能伤及普通 RMB/Shift ATTACK。仅维护 `research/n1-native-shift-behavior-patch-20261009`，绝不修改 main，不上传 EXE 或玩家私有内存日志。

## 回归入口

- `maintenance_tools/native_shift_re/member_state_transition_pins_20261016.txt`（142条）
- `maintenance_tools/native_shift_re/audit_member_state_phase_20261016.py`
- `tests/test_native_shift_re_member_state_phase_20261016.py`（19个定义，公开 CI 原始 EXE 项跳过）
- 本地 `BSC_R26_MEMBER_STATE_TRANSITION_NATIVE_AUDIT_20261016.zip`：独立原始 EXE 审计器、18项本地回归、只读证据、原始机器码、中文研究报告，无游戏二进制。
