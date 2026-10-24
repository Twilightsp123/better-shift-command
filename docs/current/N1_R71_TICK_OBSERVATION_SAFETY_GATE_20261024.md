# BSC R71 — 原生成员 Tick 只读观测入口与线程安全门槛（2026-10-24）

**结论：原生入口定位可靠，但 `HOOK_NOT_AUTHORIZED`。不是游戏修复，未安装 Hook/运行 DLL。**

## 真实 EXE 精确核验

用户上传的 Win64 `Warhammer3.exe` SHA256 为 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`，大小 232531920 字节，ImageBase `0x140000000`。以下都是 RVA。

- 普通成员虚表 `0x03912950+0x18` → `0x03086F04`（主 Tick）。
- PE UNWIND 函数为 `0x03086F04..0x0308774C`，`UNWIND_INFO RVA 0x03CCF090`。原始 PE 声明的序言长度为 **63 字节**，19 个 unwind code slots。
- 入口前两条完整指令：`0x03086F04: 48 8B C4`（`mov rax,rsp`），`0x03086F07: 48 89 58 10`（`mov [rax+0x10],rbx`），下个指令始于 `0x03086F0B`。Derpy 的 `CAVE_SITE` 完全一致。**7 字节对齐不代表位于 prologue 内的 detour 可以安全展开。**
- `0x03086F2C` 保存 `RCX=member` 至 RDI，后续在条件允许时调用 `0x03087013→0x03065DB8`（待处理目标）和 `0x03087349→0x03059BC8`（Steering）。不能把任意 Tick 当成完整同兵牌全员观测。
- 本地对真实 EXE 校验 32/32 完整机器码与 objdump 起点、4/4 E8、函数及异常展开记录、普通成员虚表，均 PASS。

## 重新解包的第三方真实源码

- Derpy `platform.lua` 匹配当前游戏版本及 7 字节入口，其 `P.check_mailbox()` 在初始化时尝试安装 `mr.patcher('derpy_tp'):cave('mailbox', update,...)`。作者记载早期跨 Lua/native 工作线程销毁单兵 action 发生崩溃；改以 Tick cave 执行动作操作。这是第三方源码证据，非本轮游戏动态验证。
- 用户上传 **memreader Plus 0.15.1** 的 `sites.lua` 明确 `STAYS={cave,frame,relocate}`，`remove` 对这些类型返回 `stays for the session`；安装时存在原字节及线程检查，但既不能保证对象生存期，也不能证明可逆完整卸载。
- 本地对上述两份实际 PFH5 pack 进行了 10/10 只读源码条件核对；不会在 GitHub 分发其源码、DLL、游戏 EXE。

## 禁止立即安装 live probe 的四个阻断

1. 被替换的七字节位于 63 字节原生 prologue 内，缺 Win64 寄存器/RFLAGS/XMM、stack alignment、unwind/异常处理及跨线程入口迁移的完整证明。
2. 当前 `RCX` 可定位同次成员 Tick，**但没有该成员/引用世界目标在其它线程中的并发生存期保证**；多个 member 的序列并非同一帧原子记录。
3. Derpy 可能已占用该入口，memreader 的 cave 是会话持久型；不能叠装、不能假设卸载安全。
4. R70 的 `member+0x23C` 模式清零与投影门槛之 Shift 特定因果仍为 BLOCKED；现在还没有可用的修复条件。

## 样本/源码来源与验证等级

本轮 ZIP：`BSC_R71_NATIVE_TICK_LIFETIME_UNWIND_STATIC_20261024.zip`。包含 **完整**离线检测器（还会检查 objdump 指令边界）、真实原始 EXE/第三方源本地检验 JSON、完整 Tick 反汇编、20 项本地离线测试（含真实 EXE+pack）、中文报告和历史 R70；不含商业或第三方二进制。

本 GitHub 提交提供可复现的**32 pin 精简 SHA/PE/UNWIND 检查器**、安全决策契约与独立的公开 CI 测试；公开 CI 中 EXE 测试应当 SKIP。测试成功不能代替游戏线程验证。

**R72 唯一优先事项：**只在离线私有测试进程中设计/验证可安全展开的极小 Native 观察 trampoline 或与原生线程同步的样本发布协议；须证明寄存器与 XMM/RFLAGS、原生 UNWIND、对象生命周期、单成员代际、固定容量无阻塞发布、失败回退。若无法达到这些门槛，不安装 WH3 Hook，不让用户反复实机测试。

`root_cause_proven=false`；`live_hook_authorized=false`；`gameplay_patch_authorized=false`；`main_unchanged=true`。
