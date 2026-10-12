# BSC N1 — 2026-10-12 第二次实机 JSONL 重审与采集器预算修复

**证据类型：真实游戏日志 2,097 行 + 原始 EXE 静态验证 + 本地 Node／Python 回归；未取得可发布的 Native 挤压修复。** 原始 user JSONL、游戏 EXE 和运行时原始地址不上传公开 GitHub。

## 正确理解这次新日志

- 真实 `ready` 1、`event` 2,095、`summary` 1，均有效；没有 Frida 错误；完整摘要的 `eventsSaved=2095`。
- 旧分析报告 `NO_SAMPLED_NATIVE_SENDER_EVENTS` 是**误导等级**。实际 Hook 汇总 21,534 次 `QUEUE_MANAGER_ENTRY`，其中 1,697 条保存、**19,837 条丢弃**；该垃圾日志在启动约 4.6 秒就耗尽普通事件预算。
- 其它被丢弃的 31 条：`NATIVE_MOVE_ISSUER` 6、`POSTCTOR_SENDER_ENTER` 2、`QUEUED_CONTINUATION` 2、`NATIVE_MEMBER_SEND` 3、`MEMBER_RECEIVER` 3、`DEFERRED_PACKET` 3、`GOAL_WRITE_PRE` 3、`GOAL_WRITE_POST` 3、`GOAL_READ` 3、`NATIVE_GOAL_DIRECTION` 3。**19,837+31=19,868**，和探针 `dropped` 恰好一致。
- 完整的非采样 `sourceCounts`：`POSTCTOR_REWRITE=50`，`RECEIVER_OTHER_OR_UNKNOWN=50`，`DEFER_OTHER_OR_UNKNOWN=50`。因此已证明实际运行的原生改包发送钩子被命中 **50** 次，也有各 **50** 次公共接收／延迟分支；**没有他们逐次同成员、同包、同命令的实例关联**，不能把 3 个 50 数字自动一一配对。
- 真实 `QUEUED_CONTINUATION` Hook 总共命中 2 次，用户报告中 0 次仅因丢弃；该命中也不能直接证明与被采样的折返来自同一 Shift order。
- 原版另把 `member+0x60` 当成阵型 ordinal，并按模 8 选士兵；本次实际原字段是 304、305、359、361，**尚无机器码证明其是阵型序号**。按序号过滤会漏掉成员；本轮改成按实际成员指针至多 24 名。

## 真实运动：只读位置，可量化但不造因果

10 次 `MOTOR_GOAL_REVERSAL`、151 次 `POST_TURN_POSITION`、234 次 `GROUP_TICK_POSITION`，同一 group 只采到 **4 个不同成员**。Tick 423 两名成员同 Tick 几乎反向，465 两名，548 三名；467 与 550 属于先前 465 与 548 已经活跃的 18-Tick 窗口，所以它们的单独回转事件虽保存，但无需再新建采样窗口，旧报告零位置数据不能解释为“没运动”。

最小**相同 group Tick 的两名成员 X/Z 中心水平距离**：

| 活跃窗口 Tick | 已采样成员 | 最小距离 | 对应 Tick |
|---|---:|---:|---:|
| 423 | 2 | 13.4851 | 424 |
| 465 | 3 | 2.2829 | 482 |
| 548 | 4 | 1.3962 | 551 |
| 658 | 4 | **0.6087** | 660 |

最后一对成员从 Tick 659 的 1.1241 距离缩到 Tick 660 的 0.6087，又在 Tick 661 拉到 0.973。这是局部实际接近后分离，并不证明有碰撞箱重叠、挤压根因、或该次转弯是 Shift 而不是 RMB。回转后继续沿旧运动方向的有限 Tick，亦不能直接当作旧 motor 目标读取错误；可能属于 CA 的渐进转向。

## 代码、测试及部署边界

修改 `maintenance_tools/native_shift_re/experiments/n1_one_shot_20261012/`：

- `one_shot_native_source.js`：队列管理器只采首 4 次和每 4,096 次，原生调用总数独立统计；MAX 提高到 5,000，源身份/目标/队列/群组位置保留高优先级；撤销未证明的 modulo-8 筛选；对接收器 RETURN-RVA 分布与同线程 member + packet 指针关联独立计数；每类事件 attempted/saved/dropped 分开核查。
- `analyze_one_shot.py`：离线将旧日志正确归为 `NATIVE_SOURCE_EVENTS_TRIGGERED_BUT_DROPPED_BY_LOGGER`，重建并严格对账 19,868 丢失条目；额外计算同 Tick 两名中心距离和 467/550 的重叠采样窗口。
- `test_probe_node.js`：先模拟 **21,534** 次普通队列管理器调用，再完成 sender→receiver→queued→goal→groupTick。要求源事件保存，`dropped=0`，包含返回 RVA、同包指针配对和 SHA/机器码 guard。
- `test_offline.py`：新增不含用户指针的同量丢弃统计回归和“模型中心近距离≠碰撞证明”的负对照。

在精确 SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` 的原始 EXE 上：**14/14 PE/unwind/objdump 原生 Hook 守卫 PASS**。Python 12/12 本地 PASS（提供精确 EXE 时），Node JS mock、Frida `ptr` locked-global PASS；GitHub CI 使用公共无游戏 EXE 合成测试。

**新修正版 Windows 实机 Frida 尚未执行；不准声称已动态验证其发送者实例匹配。** 不需为这份旧日志原样重测。离线追查必须先把实际 native return RVA 和 RMB/Shift order 身份关联，之后才可能分析有无可修补的局部运动目标矛盾。禁止用 Lua 取代 Shift 或直接把 CA 渐进转弯变为强制瞬转；Native Patch 未授权。
