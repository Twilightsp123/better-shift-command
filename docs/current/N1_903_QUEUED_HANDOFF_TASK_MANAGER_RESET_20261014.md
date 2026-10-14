# BSC N1 — 2026-10-14 成功 MOVE→MOVE 移交后的 shortTask 管理器清退

## 固定 EXE 机器码证据

使用 SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` 的原始 x64 EXE 独立只读审计，已完成 **72/72 opcode/unwind/objdump 指令起点、11/11 E8、1/1 E9、6/6 branch、6/6 typed vtable**，本地原始 EXE+合成回归 14/14 PASS。这不是游戏运行时分支证明，也不是已修复 MOD。

原始 `0x0304433C` 仅当 queue count>1、源 MOVE +0x40 提供可复用大 task、后继 MOVE +0x38 接受时走成功移交：
```text
0x030445AB   下一 MOVE +0x48 接收旧大 task（保留 state1 连续性）
0x030445B1   CALL 0x02F4FD10       从队列 pop 旧 MOVE 槽
0x030445B6   RCX = [queue+0x08]    已确认是 UnitRoot+0x2FA0 管理器
0x030445BA   XOR EDX,EDX          保留任务数量目标为 0
0x030445BC   CALL 0x02F4FD5C      尝试清空全部旧 shortTask
0x030445CB   CALL 0x030CFAC4      清理 group 调度状态
0x030445D3   CALL 0x030433B0      条件激活下一 MOVE
```
以上顺序属于同一个 unwind 所属函数的原生执行路径，调用目标经真实 E8 rel32 校验。**共享大 task 复用不等于短期 shortTask 继续存活**。

### 清空是有门槛的

`0x02F4FD5C` 在 `manager+0x250=0` 时直接退出；若非零，则逐个清退 `manager+0x200+16*i` 栈尾任务，使用每个任务虚表+0x00（EDX=1），减 `manager+0x240` 直到目标为0，最终恢复 `+0x250=1`。常规单位更新先 `0x03043770` MOVE 队列，再 `0x0304377C` 任务 Tick；后者退出时恢复管理器 `+0x250=1`。

因此**正常、非重入、成功 MOVE→MOVE task 继承**已排除旧 shortTask 被新任务压住后再恢复发包的假设。但失败继承、其它类型命令、`+0x250=0` 重入例外不能由此排除，更不能声称某次玩家 Shift 实机已经命中这些分支。

### 下一项真正应研究的对象关系

不再优先沿旧 shortTask 的 `+0xA0` 复活猜想寻找补丁。应沿**保留的共享大 task**的 state=1 旧方向投影，经新 shortTask、新 group 和成员 `record[i]` 目标生成，检查个人朝向/位置修正后相邻成员的局部目标是否交叉。仍要保持 CA 原生队列、渐进转弯、寻路、避障、普通 RMB 和 Shift ATTACK。

新增 `audit_queued_handoff_manager_clear.py`、同名回归测试、脱敏 evidence JSON，并更新 current 与 AI handoff。无原始 EXE、原始用户指针 JSONL 或游戏补丁提交。
