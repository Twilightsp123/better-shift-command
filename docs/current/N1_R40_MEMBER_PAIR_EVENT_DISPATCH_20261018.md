# BSC 第40轮（本对话第6轮）：新版 EXE 邻近响应虚调用的具体事件分发器及两个订阅者

日期：2026-10-18；只读静态审计，没有安装 Hook，没有更改游戏 EXE，也没有 gameplay patch。

## 版本身份和限定校验

- NEW Win64 Warhammer3.exe: SHA256 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496；232531920 bytes；PE ImageBase 0x140000000。全部机器码位置是 RVA，ASLR 下须加实际模块基址。
- 使用用户提供的真实新版 EXE：99/99 完整指令起点与字节；9 个 unwind 函数、3 个显式无 unwind 叶函数；6/6 已列直接 E8；6/6 已列虚表槽。本地14/14 unittest PASS（含真实 EXE），无 EXE 时13 PASS / 1 SKIP。不是 Windows 游戏内 Shift 命中或公开 GitHub CI 结果。
- 对 0x03085114 在新版可执行节中的所有真实直接 E8 调用进行扫描，仅有四处：0x0305A800、0x030803FC、0x0325438B、0x03265B81。间接调用未排除。

## 1. 原先未知的 virtual+0x10 已类型化

普通成员 steering 0x03059BC8 在 0x0305A800 调用 0x03085114。响应函数收集当前 member、另一 member 和空间/接触参数，0x0308529D 形成 RCX = response manager + 0x1D8，0x030852A7 经 [vtable+0x10] 调用。此 RCX 不是士兵对象，不得用相同字段偏移误判为 member 速度写者。

原生 context 构造 0x02D9A004 的 0x02D9A373 E8 调 0x02DA0800 创建管理对象，0x02D9A381 写 owner+0xF0。管理对象构造器依次在 +0x1D8 安装初始虚表 0x03AAF7F0（0x02DA09FE），随后安装最终虚表 0x03AB1B48（0x02DA210E）。两表 +0x10 的实际地址均指向 0x02DD06F0。steering 侧 [source+0x440]+0xF0 读取该 manager。

0x02DD06F0 并非直接成员运动积分器，而是事件广播器：

- 0x02DD0735/0745 从通道订阅数组取得 listener。
- 0x02DD0753 调 listener virtual+0x10（判断条件）；符合条件才在 0x02DD0763 调 listener virtual+0x08（传入当前接触记录）。
- 若有 listener 条件不满足，0x02DD0793 E8 到 0x02D8E774，将接触记录追加到 channel+0x30 的延迟事件队列。该数组的固定记录步长为 0x38 字节（0x02D8E7AD）。不等于已类型化整个延迟消费链。

## 2. 两类确定的订阅者回调也只是事件队列转发

订阅者 A：构造函数 0x02F9AF4C；0x02F9B170 LEA R10,[R11+0x1F8]；0x02F9B2F6/Fd 在该子对象安装真实虚表 0x03AD0678；0x02F9B64A 通过 0x01C3ADF0 注册到 manager+0x1D8。此表 +0x10 = 0x008D5490（读 listener+0x20 的 byte）；+0x08 = 0x02FF0520（读 listener+0x460，加 0xC0，然后 tail JMP 0x02D8E774）。

订阅者 B：构造函数 0x02F9C9C4；0x02F9CAD5/DC 在 +0x40 子对象安装 0x03AD0328；0x02F9D394 通过同一注册器安装到 manager+0x1D8。此表 +0x10 = 0x008D5490；+0x08 = 0x02FF0680（读 listener+0xC8，加 0x10，然后 tail JMP 0x02D8E774）。

两个已定型 listener 构造器都将其 +0x20 判断位初始写为零，但后续修改者未穷尽，不能宣称回调永远不执行。其它 listener 是否也只是转发队列未证明。

## 3. 研究排除条件与下一步

- 已证：原先 0x03085114→context+0x1D8→virtual+0x10 这根边，直接实现是事件分发而非 member 实际速度/位移提交；两种具体 listener 的直接回调同样仅转发队列。
- 未证：全部 listener 回调、延迟队列最终消费者、事件间接运动效应、真实 Shift 折返命中此通道、异常速度或世界目标因果。
- 止损：不继续泛扫所有 0x01C3ADF0 订阅点；接下来优先从普通 member Tick 和真实速度/位移的写入者沿对象类型及条件返回追查。不得全局 NOP 此分发器，不能误伤 CA 原生 RMB、Shift ATTACK、渐进转向与避障。
- native_patch_authorized=false, root_cause_proven=false, player_shift_instance_proven=false。旧游戏 EXE 不上传，也未修改 main。

## 4. 复现材料与同步范围

本轮完整离线资源：BSC_R40_PAIR_RESPONSE_EVENT_DISPATCH_20261018.zip（不含游戏 EXE），含 99 条精确字节指令清单、完整 SHA 防错审计器、14 项本地测试、证据 JSON、有限反汇编、前一轮 R39 完整 ZIP。GitHub 本文是精要归档；离线包才包含全部源码测试证据，不得把缺失源码的远端 CI 宣称 PASS。
