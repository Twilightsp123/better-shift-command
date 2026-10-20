# BSC R48 / 本对话第15轮：旧实机位置证据与 R47 空间诊断工具的严格衔接（2026-10-20）

**结论：找回了可靠的历史实机统计，未找回原始逐成员位置 JSONL；不能从汇总反推轨迹或 Shift 根因。** 本轮没有启动游戏或第三方 DLL，没有制作 gameplay patch，没有修改 main。

## 1. 两组不同的历史实机证据，禁止混合

- V3 对照统计：同一 UnitRoot 共60名士兵、36名被稳定采样。普通 RMB MOVE 的 139 帧中 0 帧出现小于1米的近距成员对；Shift queued MOVE 的194帧中85帧出现；约180°折返专项观察40帧中的29帧出现近距，最小报告约0.474m。来源：`docs/current/N1_903_AI_HANDOFF_20261011.md`。这是**历史实机汇总**，不是本轮重新计算的逐人轨迹。
- 2026-10-12 另一份 one-shot 实机采样：保存2,095条 event，其中234条 `GROUP_TICK_POSITION`，只记录了4名不同成员。Tick 658活动窗口的 Tick 659/660/661，前次报告的中心距分别为1.1241/0.6087/0.973m。来源：`docs/current/N1_903_20261012_FIRST_VALID_SOURCE_TRACE_LOGGER_OVERFLOW.md`。**这是另外一次测试，不得与 V3 比较统计合并，也无法凭三个距离重新构建两个人的 X/Z 坐标。**

检查了当前工作区的 R34-R47 ZIP、会话上传、Project/Library 可检索文件与 GitHub 当前研究资料。R47 ZIP 只包含标明 `synthetic` 的位置 JSONL。早期文档明确写明用户原始 JSONL/EXE/内存指针没有公开上传 GitHub。**本轮没有找到可以直接用 R47 算真实玩家逐帧形变的原始 JSONL**。

## 2. 真正落地的离线工具（完整源代码在本轮交付 ZIP）

新增独立的 `maintenance_tools/native_shift_re/r48_legacy_group_tick_triage.py`，直接支持旧版 `experiments/n1_one_shot_20261012/one_shot_native_source.js` 采样事件：
`type=event, ev=GROUP_TICK_POSITION, group, member, turnStartTick, groupTick, x, z, atMs, seq`。

严格遵守旧来源能够证明的内容：
1. 按原始 Group/转向窗口/GroupTick 匹配成员；同一 GroupTick 的读取是**顺序读取，不是原子群组快照**；
2. 同组 Tick 超过默认50ms的人为采样时差阈值、同Tick重复成员、跨Tick缺口、时间倒退的记录不强行合成连续轨迹；
3. 输出真实的**成员中心距离**与相同成员对应的前后Tick距离变化，至少3个成员时做刚体平移+旋转的非刚体残差；仅用于描述形变，不等同身体碰撞或原生Bug；
4. 旧 `actorMode` 不是 R47 `member+0x330` 动作虚表，旧 `goal24` 不等于当时正在生效的世界motor goal；输出强制标记这两层 NOT_OBSERVED；
5. 原始 Group/member 字符串仅在本地内存中配对，报告用匿名窗口/成员ID，不保存原始运行时指针；跨Tick的相同指针也无法排除 ABA 复用。
6. 汇总统计不是事件格式。即使输入 `85/194` 或已知 `0.6087`，若没有实际 GROUP_TICK_POSITION 原始行，新工具将诚实返回 `source_position_events=0`，不会生成假轨迹。

完整离线资源：`BSC_R48_LEGACY_TRACE_SPATIAL_REUSE_20261020.zip`，包含可执行分析器、19项新单测、真实历史汇总与来源清单、**合成坐标**字段兼容样例、匿名报告、回归日志、R47完整档案与SHA256校验文件；不含游戏EXE、第三方 DLL、用户原始 JSONL。

## 3. 实测验证级别

- 新 R48：**19/19 合成离线回归 PASS**（包含唯一成员、采样时间预算、缺Tick、非原子边界、变形残差及不能凭汇总编造轨迹）。
- 复跑原 R47：**19/19 PASS**（包含用户上传真实新版 EXE + memreader Plus 与 Derpy ZIP 的静态文件身份校验；其空间轨迹用例仍为合成）。
- R48 合成演示中将 Tick 659→660→661 的中心间距设为1.1241→0.6087→0.973m，**仅是按已发表汇总数字构造的测试数据，不是恢复出的 V3/one-shot 实机坐标**。
- **R48 没有真正重算历史实机逐成员间距或发现挤压根因**。它解决的是旧 JSONL 的合法输入与无效证据拒绝条件。
- 不执行、分发或建议盲目安装新的 Hook。保留 CA 原生 queued Shift MOVE、渐进转向、阵型与避障，以及 RMB MOVE 和 Shift ATTACK。

## 4. 研究止损与下一个真正高价值问题

除非以前的真实 JSONL 可恢复，否则**停止尝试从没有坐标的历史统计推回士兵轨迹**。继续推进 R47 基于 memreader Plus 的单兵只读采样合同，重点审计其 Lua API、成员实例生命周期与同一 Tick 的采样偏差；若无法安全得到成员状态，就继续静态追 R41-R45 普通成员的积分状态交接。实机数据缺失应报告，而不是反复叫玩家重测。

**证据状态：** real legacy aggregate present; raw legacy per-member trajectory absent in accessible artifacts; R48 offline converter tested; current-game collector untested; first_error_proven=false; native_gameplay_patch=false.

完整脚本随本轮本地 ZIP；GitHub 本文件仅保留研究结论和获取源码的交付说明，未经远端上传的工具不宣称已在仓库落盘。
