# BSC R72 — 独立 Native 观测微实验（2026-10-24）

**阶段：离线独立进程实验，不修改 WH3，不安装 Hook，不是游戏补丁。**

## 已完成的实际施工

在 maintenance_tools/native_shift_re/r72_native/ 新增完整 C++17 固定容量 MPSC 环形队列（序号 + release/acquire），测试 4 个并发生产者、1 个消费者、满队列有界丢弃、循环复用、线程退出和 Epoch/匿名 token 拒绝。每个事件是 32 字节、纯值类型；生产者热路径不分配堆内存，不读取游戏成员指针。消费者和测试本身可以使用 std::set 分配内存，这不代表生产端发生分配。

Linux Release 实际编译执行并通过 CTest **2/2**；在合成负例中，80,000 次发布尝试满足 accepted + dropped = 80,000，读出事件无重复。GCC UBSan Debug 也通过 CTest **2/2**；13/13 Python 事件协议测试拒绝跨 Epoch 混淆、重复/乱序、原始指针字段并强制声明跨成员非原子性。数量是测试样本数，不代表游戏帧性能或无竞态形式化证明。

## Windows x64 专用实验（与 Linux 区分）

独立的 Win64 MASM 文件 win64_abi_fixture.asm 使用 PROC FRAME、pushreg/allocstack/savexmm128/endprolog 定义完整 UNWIND 元数据，保存其用到的非易失 GPR 和 XMM6–15；C++ windows_context.cpp 校验 nonvolatile 哨兵、callback 期间的 CF 恢复、RtlLookupFunctionEntry 以及 synthetic SEH RaiseException 跨 MASM 帧展开。

**请以 Windows GitHub Actions 作业实际结果为准**。Linux CTest 不能代替 Windows/MSVC/MASM/SEH 测试。即使 Windows 通过，该程序只是自有测试函数，不是游戏中途 Tick detour；它不能证明原游戏 7 字节 stolen prologue、全部易失寄存器/XMM0–5、RIP 重定位、跨线程安装与恢复、安全异常展开以及活成员生存期。

R72 workflow 位置：.github/workflows/r72-native-fixture.yml；Windows-2022 x64 编译与 CTest 独立运行，不生成或发布游戏 DLL/PACK。

## 原 EXE 与第三方约束

本地重新核验用户 EXE SHA256：9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496，大小 232531920。R71 所确认的 member Tick RVA 0x03086F04 和 63 字节 prologue 仍是研究范围。Derpy 已可能占用同一入口；memreader Plus 0.15.1 Cave 为会话持久型。R72 **没有**尝试碰触其原码或加载第三方 DLL。

## 最重要的未闭合问题

1. 单位/成员对象真实生命周期、跨线程别名与 world-goal 引用帧的生存期依然未知；Epoch 是合成值，不是已证实的游戏代际。
2. 不同成员 Tick 的事件不能作为同一时间戳的全兵牌原子快照；未证明 queued Shift 任务与特定成员状态存在同实例身份。
3. Win64 ABI 成功（若通过）只覆盖自建测试帧，不能授权覆盖游戏 Tick 原生 prologue 或执行逆向修改。
4. R70 状态清零导致挤压的假说继续为 SHIFT_CAUSAL_LINK_BLOCKED。

## R73 单一任务

在现有离线 MPSC/ABI 基线之外，优先研究**无需占用普通成员 Tick 序言**的同实例原生任务身份与运动事件关系；若无法证明对象生命周期、线程/异常展开、原码恢复与排他性，维持 LIVE_HOOK_NOT_AUTHORIZED，禁止要求玩家反复安装实验性 Hook。任何未来游戏观测须先有可撤销方案、单次预算和失败回退。

交付的独立 ZIP 包含完整源、真实 Linux/UBSan 日志、同 SHA EXE 身份核对结果和 R71 既往 ZIP；不分发商业 EXE、第三方 pack/DLL 或用户指针日志。

**根因状态：** root_cause_proven=false；member_lifetime_proven=false；game_hook_authorized=false；gameplay_patch_authorized=false；main_unchanged=true。
