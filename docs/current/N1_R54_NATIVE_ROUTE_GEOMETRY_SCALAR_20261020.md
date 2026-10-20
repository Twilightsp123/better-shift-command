# BSC 第20轮 / R54：真正的原生路段几何标量及朝向修正数据流

日期：2026-10-20。研究目标：**让 CA 原生 Shift 连续折返更加流畅**，而不是用 Lua 重写 Shift，也不以减少转向速度掩盖穿插问题。

## 1. 版本、核验类型和限制

- 用户新版 Windows x64 `Warhammer3.exe` SHA256：`9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`。所有地址均为 RVA；静态只读、无进程注入。
- 本轮独立校验：**84/84 完整原始指令字节和 GNU objdump 指令起点、10/10 E8 目标、2/2 converter 直接条件分支、1/1 上游 rich/inline JCC**，涉及 PE unwind 函数和被编译器省略 unwind 的真实短叶函数 `0x030F1B3C..0x030F1B98`。
- 14/14 本地 `unittest` PASS（其中 1 项直接读取真实 EXE）；无 EXE 为 13 PASS / 1 SKIP。CI/mock 与真实 EXE 静态校验分开记录。**没有 Windows 游戏内实测和 Native gameplay patch**。

## 2. R53 纠错：0x030F1B3C 不是曲率求解器

`0x030F1B3C` 是无 unwind 的描述符构造短叶函数（真实终止 `RET=0x030F1B98`）。它把输入目标记录中 `[r8+0x00..0x20]` 复制进 `desc+0x18..0x30`，并写：

- `0x030F1B86`: `desc+0x38 = R9W`（16 位朝向）；
- `0x030F1B7C`: `desc+0x3C = float([caller RSP+0x20])`；
- `0x030F1B8B`: `desc+0x40 = 0`；
- `0x030F1B81`: `desc+0x44 = float([caller RSP+0x30])`；
- 其余 `+0x48`、`+0x4C` 是描述符初始化。**本体没有转弯半径算法、没有求解器 E8。**

原 `0x030F1B3C` 为叶函数，被 R53 当作“重点找曲率”的候选；现在应该把逆向关注点移至下游几何转换而不是在叶函数中猜字段。

## 3. 两个后继朝向均进入 rich geometry 路由

R53 已确认新版 `0x0302AE74` 后继 MOVE 分为保存的 `slot+0x98` ushort 方向和按当前 Group 点至目标的 live 方向。**本轮新证据**：

- `0x0302AF87 MOV BYTE PTR [rsp+0x28],1`（预存 heading 分支）；
- `0x0302B114 MOV BYTE PTR [rsp+0x28],1`（live heading 分支）；
- 两者调用共同路线配置器 `0x030179B0`，Win64 调用约定下上述位置是其**第六参数**；
- callee 先 push rdi、分配 `0xA0` 栈，在 `0x03017A28` 检测自身 `[rsp+0xD8]` 的第六参数；若零，`0x03017A30 JE 0x03017AC4` 跳入 inline 路径，非零则执行 rich 路径。

因此**在满足函数前置成功条件的这两个后继 MOVE 调用里**，都会执行 rich 处理（并不意味着后续 converter 的全部条件都成立）。不能把“rich vs inline”简单解释为玩家键盘 RMB/Shift 两种类别。

## 4. 真正涉及几何修正的链路

```text
route_config 0x030179B0
   ├─ 0x03017A36 读取 Root+0x32F8 当前 Group
   ├─ 0x03017A47 取 Group+0xB30 的关联对象
   ├─ 0x03017A4E → 0x030D6A0C
   │       这个薄包装器调用对象 virtual+0x20，随后跳 virtual+0x28
   │       返回 scalar_A（具体对象类型/物理语义尚未知）
   ├─ 0x03017A53 读取 Root+0x1D0 scalar_C
   ├─ 0x03017A79 → 0x030F1B3C 组装临时记录
   │       heading+0x38, scalar_A+0x3C, zero+0x40, scalar_C+0x44
   ├─ 0x03017AB6 → 0x0300D948
   │       └─ 0x0300D984 → 0x03126A58，经过 group routeContext+0x160
   │           ├─ 0x03126AE8 复制完整记录到 route node+0x20
   │           └─ 模式/记录标志条件满足，0x03126B41 → 0x03102B28
   │               ├─ 0x03102B76/7F: xmm6=record+0x3C - record+0x40
   │               ├─ 0x03102BE2/F7/FC: heading 查表取得二维参数
   │               └─ 0x03102C2D..5A: 用0.5系数修正两维目标点
   └─ 0x03017ABB 条件发布 Root+0x270 route binding
```

注意 `0x03102B28` 就是**旧版研究过的转换器 `0x030FDA9C` 的新版对应地址**，不是“发现新的 CA 求解器”。旧研究曾追踪它的条件 NULL 返回与候选不变量，但尚未把这条 *具体浮点偏移的数据来源* 和 queued MOVE 两条 heading 源连在一起，本轮填补这一点。

从机器码得到的直接浮点关系：

```
D = record[+0x3C] - record[+0x40]
V0 = lookup[uint16(heading)][0]
V1 = lookup[uint16(heading)][1]
new_x = resolved_x - V0 * D * 0.5
new_z = resolved_z - V1 * D * 0.5
```

`0.5f` 的文件字节位于 RVA `0x0392211C`，已直接验证。**`lookup` 不能未经运行时证据叫作单位切向量或正弦余弦。**其表地址 `0x03E8F360` 在文件的 `.srdata` 节，磁盘样本均为零；说明**无法通过目前的磁盘字节直接推断运行时表数值**，不代表执行时实际表全为零。

后续调用 `0x0310E450`、`0x030C7058`、`0x030C72F0` 等进行候选、节点与路径求解；这些还未完成与阵型宽度/圆角半径的对象类型闭合。

## 5. 这对“更平滑转弯”意味着什么

**已证：** 后继 MOVE 传入的方向可以选择不同来源，但在正常允许执行 rich 路径时，两者进入同一个记录/转换通道；这个通道按 16-bit heading 对二维点施加一个与描述符标量差值成比例的偏移。

**未证：** scalar_A 是阵型半宽、预瞄量还是其它原生空间值；动态 lookup 是单位朝向向量；这个修正控制转弯半径；Shift 折返挤压正是由它造成。

更有价值的静态下一步：**类型化 Group+0xB30 对象的 virtual+0x20/+0x28，追踪其返回标量的来源和范围**，同时找出 Root+0x1D0 的数据意义。若标量是路径预瞄或阵型宽度，可进一步审计其限制和交给 member route 的方式，再考虑 scoped Native 调节，而不是全局 NOP、改 ushort heading、或强制停队转向。

纯合成几何测试可以假设 V=(1,0)、A=8、B=0，则二维点会沿第一维位移4个数学单位；它验证的是代数实现，不代表任何游戏测量。

## 6. 回退与资料归档

包含 `audit_r54_geometry_scalar.py`、`r54_geometry_scalar_pins.txt`、`test_r54_geometry_scalar.py`、配套 R53 PE helper、静态脱敏证据、完整函数反汇编、测试日志、R53 历史资源包。**不会修改游戏 EXE，禁止盲目对 scalar 加系数或改写 Group 的运动状态。**

当前：`root_cause_proven=false`、`native_gameplay_patch_authorized=false`、`in_game_testing=false`。仅维护研究分支，不动 main。
