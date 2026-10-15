# BSC N1 — 第17轮：普通 B 两条发包路径的逐字段输入对照（2026-10-15）

## 固定原始 EXE 与验证级别

Windows x64 原始 `Warhammer3.exe`，SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，PE ImageBase `0x140000000`，所有地址均为 RVA。本轮独立只读核验 **82/82 机器码与 GNU objdump 指令起点、7/7 E8 真实目标、2/2 类型化 B 虚表槽**，本地 **11/11** 回归 PASS（含真实原始 EXE、错误 SHA/Python -O 负例）。**没有** Windows 运行时 Shift 对应、物理挤压因果或 gameplay patch。

## 1. 两条不同路线来源，进入同一个成员生成器

普通 B vtable `0x03AE00E8` 的两条路径：

- 快路径 `+0x08 → 0x03271B0C` 从 `aux+0x60` 取现成路线，`0x03271B71` 分配 0x30 字节临时参数，经 `0x03271B8E CALL 0x03265B24` 发送；成功后 `0x03271B9F` 标记 `aux+0x80=1`。
- 后续节点路径 `+0x10 → 0x03281520` 必须先通过 `aux+0x80==0`、`aux+0x78!=NULL`、`node+0x08!=0`，才从 `node+0x70` 取路线；`0x032815A7` 分配同样大小的参数，`0x032815C5 CALL 0x03265B24`，随后标记处理完毕。

**不同的仅是本次静态输入链中的路线对象来源，以及两个发包阶段的门槛与时刻。** 两者的辅助对象状态字段不保证在不同 Tick 数值相同。

## 2. 同一个 0x30 临时参数结构：有证据的已初始化字段

| 输入记录偏移 | 快路径输入 | 后续节点输入 |
|---|---|---|
| `+0x00` | `aux+0x60` 现成路线 | `aux+0x78→node+0x70` |
| `+0x08` | `aux+0x68` float | 同一字段 |
| `+0x0C..+0x10` | `aux+0x70..+0x74` 五个标志 | 同一字段 |
| `+0x14` | 置 0 | 置 0 |
| `+0x18` | `aux+0x6C` 状态 DWORD | 同一字段 |
| `+0x1C` | `aux+0x75` 标志 BYTE | 同一字段 |

两条路径在发送前把 `RDX=[aux+0x10]+0x08`、`R8=aux+0x18` 和 `R9=&record` 交给同一函数 `0x03265B24`。该函数经阵型策略 `virtual+0x48` 产生 0x30 步长的 `record[i]`，从群组成员数组取 `member[i]`，再经 `member virtual+0x368` 下发。**普通 B fast/fallback 入口并不存在两套独立成员索引/发包算法。**

严格边界：我们**没有**证明完整 0x30 字节（未初始化 padding）相同；更没有证明两个不同时刻的路线指针、group 上下文、member+0x318、record+0x2C 和最终 motor goal 一致。因此这是静态入口参数**布局相同**的正证据，不是实机物理目标相同的证明。

## 3. 真正的下一因果差异

前轮 B 构造器将初始 `node0+0x70 → descriptor+0x28 → aux+0x60`。当这个初始路线为空时，`+0x08` 才会另建节点，后续 `+0x10` 消费 `aux+0x78→node1+0x70`。下一轮**不要再比较共同的 `0x03265B24` 算法**；只需检查为何初始 `node0+0x70` 为空、后续 `node1+0x70` 如何变成有效，以及两者是否在**同一 queued MOVE 的同一 group/任务代际**中出现空间不同。再决定是否需要一次性、严格版本守卫的只读任务身份采集。

继续保留 CA 原生 Shift 队列、渐进转弯、寻路避障、RMB MOVE 和 Shift ATTACK。不得重试“改所有 packet”、取消旧方向投影或以 Lua 替代。用户已证明 Shift 挤压存在，**不要求再证明**。

## 4. 可重复验证

- `maintenance_tools/native_shift_re/b_two_path_compare_pins_20261015.txt`：82 个真实原码位置。
- `maintenance_tools/native_shift_re/audit_b_two_path_input_contract_20261015.py`：严格 SHA/PE/unwind/指令起点/E8/类型化 B 虚表、已初始化参数布局。
- `tests/test_native_shift_re_b_two_path_input_contract.py`：本地真实 EXE **11/11 PASS**；无私有 EXE 的公开 CI 应 10 PASS / 1 SKIP。负例包含未初始化字段“不等同整块内存”等价、错误 EXE、优化模式以及文件不可覆盖。
- 本地独立完整证据包另有完整 disassembly 参数表与脱敏结果。未公开游戏 EXE、私有 runtime pointer、未验证 Native patch。

`native_patch_authorized=false`。只维护 `research/n1-native-shift-behavior-patch-20261009`；不可改 main。

## 第17轮进一步：已找出初始 node0 与 fallback node1 的第一次构造门槛差异

针对同一固定 SHA 原始 EXE，新独立审计 `audit_b_node_initialization_gates_20261015.py` 通过 **17/17 原始机器码及真正指令起点、5/5 E8**，本地 **7/7** 测试通过，包含实际 EXE 检查。

初始节点：`0x02F4F5C3` 的输入记录从栈 `rsp+0x50` 开始，`0x02F4F5C8` 将 `[rsp+0x9C]=(record+0x4C)=1`，经 `0x02F4F5DE` 调普通节点构造器 `0x031219B0`。

fallback 节点：`0x03271BE9 CALL 0x030ECA50` 组装输入；原生叶函数 `0x030ECA56 XOR R10D,R10D`、`0x030ECAAB MOV [RCX+0x4C],R10B` 保证新的输入 `record+0x4C=0`，之后 `0x03271C04` 同样调用 `0x031219B0`。

**首次不同的强制条件：** 节点构造器 `0x03121A82` 读取 mode helper；`0x03121A87/89` 若 AL=1，直接到转换分支，否则 `0x03121A8B/8F` 只有在输入 `record+0x4C==1` 时才允许转换。故初始 node0 **必尝试** `0x030FDA9C`，fallback node1 由于未设置强制标志，**只有 mode helper=1 才在本次构造立即尝试转换**。否则 `node+0x70` 保持清零、`node+0x08` 未被标记，等待后续有条件重算。这解释了为什么两个节点未必在同一阶段 ready。

**关键限制：** `0x03121A99` 调转换器后，`0x03121A9E` 无条件写其返回值至 `node+0x70`，`0x03121AA2` 直接写 `node+0x08=1`；未发现中间检测 RAX 是否为空。因此 **node+0x08==1 并不等于 node+0x70 非空**。当前仍缺真实 queued Shift 中的 mode/group 身份以及生成路线是否正确，不能直接 Hook 这两处 flag 或把正常 deferred 当作错误。

更新 [审计](../../maintenance_tools/native_shift_re/audit_b_node_initialization_gates_20261015.py) 和 [回归](../../tests/test_native_shift_re_b_node_initialization_gates.py)。本轮两项私有 EXE 审计合计 **99 个原始指令位置、12 条 E8、2 个 B 虚表槽，本地 18/18 测试 PASS**，分属两个独立原码验证模块，数字只描述静态覆盖。无 Native gameplay patch。
