# BSC R75 — Group rebuild 与成员发送器任务归属，竞争假说有界止损（2026-10-26）

**最终决策：`ROSTER_RACE_CAUSAL_LINK = BLOCKED/DEPRIORITIZED`；不是证明所有 WH3 并发情形不可能。** 产品目标仍是修复原生 Shift 连续折返的士兵穿插/挤压，保留 CA 的 MOVE 队列、渐进弯道、避障、普通 RMB 与 Shift ATTACK，不以 Lua/native 第二套队列取代。

### 严格原始 EXE 静态发现

使用当前用户 Win64 `Warhammer3.exe` SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`、232531920 字节、ImageBase `0x140000000`。在原始 `.udata` 的 E8 rel32 目标候选全扫描后，逐条核对 PE unwind 函数归属、原始五字节，并在本地 **GNU objdump 实际指令起点**复核 **17/17** 个直接调用位置。该集合不含任何间接调用、虚表分发或运行时线程上下文。

| 目标函数 | 直接 E8 调用 RVA | 说明 |
|---|---|---|
| `0x030209EC` Group 构建器 | `0301F38C, 030251F3, 03032C92, 03042E03` | 4 个真实调用者，不专属于一种 Shift 场景 |
| `0x0326A994` 成员 sender | `032769F2, 0328034E, 03282768, 03286445` | 4 个真实调用者 |
| `0x03032C48` Group/路线相关入口 | `02D8AAA7, 02D8AB6C, 02DB9F86, 03014613, 03035F2C, 030366F3, 03037167, 03037A69, 0303D094` | 9 个调用者；不能断言其全部实际到达构建器 |

**新证据与纠错：** 发送器的 4 个直接调用者中，只有 `0x03276970 (B2+0x08) → 0x032769F2` 与 `0x032863A0 (B2+0x10) → 0x03286445` 在 R37 有构造器绑定的 B2 类型证据。另外两处 `0x032802B0→0x0328034E`、`0x032826B4→0x03282768` 均是真实 PE 函数内的直接 E8，但其具体上游任务类型没有在本轮独立证明。不得把 sender 的所有命中都记录为 B2/Shift。

### 关于 roster 竞争：已证与未证

R74 已确认真实的新 Group 构建可以先从旧 Group 删除成员，变更旧组的 `+0x24/+0x28`，然后才将新组绑定到 `Root+0x32F8`。R73 的 B2 sender 固定自身 Group 指针，但循环逐次读取其 `+0x24/+0x28`。这是两套代码访问**相同类型字段**的事实；不是实例级冲突事实。

R75 **没有**建立旧 B2 发送器与新 Group 重建的真实工作线程重叠，也没有确定引擎外层调度屏障/锁的有无，更没有证明同一个 Group incarnation、同一 queued Shift MOVE、同一成员漏发或目标错配。两条代码路径在各自调用栈内为直接同步调用，不能据此声称两条独立栈必然串行或必然并发。R72 的独立 MPSC/Win64 ABI 测试也不能充当 WH3 线程归属证据。

### 反证与止损协议

提供合成调度事件 `begin_sender/end_sender/begin_rebuild/end_rebuild`：验证串行无重叠、跨线程假想重叠、同线程嵌套（窗口重叠≠真实多线程）、不同 Group 代际不误合并、缺失事件 fail-closed。所有合成结果始终标为 `SYNTHETIC_ONLY`，不是 WH3 动态证据。

**本地原 EXE 运行了完整审计与 21/21 Python 测试（含2项原 EXE）。公开仓库另附较精简的 SHA/E8/UNWIND 检查器与回归用例，无原始 EXE 时 SKIP。** 全部 17 条直接调用的原始字节和 objdump 检查、反汇编摘录、完整源码/测试/结果 JSON、R74 完整历史在聊天交付的 `BSC_R75_EXECUTION_OWNERSHIP_RACE_STOP_20261026.zip` 内。不分发游戏 EXE、第三方 DLL 或运行时指针。

### R76 唯一主线

将 **`ROSTER_RACE_CAUSAL_LINK` 降级，禁止继续无限搜索 Group+0x24/+0x28。** 下一轮优先回到已类型化的单成员原生链：后继 MOVE → reference-aware world goal → `0x03059BC8` Steering → `0x03146FF0` 积分和邻近响应。定位一处可以区分“目标已跳变”与“目标正常但内外侧成员运动协调异常”的具体决策；没有对象寿命/ABI 实证前仍禁止 live Hook，不能凭合成轨迹发布 gameplay patch。

`actual_concurrent_roster_mutation=false`（未证）、`external_serialization_proven=false`、`root_cause_proven=false`、`native_gameplay_patch_authorized=false`、`main_unchanged=true`。
