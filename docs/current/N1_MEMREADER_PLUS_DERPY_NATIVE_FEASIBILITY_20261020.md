> **2026-10-20 实际文件审计更新：** 本文是仅依据公开资料进行的早期评估，其中“尚未取得/审计 Derpy .pack”及 `derpy_pack_reviewed=false` 是**当时的历史状态**，现已被 [R46：实际解包用户提供的 Derpy 与 memreader Plus，并严格核对同版 EXE](N1_R46_DERPY_MEMREADER_ACTUAL_PACK_AUDIT_20261020.md) 取代。不要再以旧描述指导下一轮。R46 证实 Derpy 具有同版 Native Tick code cave、BattleUnit 成员数组桥及 Battle worker-thread mailbox，未证明 Shift 挤压根因。

# BSC — memreader Plus / Derpy Third-Person Battles 对原生 Shift 修复的价值评估（2026-10-20）

> 调研报告而非游戏实测。**没有安装第三方 DLL、提取 Derpy .pack、运行新的 Hook、修补 gameplay，也没有触碰 main。** 这是对已有 BSC N1 原生逆向成果的观测/实施工具架构评估。

## 1. 已公开核对的外部资源

- memreader Plus Steam 创意工坊（Druwski）：https://steamcommunity.com/sharedfiles/filedetails/?id=3811098873
- memreader Plus MIT 源码及完整接口规范（PKozdra）：https://github.com/PKozdra/memreader_plus
- Derpy's Third-Person Battles BETA (Vanilla 9.X.X) (MCT)：https://steamcommunity.com/sharedfiles/filedetails/?id=3822187184
- Derpy 公开描述：基于 memreader Plus 读写游戏内存，Lua 管理第三人称控制、单士兵动画、若干 game-code patch/cave；小块 steering code 持续到进程退出。**仅有公开作者自述，没有审计 Derpy 的实际 .pack 和原码。**

## 2. memreader Plus 可以帮助什么

- `read_struct` / `read_vector` / `read_chain`：一次性读取类型化内存布局，以 BSC 已审计成员位置、目标、运动增量和状态字段建立只读近时点样本。
- `find_pattern` 及 `patcher(owner)` 的 target table + `expect`：按机器码特征及旧字节校验定位新版函数，避免将旧 RVA 不加核验直接写进 MOD。特征唯一并不证明对象类型或函数语义。
- `hook` / `hook_site` 和 `patcher:prefix/postfix/around/site`：可以给**脚本线程**经过的函数挂观察逻辑；`hook_info` 的 `calls` 与 `other_thread_calls` 区分脚本线程命中和被绕过的工作线程调用。
- `patcher:patch / cave / batch / sites / remove`：给每个 MOD 归属、原字节校验、跨 MOD 字节冲突保护和成组写入。**patch、链接可在条件允许下移除；cave / frame / relocation 会留到本次游戏进程退出。**
- `memreader_plus_runtime_report()`：当前 Hook/Patch 归属、诊断与运行状况；用于兼容性核验。

## 3. 不能忽视的局限

1. **最关键：Hook 和 site 的 Lua 回调只在游戏 Lua 脚本线程执行；别的线程绕开 Lua，直接执行原函数。** 普通成员 Tick、steering 或积分器很可能部分属于工作线程，但尚无本游戏实例的动态证据。必须先统计 `other_thread_calls`，不能把 0 次 Lua Hook 命中误报成 native 未调用。
2. 高频逐士兵 Hook 即使开销很低，也可能因 Lua 分配、重入、线程及安全锁等原因影响战斗。先用低频观察点、只读限额，不在回调内大量写日志/调用引擎函数。
3. 中途插桩要求真实指令边界、完整跳转进入点审计、PE unwind 和异常路径验证；错误的 `hook_site` 可能导致崩溃。
4. CA Lua 的数字只有约 24 位精度：原生指针和大型 RVA 不能按普通 Lua number 算，必须使用专用 typed pointer、`mr.add` 等运算以及特征码寻址。
5. memreader Plus 为第三方 native DLL，需核对发布源码/版本/文件 SHA。模型修改涉及多人同步，初版只支持离线单人诊断。
6. Derpy 改写单人控制和部分 steering，**不能与 BSC vanilla 基线同时开启**，否则破坏对照条件；其实现可以作为可恢复 patch 及识别成员引用的技术参考，绝不能直接充当 Shift 阵型修复。

## 4. 与现有 BSC 实证研究的对接

基准 EXE SHA：`9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`。以下仅是新版 EXE 已研究的 RVA，**不是安全 Hook 授权**：

| 研究点 | RVA | 目标 |
|---|---|---|
| MOVE shortTask 当前 Group 分发 | 0x02F5B400 | 低频同 UnitRoot/Group 入口观测候选 |
| B2 成员 packet 接收器 | 0x03070A48 | 接收者状态/模式分流 |
| 世界目标解析相关 steering | 0x03059BC8 | 正式运动计算前的目标及邻近选择 |
| 普通成员积分函数 | 0x03146FF0 | `member+0x88/+0x90` 位置及 `+0x13C/+0x140/+0x144` 增量消费 |
| 成员状态恢复 | 0x03164710 | `member+0x108` 状态复位与后续 Tick 交接 |

**最优先验证的是低频 Hook 所在线程，并保留 fallback：如多数成员积分由非脚本线程执行，则不能以 Lua Hook 串起所有逐成员事件。** 在因果链建立前，不部署会影响 gameplay 的 patch。

## 5. 可以执行的有限范围研究计划

A. 先阅读 memreader Plus 对 `hook_info`、`patcher:sites`、`batch`、`read_struct`、`read_original` 和线程绕过行为的接口约束，并审查源码发布与更新版本；静态测试使用 mock，不访问游戏。

B. Derpy 的 Steam 页面自述可作为“第三方已经通过内存操纵单一成员运动”的可行性佐证；但需实际取得其合法订阅后的 .pack 并审计 Lua/机器码特征，才能借鉴成员指针、steering 修改点与生命周期。**不得把尚未取得的 Derpy 内部实现当事实。**

C. 如果只读 Hook 的 ABI、局部指令边界、工作线程覆盖和预算都通过审计，做一次最多一个 UnitRoot、有限成员、限时、无 gameplay 修改的采集方案。采集字段依照 BSC R29 v2 首差工具要求，不能凭同一个 Tick ID 伪造原子快照。用户无需重新证明挤压存在。

D. 如果 Hook 在工作线程不覆盖，则改用 C++ 只读探针或安全的机器码代码洞/环形缓冲区；只在找到具体错误条件后才考虑 Native 修复。仍保留原生 CA Shift MOVE 队列、渐进转向、寻路避障和 Shift ATTACK。

## 6. 结论

memreader Plus 是 **高价值的原生内存/补丁基础设施**，可能替代我们先前花大量精力自行制作的 DLL 注入和 Hook 管理外壳；但是其**Lua Hook 不覆盖游戏其他线程**，不能据此承诺单独解决所有士兵观测或修复。Derpy 是**高价值的案例与潜在源码参考**，但不提供 Shift 折返因果证据。

本报告仅建立工具适用性与下一阶段决策条件；**root_cause_proven=false, gameplay_patch_authorized=false, memreader_in_game_tested=false, derpy_pack_reviewed=false**。
