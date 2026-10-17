# BSC N1 第29轮：只读观察位置类型审计与首差比较器防误判（2026-10-17）

## 本轮真正完成的工作

固定用户原始 WH3 Win64 EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，ImageBase `0x140000000`。重新从用户 ZIP 直接解压并计算完整 SHA，大小 252021192 字节。**21/21 原始 opcode/objdump 真实指令起点、3/3 E8 目标、PE unwind 所属函数与目标身份审计 PASS**。新独立本地回归 **22/22 PASS（包含真实 EXE）**；不带私有 EXE 的测试 **21 PASS / 1 SKIP**。这些全部是静态/离线事实，**没有任何新游戏内动态采集，也没有修好 Shift 兵牌折返穿插**。

## 一、四处采样入口必须按真实 Win64 寄存器/对象类型解释

| 候选位置 RVA | 静态已证参数/字段 | 为什么还不是可部署探针 |
|---|---|---|
| `0x0306B9F0` B 成员 packet 方法入口 | `RCX=member`，`RDX=packet`，`R8B` 为一个函数标志 | 无 MOVE/Group 构造代际，不能由此证明实机键盘 Shift |
| `0x0311954C` 最终目标提交器入口 | `RCX=member`，`RDX=目标记录`，`R9D=flags` | 可提前返回/改道；多处公共调用者，不是每次都提交 |
| `0x03081EB4` 成员 Tick 入口 | `RCX=member`，prologue `RDI=RCX` | 一个 member 的 Tick 不等于整个兵牌原子更新屏障 |
| **`0x0305502E` 世界目标刚解析完成** | `RDI=当前member`（`0x03054BA9` 来自入口RCX）；`RAX` 指向本函数此前 `[RSP+0x60]` 输出缓冲区 | 仍需 Win64 活动线程、生命周期、采样预算和安全验证 |

**重要类型纠错：** 公共 `0x0311CED4` 自己的 `RCX` 是目标记录、`RDX` 是输出缓冲区，没有 member 身份。不能直接在那里把 `RCX` 记成 soldier ID。与它不同，`0x0305501D LEA RCX,[RDI+0x1E0]`、`0x03055024 LEA RDX,[RSP+0x60]`、`0x03055029 CALL 0x0311CED4`，构成同一成员函数里的数据边。`0x0311CF02 MOV RAX,RDX` 让调用返回值指向该 xyz；`0x0305502E` 之后的 `0x03055036` 才开始从 world xyz 减去 member+0x88 坐标。因此调用刚返回的观察点比通用 resolver 入口更有成员身份语义。

**这只是静态候选方案。** 不能因固定 SHA 和正确 RDI，就断言 Frida attach 在该点安全、性能可接受或目标对象一定仍有效。当前明确 `collection_ready=false`。

## 二、对第28轮离线“首差”工具的纠错

旧工具把 `unit_epoch+move_epoch+tick` 一致看成足够配对条件；但真实成员逐一 Tick，**同 Tick 号不是同时刻**。它还默认 `member_index` 相邻可以代表阵型邻兵，而实际索引邻接不证明空间邻接。又如 group_epoch 缺失、frame_epoch 不同时，旧工具仍称 frame 是“首次差异”，但更早的差异根本未被观察。

新工具 `causal_first_difference_v2_20261017.py` 改用 `bsc.n1.member_observation.v2`：
- 必须有同一 `trace_id、unit_epoch、move_epoch、snapshot_id、tick` 和两个相邻索引；必须有明确 `phase` 和每条记录的 `sample_seq/sample_time_ns`。
- 采样阶段不同返回 `NOT_COMPARABLE_PHASE_MISMATCH`；序列号重复返回 `NOT_COMPARABLE_DUPLICATE_SAMPLE_SEQUENCE`；采样时间差超过**人为保守预算** 200000 ns 返回 `NOT_COMPARABLE_SEQUENTIAL_SKEW`。该阈值**不是游戏引擎规定的时间屏障**，通过它也仅说明采样接近。
- 缺 `group_epoch` 等较早观察字段时，继续列出可记录的候选差异，但 `earliest_stage_is_unambiguous=false` 并列出 `earlier_unobserved_stages`；该排序仅是数据处理阶段的优先级，不能把它解释为时间先后或物理因果。
- `velocity_xyz` 尚缺经过定型的写入器时可以填 null；不允许伪造该字段，报告会列 `unobserved_stages`。
- 工具拒绝非数值/无穷向量、明显原始地址形式、不匹配 epoch、重复样本和超过2000条输入。它无法从 ID 文本证明采集器真的正确生成代际编号，因此仍明确报告 `cannot_verify_collector_lineage=true`。
- **无论结果如何**，`actual_atomic_snapshot_proven=false`，`cannot_prove_spatial_neighbourhood=true`，`root_cause_proven=false`，`patch_authorized=false`。不允许把合成的两士兵目标相反例子当游戏 Bug。

这相当于把“可能误导修补位置”的观察先从分析流程中排除。两个正确相邻索引的士兵朝向不同在原生队形中可能合法，**没有真正的同实例与原子性证明就不授权修复**。

## 三、下一阶段只有五道进入实机采样的安全门槛

1. **生命周期 ID**：证明 UnitRoot、Group、MOVE slot 与成员的构造/清退与池复用（ABA）；不能用指针相等伪造代际。
2. **调用实参和对象有效性**：所有采样点要求固定 SHA 和完整 opcode、PE unwind、Win64 ABI、入口/出口对象边界；本轮只完成这些的**静态部分**。
3. **同步采样条件**：不能把“同 engine Tick 整数”冒充同一个兵牌快照；要找到真正的全组安全读窗口，或将数据标记为 sequential near-time、不做首差因果判断。
4. **限制频率**：只读、单 UnitRoot、有限成员、一次性短采集、明确的内存异常处理和最大数据预算；不得阻塞战斗主线程。
5. **运动输出真实写者**：还没有完全定型，只记录可证明的世界目标和 Tick 分支，不得编造物理速度输出。

**没有完成上述门槛前不要求玩家重复进游戏**。如无法证明安全采集，继续以原始 EXE 做静态验证，不把未验证的 Hook 交给玩家运行。

## 文件与结果

- `maintenance_tools/native_shift_re/audit_readonly_observation_sites_20261017.py`：21个位置/3条E8、静态候选 site/ABI 和 BLOCKERS，游戏未注入。
- `maintenance_tools/native_shift_re/causal_first_difference_v2_20261017.py`：严格阶段/采样差离线对照。
- `tests/test_native_shift_re_observation_feasibility_and_diff_v2_20261017.py`：19项仓库回归定义，其中私有 EXE 项在 CI 明确 skip；本地独立版测试22项、真实 EXE 全 PASS。
- 独立完整档案 `BSC_R29_PROBE_SITE_AND_COMPARISON_SAFETY_20261017.zip`：源代码、脚本原始运行日志、合成 v2 JSONL/报告、脱敏 site evidence、中文总结、固定 SHA 证明；**没有 EXE、用户进程指针或写入/Hook 脚本**。

本轮发现的是实机诊断的正确对象/时间边界，**不是挤压根因，不是 Native 修复**。保留 CA Shift、渐进转弯、避障、普通 RMB、Shift ATTACK。`native_patch_authorized=false`。只改 `research/n1-native-shift-behavior-patch-20261009`，不碰 main。
