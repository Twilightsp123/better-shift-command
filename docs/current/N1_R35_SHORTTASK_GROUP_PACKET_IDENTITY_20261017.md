# Better Shift Command — 第35轮 Native 只读审计

日期：2026-10-17。目标：在**用户本轮新上传**的 Windows x64 `Warhammer3.exe` 上，检验 MOVE shortTask 创建时的路线/任务引用、回调时读取当前 Group，以及 A/B 到成员 packet 的时相是否存在 **可核验的身份/版本门槛**。

**不是 gameplay patch；没有要求玩家重复证明 Shift 折返挤压。** 全文 RVA 基于当前新 EXE，并且需在指定完整 SHA 下解释；ASLR 运行时绝对地址 = 实际模块基址 + RVA。

## 0. 版本和本轮验证

- 新 EXE 232,531,920 字节，PE ImageBase `0x140000000`，SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`；与旧研究基准 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` 不同。
- 本轮 `audit_r35_group_transaction.py` 直接读取真实新 EXE：**119/119 完整机器码与 GNU objdump 指令起点；12 个 PE unwind 函数和 3 个显式无 unwind 叶函数区域；17/17 E8、3/3 JMP/JCC、2/2 vtable slot**。脱敏机器码清单包含每条的原生汇编注释；不读取运行进程，不写 EXE。
- `test_r35_group_transaction.py`：**11/11 本地 PASS（含私有新 EXE 真实静态测试）**。仓库 CI 不带 EXE 时需明确 SKIP 相关测试；合成辅助单测不得作为游戏实测证据。
- 仅重定型已知调用链的**部分局部边界**，没有全函数等价性、所有虚方法实现、实机 Shift 动态命中或修补的证明。

## 1. 从后继 MOVE slot 到 shortTask 的确切别名

新版工作函数 `0x0302AE74`：

```text
0x0302AEDB   LEA R14,[MOVE_slot+0xA0]               取槽位大任务指针字段的地址
0x0302B191   MOV [RBP-0x70],R14                    写入栈上描述符+0x50
0x0302B1A3   LEA R9,[RSP+0x40]                    R9 = 栈上描述符首地址
0x0302B1B3   CALL 0x02F31778                      创建 shortTask
```

栈帧实测 prologue：`RBP = incoming_RSP-0xB8`，3 次 push 后 `RSP = incoming_RSP-0x1B8`。因此 `[RBP-0x70] == [RSP+0x90]`，确实是 `[descriptor+0x50]` 而不是另一份局部变量。

`0x02F31791` 将 `RDX=UnitRoot` 保存到 `task+0x08`；`0x02F317C8→0x02F31878` 复制描述符到 `task+0x30`，所以：

| 创建时的输入 | shortTask 保存位置 | 证据 |
|---|---|---|
| `UnitRoot` | `task+0x08` | `02F31791` |
| `descriptor+0x42` 16-bit | `task+0x72` | `02F318C1/C5` |
| `descriptor+0x44` 8-bit | `task+0x74` | `02F318C9/CD` |
| `descriptor+0x50` 指针（指向 slot+0xA0 字段） | `task+0x80` | `02F318EB/EF` |

下游无 unwind 叶函数 `0x02F53FDC` 从 `[task+0x80]` 取字段地址，再解引用取得当时保存的大任务；若为空另有 `task+0x98` 后备。`0x02F55FE0` 在条件成立时递减其 refcount 并清空 `*[task+0x80]`。因此**任务创建时并未将 Group 指针冻结到 task+8**；它冻结的是 UnitRoot 身份，并对槽位 bigTask 字段保留了可变别名。不能在清退后用 slot+0xA0 的 NULL 反推它从未继承。

## 2. 回调发包前的 Group 晚绑定

当前新函数 `0x02F5B1E4` 在若干前置状态门槛满足后：

```text
0x02F5B3F0  RCX=[task+0x08]            ; UnitRoot
0x02F5B3F4  RDX=&[RSP+0x50]           ; 已准备的路线/参数临时记录
0x02F5B3F9  RCX=[RCX+0x32F8]          ; 此时当前 Group
0x02F5B400  CALL 0x0327ECA4           ; Group A/B 分派
0x02F5B405  JMP 0x02F5B4B3            ; 跳到后续状态/清理门槛
```

上述**两条相邻指令之间没有比较历史 Group 指针、路线 generation ID 或一致性版本**。但它只证明这一局部发包入口没有明确的前置比较：**不证明更高层或间接子过程完全没有兼容性检查**，也不证明玩家 Shift 真的出现新旧数据混用。

`0x0327ECA4` 通过 Group 关联上下文作模式判断：

- **A：** `0x0327ED17 → 0x030DA5D8 → 0x030DA51C`，可以在当前调用栈内按成员直接发包。
- **B：** `0x0327ED3C → 0x03268920`，首先在 Group 内嵌 `+0x8F0/+0x908` 位置初始化 B 路线任务；该构造器安装 `0x03AE5820` 虚表，其 `+0x10=0x03286288` 是后续路线/任务推进方法，而**不是此处直接调用成员 packet 接收器**。另有已审计 `0x032863A0→0x03286445→0x0326A994` 逐成员的条件路径，但仅凭虚表槽不能断言每次本 callback 的 B 对象实际经历该条后续路径，更不能声称同步发包。

两者属于不同的阶段。旧假说把 `Group A/B 分发` 简化为“同时生成两套直接成员 packet”，必须纠正。

## 3. 第二个晚绑定：路线回退可重新读当前 UnitRoot+0x270

- A 分派中 `0x0327ECCD` 分支选择后，若当前临时记录 `+0x30==0`，在 `0x0327ECDC/E3/EA` 通过 Group+`0xA10` 取得 UnitRoot，再从当前 `Root+0x270` 读路线朝向；若记录自带显式朝向则采用 `record+0x32`。
- B 另一路 `0x02F5B42D→0x03268CEC` 的输入 `R8=task+0x08 UnitRoot`，在 `0x03268CF0` 从该 UnitRoot 的 `+0x270` 获取路线，用于条件性 B 节点构造。

这意味着同一路 MOVE 的下游不一定只消费创建时冻结的路线描述符：**Group 和 Root+0x270 的读取时间都可能晚于短任务创建**。这建立了需要比较的两处具体时相；目前没有任何新 EXE 实机证据证明这些数据发生错误代际组合。

## 4. 两个 A/B 发送器是否在单次直接循环内逐个重取 Group？

已审计真实汇编：

| 发送器 | Group 成员总数 | Group 成员数组 | 每名成员入口 |
|---|---|---|---|
| A `0x030DA51C` | `Group+0x24` | `Group+0x28` | `0x030DA59B`，vtable `+0x368` |
| B `0x0326A994` | `Group+0x24` | `Group+0x28` | `0x0326ABAF`，vtable `+0x368` |

两个直接循环**没有每处理一个成员重新加载 `UnitRoot+0x32F8`**。这缩小了“单次循环里成员各自重取新旧 Group”的猜测，但调用前、回调子函数、对象复用、两次独立 fanout 及异步 B 激活，均仍可能影响整体时序。成员索引相邻不能代替实际空间邻兵。

## 5. 存在发包后 Group 对照/重置，不能误判成提前防护

回调在 `0x02F5B400` 后经过 `0x02F5B405 JMP 0x02F5B4B3`；只有以下门槛成立才进入后续组引用处理：`task+0xA0 != 0`、`task+0xA1 == 0`、`task+0x90` 非空、其 `+0x60` 非零、`+0x58` 非空以及一段关联处理。

随后，回调遍历 Root 中**两组引用列表** `Root+0x3298/+0x3294` 和 `Root+0x3278/+0x3274`，分别在 `0x02F5B529`、`0x02F5B577` 比较**当前** `Root+0x32F8` 与表内 Group 指针。不相等时调用 `0x030D4B50` 清理相关 Group 的 B 路线子对象 `+0x8F0` 并执行其它重置。进一步还有对当前 Group 的条件检查。

**这是真实的同一轮 Group 引用一致性清理线索，但顺序是在该 callback 的 Group A/B 分派之后。** 它不是我们寻找的“发包之前验证 shortTask 对应的 Group 与路线同代”的正证据；同时不能从存在后置清理推断 CA 先前必然用了错误引用。

## 6. 本轮排除与未解决问题

- **本轮否定/降级：** A/B 都必然在当前调用里直接给所有成员发 packet；两种发送循环每位成员都独立读取 UnitRoot 当前 Group；后置 Root+Group 引用清理等于发包前版本屏障。
- **静态仍成立：** UnitRoot 在 shortTask 创建时保存；大任务槽位字段地址沿 `descriptor+0x50 → task+0x80` 保存；下游 Group 与 Root+0x270 有晚读取；A/B 不是同相位发送；A/B 均最终有按 Group 成员列表发包的已证本地实现。
- **仍未确认：** 玩家新版 Shift 是否进入具体 A/B 分支、同一后继 MOVE 在路线/Group 代际上是否真的有错误、是否存在更上游保护机制、B 对象从初始化到 fanout 的具体同实例条件、world goal 是否错误，以及真正导致挤压的成员 steering/速度提交写者。
- **不授权补丁：** 不能全局修改 Group+0x32F8、Root+0x270、A/B 门槛或成员 position writer；普通 RMB、Shift ATTACK、原生渐进转向与避障不得被牺牲。

## 7. 下一轮唯一限定追踪

**沿 B 条件任务的一次路线有效性更新（`0x03286288→0x032862C4`）到真正 B 成员发包（`0x0326A994`）之间的“同一 Group + 同一路线”身份转换，优先判定 B 路线更新是否从当前 Root+0x270 重新取得几何目标，以及是否有 generation/有效性门槛。** 若这条边不能形成具体可错配条件，停止继续扩大 Group 猜测，转追 `0x03059BC8` steering／`0x03085114` 邻近接触响应的真正速度或位移写入者。无新增用户实机测试要求。

## 8. 本轮资源

- `audit_r35_group_transaction.py`：固定新 SHA 只读审计，PE unwind 与 objdump 起点、原码、E8、条件跳转、B vtable。
- `r35_pins.txt`：119 条完整机器码清单，15 组受限子图。
- `test_r35_group_transaction.py`：11项本地回归。
- `r35_static_evidence.json`：可机读核验输出。
- `early_disassembly.txt`、`core_disassembly.txt`、`owner_dataflow_disassembly.txt`、`b_vtable_methods.txt` 等真实新 EXE 脱敏反汇编摘录。
- `BSC_R34_NEW_EXE_RVA_REBIND_20261017.zip`：包含上轮完整新旧 RVA 重绑定工具及报告，作为交接基线；没有 EXE。

**状态：研究分支专用；新 EXE 静态 PASS；游戏内未验证；native gameplay patch 未制作。**