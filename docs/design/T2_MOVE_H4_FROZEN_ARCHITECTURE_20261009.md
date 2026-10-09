# BSC H4 — 冻结的速度优先架构基线（2026-10-09）

**状态：架构与参考实现已固定；不是主线运行版发布。**
**基线：** `6027a28fcf9eb6766aec60b7c74ee16af01e2acf`，分支 `maintenance/t2move-h4-soft-corner-speed`。
**源代码快照：** `archive/h4_soft_speed_20261009/`。
**离线证明：** [Actions 37880088909](https://github.com/Twilightsp123/better-shift-command/actions/runs/37880088909)，H4 Controller 6/6、Native V3 4/4、4/4 mutants caught，46项完整维护套件 PASS。WinX64 9.0.2 Native 是 CTest 14/14 通过的构建，完整实验安装包 [Artifact 11594255419](https://github.com/Twilightsp123/better-shift-command/actions/runs/37880088909/artifacts/11594255419)。

## 冻结的产品语义

**速度/运动连续性优先**；Shift MOVE 链的中间 waypoint 是大致方向引导点，而非必须精确抵达的坐标。只要符合既有、受相邻腿长约束的 SC1/SC2/SC4 动态转向窗口，允许转角提前执行下一条 MOVE；不能为了精确踩点强制停下。明显漏掉整段路线、执行权混乱、无穷重发、任意跳过 i+2 等仍应视为故障。

## 对应实现

- **许可：** 当前 `R1.TransitionPolicy.evaluate` 的 MOVE 许可和已有动态窗口，结合 `R1.H4SoftCornerCredit`；不得机械地使用 H1 的严格 waypoint chord reach 作为所有转角的独立硬否决。
- **结算：** `SATISFIED` 仅用于可观察的实际抵达；`DEBT_PRESERVED` 保留可偿还的 SC3 先前债务；`CORNER_SOFT_ACCEPTED` 只代表 ACK 后接受了一个合法的圆滑导航引导点，完成原因是 `H4_SOFT_WAYPOINT_ACCEPTED`，不等于物理上站在该坐标。
- **事务：** `Core.commit_transition_edge` 仍是 T1.6 唯一游标提交入口，ISSUE 在 ACK 前不提交；拒绝、陈旧 revision、不同代际、非规范的 Native 结果不得假结算。
- **Native：** exact i+1 MOVE adoption 必须有在前一个 Native MOVE 仍 active 时冻结的软转角证据；i+2 等跨越仍拒绝。
- **隔离：** 优先采用已有 MOVE 控制链，不引入没有经证实的辅助 Q 延长指令；Move→Attack 和 Exit 保持既有严格独立语义，已支付 SC3 债务也不能被随意抹除。

源码和 fixture 在 `archive/h4_soft_speed_20261009` 中以 Git blob 校验锁定。它们是实际 H4 的代码副本，**不由正式模组发布入口加载**。

## 真实 WH3 验收结果与风险

2026-10-09 11:44 的实机日志已人工审查（**原始私人日志没有公开提交**）：Native Bridge/Observer/READY 正常，`CONTROLLER_FAIL=0`；共 **4** 次 `H4_SOFT_CORNER_ISSUE` 及 **4** 次对应提交，**13** 次 `TRANSITION_EDGE_COMMITTED`；存在 **3** 次 `NATIVE_SUCCESSOR_ROLLBACK`，其中两次 Native i+2 跳过规范中间节点，一次没有可用冻结提前执行证明；另有一次 Exit reassert。战斗退出 `OBSERVER_SAFE_STOP` 成功。

用户反馈本版移动效果“还可以”，但这**不是全部场景的正式验收**：没有证明所有长短腿、180°折返、密集 Z 字形、多单位同时执行、MOVE→ATTACK 或 Native i+2 跳转均稳定。这些保留在开放问题中，不允许用“架构冻结”覆盖这些未完成验证。

## main 与候选的隔离

此提交只在 `main` 增加结构化参考源码、测试、校验合同和维护索引，**不替换** `source/better_shift_command.lua`、`src/native_bridge/`、`native_maps/CURRENT` 或正式版编译输入。

原因：H4 实验分支比 `main` 领先 274 次提交，整分支快进会改变稳定发行基线，并混入尚未正式升级的 Native 候选。未来决定发布时，应由独立集成 PR 在最新运行链上复用冻结 H4 基线，并对 Windows 9.0.2 构建、Steam PACK、实际游戏速率、回滚及退出做单独验证。冻结本身不授权 Steam 发布。

## 再次修改架构的规则

任何变更必须解释为什么不再满足“速度第一 + 大致 waypoint + ACK 事务正确性”的三项合同，附可复现真实日志/路线影像和隔离分支测试。不得反复靠角度、距离、延迟调参来取代架构证据；不得静默重启 strict-H2 到点停车。

