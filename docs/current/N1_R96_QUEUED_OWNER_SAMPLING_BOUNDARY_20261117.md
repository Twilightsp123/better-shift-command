# BSC R96 — queued MOVE 原生所有者采样入口：有界审计与停止条件（2026-11-17）

**研究范围：**匹配的 Warhammer3.exe Win64，232531920 bytes，SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`，ImageBase `0x140000000`。地址均为 RVA。只读静态逆向，未运行游戏、未装 Hook、未制作补丁。

**验收：**`S1_STATIC_SLOT_TASK_ROOT_GROUP = CONDITIONAL_PROVEN`；`S1_SAFE_LIVE_SNAPSHOT = BLOCKED`；`ACTUAL_SHIFT_ROUTE_GENERATION = UNKNOWN`；`SEARCH_CANDIDATE=false`、`ROOT_CAUSE_PROVEN=false`、`GAMEPLAY_FIX_PROVEN=false`。

## 1. 入队路径不会经过即时 Group 处理点

原生统一 MOVE 入口 `0x030374CC` 以 `0x03037500 MOV R14B,R9B` 保存原生 append/replace 标志。`0x030377C2 E8→0x02F5540C` 处理队列；`0x030377E8 E8→0x0300E170` 构造 MOVE slot；`0x030377ED E9→0x03037A6E` 跳过本函数中 `0x03037A69 E8→0x03032C48` 的即时 Root/Group 处理调用。

这是对观测方案的具体否定：**不应把 `0x03032C48` 当成所有 queued MOVE 的入队采样点**。`R9B` 是原生 append/replace 参数，不是已证明的玩家 Shift 物理键。R52 已研究该分流，本轮把分流与 MOVE 任务/Group 观测边界共同复核，不能冒称旧地址首次发现。

## 2. MOVE slot → shortTask → 当前 Group 的有类型条件链

- `0x0300E170` 在 `0x0300E185/8C` 将 MOVE slot 虚表 `0x0390DD00` 安装到对象，精确 vtable+0x08 = `0x0302AE74`。
- `0x0302AE74` 读取 `[slot+0x10]+0x08` 对应 Root；在受条件保护的短任务创建路径中，`0x0302AEDB` 保存 `&slot+0xA0`，`0x0302B191` 将其装入任务描述符，`0x0302B1AC` 获取 Root，`0x0302B1B3 E8→0x02F31778`。
- `0x02F31791` 将 Root 保存到 `task+0x08`；`0x02F317BB/C2` 安装短任务虚表 `0x03AC1310`，其 vtable+0x10 = `0x02F5B1E4`。
- 回调的受限分支 `0x02F5B3F0` 从 `task+0x08` 取 Root，`0x02F5B3F9` 再从当前 `Root+0x32F8` 取 Group，`0x02F5B400 E8→0x0327ECA4` 进行 A/B 分派。这是 **late binding**：任务创建时没有冻结这一 Group。

R35 已证明 shortTask 保存 slot+0xA0 的可变别名、Group 晚绑定及 A/B 时相差异，R73 已限定 B 发送器的 roster 重取行为。不能把二者串成“每次玩家 Shift 必然命中”的运行时因果链。当前回调局部的 Root→Group 读取之前没有可见的 Group 代际比较，但不排除外层同步或检查。

## 3. 一个不同的原生 Root 所有者局部阶段

`0x03032C48` 在单次函数调用中：`0x03032C92 E8→0x030209EC` 重建 Group；`0x03032C9A MOV RDI,RAX` 保存本次 Group；`0x03032CC8 E8→0x030179B0` 进行路线配置；`0x03032CCD` 读取 `Root+0x270`；`0x03032CD4 MOV RCX,RDI`；`0x03032CDF E8→0x030DA51C` 下发 A 类成员记录。它在原生调用栈中保存 Root/Group，比异步两次读指针更可核对，**但不证明本路径是 queued append 所经过的阶段，更不证明在中间子调用或其它线程中对象不能被回收**。R75 早已确定该函数有九个直接调用者，不属于唯一 Shift 专用入口。

## 4. R96 的观测器安全结论

现在有两个互不等价的观察阶段：入队阶段只能取得原生 slot/append 信息，shortTask callback 更靠近当次 Group 和成员 Packet，但后者尚缺 **原生 task/route generation 身份、成员/Group 生存期 pin、实际工作线程排他、SEH/unwind/Hook 相容性**。R94 对象池 ABA 反例仍有效。仅用 Root/Group/member 双向字段一致，不能提升为安全的异步内存读取权。

本地 `r96_seam_contract.py` 只评估离线声明的证据缺口，永远不从外部自填 epoch 自动授权 Hook。`S1_SAFE_LIVE_SNAPSHOT` 仍为 `BLOCKED`，不要求用户实机测试。

## 5. 复验与本轮后续工作

本地原始 EXE 逐字节及 LLVM 真实起点：**131/131**，**10/10 E8、1/1 E9、2/2 虚表指针、17/17 语义锚点、9 个有 PE unwind 的局部代码段**。本地单元测试 **23/23 PASS**；公开模式 **21 PASS / 2 SKIP**，跳过的是商业 EXE 校验。完整离线证据、9 段真实反汇编、冻结 131-pin manifest、审计器与日志在当轮 ZIP 中，含完整 R95 ZIP，不含游戏 EXE。

**R97 限定任务：**在 `0x02F5B1E4` 上游选择**一个有类型的 shortTask 原生调度器**，证明它对任务和 Group/成员的生存期/线程保护，并找到能够区分当前 queued slot/route generation 的原生来源。若缺任何一项，继续只读静态研究，禁止安装 Hook 或报告 `SEARCH_CANDIDATE=true`。

`main` 不修改。R96 不提供游戏可运行修复。