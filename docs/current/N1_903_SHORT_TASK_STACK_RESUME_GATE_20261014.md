# BSC N1 — 9.0.3 shortTask 同源任务栈、栈顶分发与旧任务再激活门槛（2026-10-14）

## 结论（覆盖旧跨代假设中的过度推断）

对用户原始 SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` 的 Win64 EXE 重新进行 **69/69 opcode+objdump 指令起点、13/13 E8、5/5 分支目标、4/4 真实虚表槽**的静态审计；额外 13/13 本地回归 PASS（包含实际原始 EXE）。只读，无游戏 DLL/EXE 修改，无玩家新测试。

**旧 shortTask 仍存活 != 旧 shortTask 还能继续下发成员包。** 原生 shortTask 与 MOVE 命令经过真实构造器使用同一个 `UnitRoot+0x2FA0` 任务管理器；`0x03043520` 当前只对最后一个任务执行 `virtual+0x10`，较早的 shortTask 被调的是空 `virtual+0x18`。但最后一个完成且出栈后，较早 shortTask 可能重新成为最后任务；此时仍必须检查自己的状态，不可反过来认定跨代发生。

## 1. 任务管理器不是同结构猜测：从真实构造器贯通

```text
0x030078E4 UnitRoot 构造器
  0x03007AD1   RAX = &root+0x2FA0
  0x03007B5B   [root+0x278] = root
  0x03007B62   [root+0x280] = RAX
                   （以上区间无 call / RAX 写入）

0x030323C8 MOVE 命令发放
  0x030326B4   RCX = &root+0x278
  0x030326BE   CALL 0x02F50410
  0x02F50460   读取 queue+0x08（= root+0x280）
  0x02F50493   复制到新 wrapper+0x10
  0x030326CE   RCX = &wrapper+0x18
  0x030326E4   CALL 0x030090BC（真实 MOVE vtable 0x0390B4F0）
  0x030090CC   CALL 0x03008814
  0x0300884D   读取 wrapper+0x10
  0x03008851   [MOVE slot+0x18] = 该管理器指针

0x03025D70 MOVE 激活
  0x03026084   RDX = [MOVE slot+0x18]
  0x03026091   CALL 0x02F2FFB0：按管理器+0x240计数，在+0x200处追加16字节记录
  0x030260AF   CALL 0x02F2C734：构造shortTask，安装0x03ABBE18虚表
```

因此 MOVE slot 的 `+0x18` 与普通 MOVE 命令内部的 `root+0x2FA0` 管理器有直接字段归属关系，**不能与跨队列复用的大任务 `MOVE slot+0xA0` 混成同一指针**。

## 2. 管理器的栈顶更新规则

原生单位更新 `0x03043648` 在符合单位成员非空等分支要求时：

1. `0x03043769/70`：调用 `0x0304433C(&root+0x278)` 执行 MOVE 队列推进。
2. `0x03043775/7C`：随后调用 `0x03043520(&root+0x2FA0)` 执行任务 Tick。

在 `0x03043520` 内，管理器 `+0x240` 是槽位计数，`+0x200+16*i` 是槽位对象指针及附属数值；它比较当前索引 `i` 与最后索引 `count-1`：

| 条件 | 原生执行 | shortTask vtable `0x03ABBE18` |
|---|---|---|
| `i == count-1` | `0x0304357D call virtual+0x10` | `0x02F561E8` 可进入分发 |
| `i != count-1` | `0x0304359E call virtual+0x18` | `0x008D3280`，机器码 `c2 00 00`，空返回 |

最后一项完成字节 `task+0x18==1` 时，`0x0304358E E8 → 0x02F4FD5C` 可退栈、减少管理器 `+0x240`；于是此前非最后的 shortTask **可能在未来 Tick 重新成为最后**。但每条虚调用也还有管理器 `+0x250/+0x251` 和任务本身的条件，不能认定任何旧 shortTask 必定重新运行。

## 3. shortTask 的发包门槛与重要纠错

`0x02F561E8` 在 `0x02F562C0` 检查 `shortTask+0xA0`，非零时跳过这次新的成员分发准备；关联任务还需满足 `+0x20==4`、`+0x24!=0`。但 `+0xA0` **可以被重新清零**：在此之前 `0x02F56223` 检查关联任务 `+0x25`，若非零，则在 `0x02F5622D` 写 `shortTask+0xA0=0`，同时执行其它清理，包括在 `0x02F56282` 清理当前 UnitRoot 关联 group 状态。

另外 `shortTask+0x74` 是**分支选择**而非无条件必备的「发包许可」：

- `+0x74!=0` 的受限路径会通过 `0x02F56358 → 0x03263D68` 构造描述符。
- `+0x74==0` 则在 `0x02F56310` 跳至 `0x02F5640E`，在 `0x02F56431 / 0x02F56460` 使用另一种描述符函数，随后 `0x02F56465` 跳到公共分发准备 `0x02F563F4`。
- 公共分发仍在 `0x02F563F4` 动态读取 `shortTask+8` 的 UnitRoot，`0x02F563FD` 读取当时的 `UnitRoot+0x32F8`，`0x02F56404` 条件性调用 `0x03279E40`。

所以旧报告中把「`shortTask+0x74` 为真」写成必要发包门槛的表述应纠正为「选择不同的构造路径」。两条路径**静态上都能到达**共同的调用点；不说明玩家当次一定命中。

## 4. 旧 group 被对象池回收后，究竟还能否发生跨代分发？

这次进一步缩小了判断条件：

| 离线序列（独立合成，不是 CA 时间轴） | 旧 shortTask 可能被 Tick 调用吗？ | 跨代发包结论 |
|---|---|---|
| 新 shortTask 已入同管理器、仍是最后任务 | 不会通过该路径调用旧 shortTask 的 `+0x10` | 此条件下排除旧任务即时发包 |
| 新 shortTask 完成并被弹出、旧任务重新成为最后一项 | 可以再次接受 `+0x10` 调用 | 是否发包取决于 `+0xA0` 和关联状态 |
| 旧 shortTask 的 `+0xA0` 已为1、且未触发重置 | 即使旧任务成为栈顶，也跳过新的发包分支 | 此条件下排除 |
| 旧任务被关联 `+0x25` 触发 `+0xA0` 重置，且共享状态仍有效 | 静态上存在再次准备参数的路径 | **仅为条件性可达，不是实机证据** |

因此不应该在 `UnitRoot+0x32F8` 或 `shortTask+0xA0` 上直接安装全局跳过 Hook；那样可能破坏合法的任务压栈/恢复、普通 RMB、Shift ATTACK 及 CA 原生转弯和避障。

## 5. 这一阶段还缺哪一条“决定能否修复”的证据

主要剩余的是**任务对象实际被替换/恢复时，关联状态到底是否允许旧 shortTask 用旧几何再发一次包**。直接调查 `0x02F4FD5C` 的具体调用条件、MOVE→MOVE 交接是否真正追加 shortTask，以及重新成为栈顶后的 `+0xA0` 重置、当前 group 对应关系；全部按原始机器码与同一对象类型证明。

只有确认这一具体序列可能破坏同一兵牌成员目标对应时，才定位最小 Native Patch。尚无跨代实例命中、相邻士兵错误目标的因果证据；`native_patch_authorized=false`。没有写游戏内存、EXE、DLL 或 `main`，也没要求玩家重复折返测试。

附带 `audit_move_shorttask_resume_gate.py` 和 `test_native_shift_re_move_shorttask_resume_gate.py`、机器可读静态证据。原始 EXE 及含内存指针日志不上传 GitHub。


## 2026-10-14 优先纠错：正常成功 MOVE→MOVE 交接清退旧 shortTask

见 `docs/current/N1_903_QUEUED_HANDOFF_TASK_MANAGER_RESET_20261014.md` 及同名只读审计工具。固定原始 EXE 72 opcode/objdump、11 E8、1 E9、6 branch、6 vtable 全部通过；本地 14 项测试 PASS。成功继承时下一 MOVE +0x48 接受旧**大 task**，但 `0x030445B1` 先 pop 旧 MOVE，`0x030445BA/BC` 以 EDX=0 调用 `0x02F4FD5C(queue+8 manager,0)` 清空旧 **shortTask**，然后 `0x030445CB` group 清理，再 `0x030445D3` 激活后继槽位。此清理受 manager+0x250!=0 门槛约束，正常单位更新 tick 退出会恢复该字节为1；manager+0x250==0 及继承失败分支均不能据此排除。故以前将正常成功继承的跨代挤压归因于旧 shortTask 被新任务压栈后复活，应当降级/排除。继续聚焦保留的大 task state1 几何、当前 group 的成员目标索引及 motor，不发布 game patch。
