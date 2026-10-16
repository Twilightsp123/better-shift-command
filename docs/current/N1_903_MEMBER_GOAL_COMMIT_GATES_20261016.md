# BSC N1 — 第21轮：成员路线写入与最终目标提交条件（2026-10-16）

## 证据

用户固定原始 Win64 Warhammer3.exe 的 SHA256 为 518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a，ImageBase 0x140000000；地址均为 RVA。

本轮独立原始 EXE 的只读验证通过 **60/60 原始机器码及 GNU objdump 指令起点、5/5 E8 调用、8/8 条件跳转**。精确读取常量 0x0391CCFC 为 float32 0.01。遍历整个可执行节并过滤真实 E8 指令起点，找出最终目标函数 0x0311954C 的 **8 个直接调用点**及路线安装函数 0x03071E04 的 **25 个直接调用点**。本地 **12/12 回归 PASS**（含私有原始 EXE、错误版本拒绝、Python -O 检查）。这属于 EXACT_ORIGINAL_EXE_STATIC，不代表用户 Shift 折返执行命中。

## 首次具体的成员级运动状态边界

动作 0x03913808 的 virtual+0x10 为 0x0325E294；其中一个原生分支在 action+0x7C/0x78、member+0x18F/+0x898、action+0x6E 等门槛满足后，0x0325EA85 调 0x03071E04 安装路线，0x0325EA8A 设置 action+0x7D=1。此门槛对**每个成员独立评估**，没有在这条分支发现全兵牌等待屏障；仍然存在其它成员目标入口，不能由此断言物理运动必不同步。

路线安装器 0x03071E04 向对应 member+0x7F8/+0x808 与 member+0x818/+0x828 写两组记录，把 member+0x710 设为1，然后调用 0x03071F20。后者在 0x030720E3 与 0x030723D9 有条件调用 0x0311954C。

最终目标写入器 0x0311954C：
1. 当 member+0x228==1 可提前返回。
2. 当旧 member+0x30 非空且 flags bit15 未置位，可改经 0x03126F64 处理而不经过本函数直接提交。
3. 当 flags bit9 没有置位，且旧 member+0x1F0 token 与新输入+0x10 一致、member+0x1EC 朝向与新输入+0x0C 一致，三个目标坐标差值均不超过 **0.01** 时，跳过目标重新提交；bit9 可以绕过此去重。
4. 在允许写入的分支，于 0x0311963A 把连续16字节目标更新到 member+0x1E0，随后更新 +0x1F0 token、+0x180 标量、+0x188 flags。

**结论限制：** 群组一次成员发包不等于所有成员在同一时刻接受同一个最终 motor goal；但上述是合法引擎控制流，不等于已证明缺陷。尤其去重阈值 0.01 本身不足以解释明显的整队相向穿插。

## 接下来不再扩大泛查

下一条唯一有价值的因果比较是同一 UnitRoot、同一 group generation、同一 queued MOVE 路段内两个邻兵：
- member[i] 与 record[i] 的身份和 kind；
- action+0x7D 锁存及 +0x78/+0x7C 条件；
- 0x03071E04 路线安装是否发生；
- 0x0311954C 是否接受新目标、token、heading 和目标坐标；
- 若都一致仍有碰撞，立即转到逐帧 steering/avoidance 的速度和碰撞修正，不再继续查路线包。

此前 NULL 结果/辅助 B 节点边界的静态证据仍有效，但没有真实游戏因果，应该降为低优先级。不要改共享目标函数、清任务指针或取消渐进转弯。用户的 Shift 折返内部挤压已经确认，不需要重新证明。没有玩法补丁，native_patch_authorized=false。

## 资源

只读证据与自动回归：maintenance_tools/native_shift_re/member_goal_commit_pins_20261016.txt、audit_member_goal_commit_gates_20261016.py 和 tests/test_native_shift_re_member_goal_commit_gates_20261016.py。完整离线资源包 BSC_R21_MEMBER_GOAL_COMMIT_AUDIT_20261016.zip 包含原始反汇编、12项本地测试和脱敏 JSON，不包含游戏 EXE。
