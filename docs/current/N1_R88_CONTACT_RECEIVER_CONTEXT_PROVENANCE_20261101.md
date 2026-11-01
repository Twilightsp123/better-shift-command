# BSC R88 — 接触虚接收器上下文来源追踪（2026-11-01）

**EXE**: 232531920 bytes, SHA256 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496, PE AMD64 / ImageBase 0x140000000。所有地址为 RVA。原版游戏静态只读审计，不装 Hook、不发 gameplay patch。

## 新证据：接收者与接触双方不是同一个身份通道

Steering 0x03059BC8 内 0x03059BED 保存入口 RCX=member 到 RDI；0x03059CCA 执行 LEA R13,[RDI+0x58]。所以 R13 锁定入口成员的上下文**槽位地址**，而后续 RDI 可能因虚调用切换关联对象。

真实 EXE 中 0x0305A7B5: MOV RAX,[R13] 取得原成员上下文 C；0x0305A7CC: MOV RDX,[RAX+0x440] 得到 G；0x0305A7F4: MOV RDX,[RDX+0xF0] 得到 P。同时 0x0305A7C9: MOV RCX,RDI 是**当时的**第一个参与者，0x0305A7C1: MOV R8,RSI 为第二参与者。0x0305A800 E8 0F A9 02 00 调用 0x03085114。

在 0x03085114 内，0x03085147: MOV R13,RDX 保存 P；0x0308514A: MOV RBX,RCX 保存第一个参与者；0x03085230 / 0x03085258 将接触双方写入局部栈记录。0x0308529D: LEA RCX,[R13+0x1D8]；0x030852A4: MOV RAX,[RCX]；0x030852A7: CALL [RAX+0x10]。

因此这一分支的接收器来源可写作：入口 member M → C=[M+0x58] → G=[C+0x440] → P=[G+0xF0] → this=P+0x1D8 → vtable+0x10。**不能将 this 错认成当前 RDI+0x1D8 或确定的当前士兵。** R82 在特定成员构造路径上证明 [Root+0x38] 到 member+0x58 的来源；这仍不足以证明同一 Shift task / route generation。

## 有界的 vtable 搜索

对执行节做原始字节级寻址候选检索：188 个语法级 MOV [reg+0x1D8],reg，150 个 LEA RCX,[reg+0x1D8]；这些**未全部检查真实指令边界、控制流及对象类型，绝不当作确证 setter 数量**。部分紧邻 RIP LEA 的疑似 vtable 样本已读取 +0x10 入口，但均未找到能同时证明 C+0x440 与 G+0xF0 构造来源的 setter。例如 0x030F32BC 写入另一对象+0x1D8 的是 0x3F800000 数值位模式，不是候选 vptr。停止只凭偏移泛查。

## 严格验证和限制

用户原始 EXE SHA、19/19 指令完整字节、1/1 E8 目标和 6/6 PE unwind 范围通过本地静态脚本；8/8 unittest PASS，其中 1 项直接用原始 EXE。无游戏进程观察，无成员运动轨迹，无接触虚方法的已验证实际成员 XYZ/pending 写入，无 Shift 因果修复；无可发布补丁。

本会话没有 R87 完整历史 ZIP（只拿到 R87 GitHub 技术报告与交接），不能宣称当轮完整历史嵌套归档已经实现。

## 结论 / 下一项最小任务

R88_RECEIVER_CONTEXT_SOURCE = STATIC_PROVEN；R88_CONCRETE_RECEIVER_TYPE = NOT_PROVEN；CONTACT_TO_MEMBER_MOTOR_CAUSAL_EDGE = NOT_PROVEN；SHIFT_CROWDING_ROOT_CAUSE = NOT_PROVEN；HOOK_AUTHORIZED=false；GAMEPLAY_PATCH_AUTHORIZED=false。

优先类型化 [C+0x440] 与 [G+0xF0] 的创建/赋值，定位 P+0x1D8 虚表安装及具体 +0x10 接收函数，再按成员同实例检查 pending / 实际 XYZ / 导航目标是否受影响。若界限内追不到，退出事件系统并转向原生阵型转向相位和世界目标的协调机制。禁止恢复 Lua 重发 MOVE、盲改常量或泛扫 member+0x738。