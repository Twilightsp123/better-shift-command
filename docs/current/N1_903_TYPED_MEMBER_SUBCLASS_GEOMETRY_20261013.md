# BSC N1 — 9.0.3 类型化成员几何分发与错误 +0x88 写入候选 (2026-10-13)

## 原始 EXE 实测
用户提供的原始 EXE SHA256 518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a。
本轮单独原始文件只读审计通过：29/29 opcode 和 objdump 指令起点、5/5 E8、2/2 E9、3/3 RIP LEA、18/18 typed member vtable slots；本地 8/8 测试通过（含真正原始 EXE）。这是 STATIC，不是实机命中，也不是 Native 补丁。

## 纠正旧对象类型：0x0390FE38 不属于未知 MOVE controller
真实构造器 0x030EE464 于 0x030EE4D0 调用基类构造 0x030EE380，再在 0x030EE4D5 LEA 0x0390FAB0，0x030EE4DF 将它写入同一对象的主 vtable。这个类型的核心槽位如下：

| 成员类 vtable | +0x260 | +0x348 | +0x368 | +0x388 | +0x580 | +0x5B8 |
| --- | --- | --- | --- | --- | --- | --- |
| 0x0390FAB0 | 0x008D3330 | 0x0306B510 | 0x03117CE0 | 0x03117D44 | 0x0306A990 | 0x0306A8C0 |
| 0x038FD658 | 0x008D3330 | 0x0306B510 | 0x0306B9F0 | 0x0306C0DC | 0x0306A990 | 0x0306A8C0 |
| 0x03910500 | 0x008D3330 | 0x0306B510 | 0x0306B9F0 | 0x0306C0DC | 0x0306A990 | 0x0306A8C0 |

因此原来标为 controller 的指针槽 0x0390FE38 = 0x0390FAB0 + 0x388，实际是具体成员子类的接口。该类 +0x368 走 0x03117CE0，在守卫后尾跳到原生接收器 0x0306B9F0。+0x388 走 0x03117D44，再 CALL 0x0324983C 组装成员几何记录，CALL 0x03117E8C 进行逐成员分发。这是确认的同类型方法关系。

固定的成员子类 +0x260 指向原生 0x008D3330，其完整短函数字节为 32 c0 c3（xor al,al; ret）。在该 vtable 不变时，0x03117D44 的初始 +0x260 非零跳过门槛不会满足，故能够执行几何记录创建；并不保证其下游每个成员都安装动作。

## 实际成员处理有分支
0x03117E8C 读取 owner+0xB64 数量与 owner+0xB68 指针数组。对每项成员，它判断 record+0x68 的 0x40/0x02 位、该成员当前 +0x330 动作状态和其它虚函数结果，在 0x03117EF7 / 0x03118040 等位置可能调用 member virtual+0x5B8，而不是无条件向每个人发送相同目标。因此挤压因果更应该比较同一 MOVE 交接中相邻成员实际走的动作安装分支、目标对应与记录代际。

## 两个明确排除的 +0x88 写入候选
0x0326F4C4 是在第三处理器注册方法区域出现的函数，但是它先调用分配器建立 0x90 字节新对象，安装另一虚表 0x03915038，随后 movdqu [rbx+0x80],xmm0 写入这份新对象 +0x80..+0x8F。这个 SIMD 操作覆盖数值偏移 +0x88，**目标却不是第三处理器 object+0x88**。另一个 0x0326519B 写 +0x88 的函数属于安装 0x03ADDE08 的不同类。不能跨类型误归因。

## 未解决边界 / 禁止误用
仍没有证明 0x03117D44 的输入几何实例和 task+0x160 后继 MOVE 子任务同一个指针；没有证明这个具体成员子类就代表 RMB 或 Shift；也尚未定位 member 目标分配造成物理挤压的精确错误分支。因此本轮无 gameplay patch，native_patch_authorized=false。

新代码：maintenance_tools/native_shift_re/audit_typed_member_subclass_geometry.py；测试：tests/test_native_shift_re_typed_member_subclass_geometry.py；脱敏证据：maintenance_tools/native_shift_re/evidence/20261013_typed_member_subclass_geometry.json。
不得上传原始 EXE 或用户运行时指针 JSONL，不修改 main。


## 2026-10-13 新证据：同一原生方法链的三条 virtual+0x388 参数来自栈局部记录
详见 docs/current/N1_903_VIRTUAL388_STACK_PACKET_20261013.md。原始 EXE 24/24 opcode/unwind/objdump、3/3 E8、3/3 virtual+0x388 入口检查 PASS。函数 0x03010724 用 RBP=entry RSP-0x128、额外分配 0x1E8 栈，分别在 0x03010B0F / 0x03010DAE / 0x03011078 之前 LEA RDX,[RBP+0]，并更新局部 [RBP+0x58] float、[RBP+0x6C] bit 0x20。**这三条调用的几何输入是栈上临时记录，不是直接传 task+0x160 指针。** 该调用者内 RBP+0x158 也是栈局部/传参位置，不能和 task+0x158 混淆。每次上游调用 0x030A48A4，后续必须逆查实际几何数据来源与同一 MOVE 实例。其余 v+0x388 调用者的对象类型尚未定型，禁止假定属于这个成员子类；无 gameplay patch。
