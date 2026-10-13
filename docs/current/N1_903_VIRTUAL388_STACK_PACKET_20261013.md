# BSC N1 — virtual+0x388 三条原生栈记录来源（2026-10-13）

## 实际验证
使用 SHA256 完全匹配的 WH3 9.0.3 EXE：518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a。只读审计对原始机器码实跑：24/24 opcode + unwind + objdump 指令起点、3/3 E8 上游来源、3/3 同函数局部记录的 virtual+0x388 分发 PASS；本地 7/7 单元测试 PASS。

## 新增直接几何参数来源证据
函数 0x03010724 的 prologue：0x0301073F 将 RBP 设成进入函数时的 RSP-0x128，0x03010746 将 RSP 再下移 0x1E8，说明 RBP 是当前调用的栈帧基准，不是指向 MOVE task 的寄存器。其下三条虚函数 +0x388 的调用点：

| virtual+0x388 call | 之前 RDX 赋值 | 当前记录更新 |
| --- | --- | --- |
| 0x03010B0F | 0x03010AFC LEA RDX,[RBP+0] | OR byte [RBP+0x6C],0x20；movss [RBP+0x58] |
| 0x03010DAE | 0x03010D9B LEA RDX,[RBP+0] | 同样两项 |
| 0x03011078 | 0x03011065 LEA RDX,[RBP+0] | 同样两项 |

三条路径都先从 [RDI] 读取虚表到 RAX，将 RDI 送到 RCX 作为接收对象，再 call [RAX+0x388]。各自上游都有一条直接 E8 到 0x030A48A4，得到其计算/门槛处理结果后才写本地浮点。因此：**对这三条已经确认的 callsite，其 RDX 指向局部栈记录，不能宣称直接等于 task+0x160 的 nextSubtask 指针。**

这是一个有界的正向参数来源证明，不是全游戏每个 +0x388 调用者的穷尽：别的对象虚表可能具有同偏移；这三次对何种动态成员 vtable 具体命中仍无运行时指针身份。0x03010724 内另有 [RBP+0x158]，它是局部栈偏移，不能误判成 MOVE task+0x158 字段。

## 与 Native 修复有关的下一条真正因果边
下一步先检查 0x030A48A4 的原生输入和返回分支，沿这份本地记录的浮点目标数据追向真正的 MOVE 几何来源，再按成员身份与 old/new route generation 作配对。不得根据栈记录 RDX 与 task+0x160 的布局相似直接补丁。当前没有足够证据证明原生 crowding 根因、发布修复 DLL 或改写 CA 原生渐进转向。

新增 audit_virtual388_stack_packet.py、test_native_shift_re_virtual388_stack_packet.py 与脱敏 evidence JSON。原始 EXE、含指针原始 JSONL 没有提交 GitHub，不修改 main，不要求玩家重测 Shift 挤压。


## 第6轮静态类型校正

本文件的3条栈参数来源在调用点范围内成立，但上游0x030A48A4不是直接生成几何记录的函数；0x02F5FCAC/0x02F5FE28此前被遗漏为两类原生record构造器。五条0x030A48A4调用分别可通向3条virtual+0x388或2条virtual+0x380。最重要的是，相关查询0x03039C7C使用与MOVE队列相同的root+0x2A0/index*0x120槽位布局，但MOVE槽位vtable 0x0390B4F0的+0xB8固定返回false，故不能说所有Shift MOVE无条件执行此特殊几何路径。详见docs/current/N1_903_MOVE_QUEUE_MEMBER_GATE_20261013.md。
