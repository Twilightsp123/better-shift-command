# Better Shift Command N1 — 从函数清单改为“首个行为差异”因果搜索（2026-10-15，第15轮）

## 目标与范围

**已经确认的玩家缺陷：** 原生 Shift 连续 MOVE 折返时同一兵牌士兵运动相向、局部挤压。无需再次证明存在性。修复必须保留 CA 队列、渐进转弯、寻路避障、普通 RMB MOVE、Shift ATTACK；禁止 Lua 队列替身、整体禁止投影、全局改 packet 或取消队形运动。

**整个研究不再以“新增了几个 RVA”作为进展。** 只接受四种产出：(1) 某字段的真实生成→消费者身份闭环；(2) 可证伪的 RMB-replace / queued-append 对照；(3) 把错误根因候选排除的真实分支/对象反证；(4) 同实例的成员目标错误条件及安全的局部补丁。其他散点调用清单仅归档。

目标固定原始 Win64 EXE SHA256：
`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，ImageBase `0x140000000`，所有地址为 RVA。不能把 EXE、含运行时指针日志提交公开 GitHub。

## 一、建立比较矩阵而非把 Shift 当布尔魔法

| 判别轴 | 对照 A | 对照 B | 证据边界 |
|---|---|---|---|
| 入队 | `R9B=0` 清队列 | `R9B!=0` 追加 | **原生意义已证**，玩家按键未直接配对，游戏内部也可追加 |
| 任务交接 | 无继承／fresh bigTask state0 | 资格通过后复用旧 bigTask，重设 state1 | 不是所有追加都继承 |
| 路线朝向 | `slot+0x9A bit2=1` 用 `slot+0x98` | bit2=0 用当前 `group+0xBF0` 重新计算 | 属于原生描述符字段，不是键盘 Shift 码 |
| 成员生成 | Mode helper 非零 → A | Mode helper 为零 → B | 虚表与输入所有者不同，不得把 A 的目标当作 B 输出 |
| 成员更新 | 当前 packet/子动作被立即处理 | 条件内联任务后续处理 | mode、kind、目标有效性等门槛参与，不能简单把某个 flag=延迟 |
| 结果 | 每人 record/packet/action/motor goal 一致 | 某两人首次出现空间或任务代际错位 | **仍未得到实机同一实例因果证明** |

**最先查找的差异节点**，是同一 MOVE slot 在激活、shortTask 任务更新、成员 packet 这三个时刻的 `任务引用、朝向来源、group generation` 是否一致。先定任务/数据源，再看运动物理；不再向外无限扩调用图。

## 二、本轮真正新证据：bit2 贯穿两次朝向选择

在固定原始 EXE 上，已经类型化证明 `0x03025D70` 的四条组合分支：

| MOVE slot+0x9A | 构造方式（bit0） | 激活时路线朝向 | 构造 shortTask 的来源标记 | 后续 `0x02F4F514` |
|---|---|---|---|---|
| bit2=1, bit0=1 | 手动写 descriptor | 保存的 `slot+0x98` | `shortTask+0x74=1`；`+0x72=slot+0x98` | 用已保存的朝向 |
| bit2=1, bit0=0 | 叶函数 `0x030092FC` | 保存的 `slot+0x98` | 同上 | 用已保存的朝向 |
| bit2=0, bit0=1 | 手动写 descriptor | 当前 group 空间参考 | `shortTask+0x74=0`，`+0x72=0` | **再按当时的 group 计算** |
| bit2=0, bit0=0 | 叶函数 `0x03009280` | 当前 group 空间参考 | 同上 | **再按当时的 group 计算** |

严格字段路径：`0x03025EDB / 0x03009375` 写 descriptor+0x44=1；`0x0302605A / 0x030092EC` 写0；`0x02F2C834` 把 descriptor+0x42/+0x44 复制到 `shortTask+0x72/+0x74`。`0x02F4F530/534/538` 再按标记选保存朝向，或通过 `0x02F4F546 → 0x02F4F554 → 0x02F4F565 → 0x02F4F57E/58B` 依**当前** group 和 shortTask 目标再算。两次 group 的地址数值即使相同，也不能据此证明对象未从池中回收重用。

**这不是已证实的错误。** 两次朝向不同可能是合法渐进转向；先检验两名相邻成员的路线目标对应是否因此错乱。合成几何测试只能证明“两个时刻的 group 位置不同，角度可以不同”，不能替代 CA 游戏物理。

## 三、更重要的任务生命周期断点：B 前先释放指针

`0x02F4F514` 在读取 `shortTask+0x74` **之前**，先执行 `0x02F4F52B CALL 0x02F50FE4`。已经对完整无 unwind 叶函数核对：

- 如果 `shortTask+0x80=&MOVE slot+0xA0` 非空并且其中 bigTask 非空，`0x02F50FF8` 递减 bigTask+0x18 引用计数，`0x02F51002` 把 `*[shortTask+0x80]` 清为 NULL；
- 如果第一来源空，可使用 `shortTask+0x98` 的 fallback，`0x02F51013/16` 对它递减引用、清理；
- 该函数本身没有把 `shortTask+0x74` 清掉；同一个 shortTask 可继续构造路线记录并在后面调用 `0x03279EE8`。

**关键反证/采集纪律：** 不能在 B packet 下发后才看 `MOVE slot+0xA0` 是否等于旧 bigTask，以此证明旧任务身份已经脱钩或从未继承。这里原生可能已主动清空。未来如确实需要只读动态诊断，务必在 `0x02F4F52B` **之前**记录 slot/bigTask/shortTask/route/group 的相关身份，后续只用本地相关编号关联，不对游戏写内存。

## 四、唯一优先的搜索顺序与停止标准

**P0：对照源字段确认，已有闭环，停止重复调查。** `R9B→DL`、条件旧 bigTask 交接、`slot+0x9A bit2`、`shortTask+0x74`、两个朝向算法、B 前释放顺序。若以后发现原始指令或对象类型反证，纠正文档，而不是先发布补丁。

**P1：静态查看同一后继 MOVE 的“任务身份存活窗口”。** 把 `MOVE slot+0xA0` 的提交、`shortTask+0x80` 指向槽位、`0x02F4F514` 的清理，以及 `0x03279EE8` 创建 B 对象按严格先后顺序列出。查能否以静态字段证明 B 辅助任务仍关联那次 bigTask，或只能持有新生成的 route node。若引用已按设计清理，**排除“B 包发送时 slot+0xA0 仍为旧 task”的默认假说**。

**P2：按 mode 将两条成员输入彻底分开。** A 使用 `0x03279E40`（临时明确朝向优先，否则回退 descriptor+0x44），B 使用 `0x03279EE8 / 0x03AE00E8`、有自己的 `aux+0x78/node+0x70`；带旧大任务 B 的 `0x03AE0128 / aux+0x58` 又是第三类。不给不同对象拼接“相同偏移”，不把 A/B 互斥分支误认为当次双发包。每条边都记录字段所有者、真实引用和 gate。

**P3：只追逐成员 motor goal 的首次错误状态。** 对同一 UnitRoot、同一 group generation（不能只比指针）、同一 MOVE slot/task 相关身份、相邻两个 member ID，比较 `record[i]`、`packet flag/kind`、`member+0x328` 子动作、最终 `member+0x1E0` 目标及其更新时间。若两个成员获得本身合法的渐进过渡目标而没有代际/索引差，转去检查真正 steering/避障局部作用；不得硬拦换目标。

**P4：若静态证明无法确定实例，再一次性只读观察，不让玩家盲测。** 先离线验证所有采集地址/反汇编/缓存/线程/对象生命周期，限定 1 次 RMB 与 1 次 Shift 同兵牌短观察，记录分支和前后身份。group 对象池存在 ABA：以审计器**本地**构造计数/生命周期序号区别复用，不依赖指针等价。最少采集点优先包括 `0x03025D70`、`0x02F4F52B` 清理前、`0x03279E40/0x03279EE8`、`0x030D5490/0x03265B24`、`0x0311954C`，必须先证明可安全命中且有去重/预算。没有这套静态准备就**不要求用户进游戏**。

**P5：补丁资格。** 只有静态/同实例动态证据证明错误的“具体条件 → 两个成员错误目标 → 可局部恢复一致性”的链路，才制作默认关闭、原始 SHA+机器码守卫、Win64 ABI/生命周期清楚、可撤销的 Native 小补丁。必要离线反例覆盖 RMB、fresh/queued MOVE、180°渐进转向、避障和 Shift ATTACK；仅静态测试通过不得宣称 gameplay 修好。

## 五、交付、证据计数与维护

本轮 **87/87** 原始机器码及 GNU objdump 真实起点、**13/13 E8**、**5/5 无 unwind 叶函数 ret** 通过；**9/9 本地离线测试 PASS（包括固定原始 EXE、错误 EXE fail-closed、全部组合）**。工具 `maintenance_tools/native_shift_re/audit_two_stage_heading.py`、清单 `native_two_stage_heading_pins.txt`、测试 `tests/test_native_shift_re_two_stage_heading.py`；公开 CI 未提供游戏 EXE 时只运行合成回归，原始 EXE 测试明确跳过。

**当前结论等级：** 双阶段朝向政策及 B 前释放顺序 = EXACT_ORIGINAL_EXE_STATIC；两时刻 group 不同造成不同角度 = SYNTHETIC POSSIBILITY；用户的 Shift 折返挤压现象已确认，但这条机制与挤压的**同实例因果仍 UNKNOWN**。`native_patch_authorized=false`。只在 `research/n1-native-shift-behavior-patch-20261009` 维护，不动 main。
