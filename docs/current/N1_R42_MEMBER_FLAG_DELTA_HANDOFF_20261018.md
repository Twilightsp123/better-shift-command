# BSC R42 — typed member bit2/delta handoff and local integrator skip (2026-10-18)

> 本对话第8轮。**只读静态研究，不是 gameplay patch。** 下列全部是新版 `Warhammer3.exe` 的 RVA，不是运行时绝对地址。

## 二进制身份 / 验证范围

- 新版 EXE SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`，大小 232531920 B，PE ImageBase `0x140000000`。
- 对 11 个 PE unwind 函数跨度做本地只读审计：**128/128 原字节和 objdump 指令起点、7/7 E8、7/7 JMP/JCC、6/6 已由普通成员构造器装表定型的虚表槽 PASS**。私有真实新版 EXE 下 **20/20 unittest PASS**，无 EXE **19 PASS / 1 SKIP**；没有在 GitHub CI 运行完整私有 EXE 测试。
- 完整审计器、128 原码 manifest、原始控制台证据、回归与上一轮档案在本轮离线包 `BSC_R42_MEMBER_STATE_DELTA_HANDOFF_20261018.zip`，**离线包不含原始游戏 EXE**。远端本文件为摘要；不要把它误作完整证据包。

## 1. 积分器 `0x03146FF0` 的两个门槛

同类型 `RBX=member`（`03147019 MOV RBX,RCX`）下，积分器可能先在 `03147199/A1` 把朝向相关修正叠加至 `member+0x13C/+0x144`，**然后**：

```text
031471A9 DL = [member+0x108]
031471AF CL = [member+0x155]
031471B5 TEST DL,0x02
031471B8 JNE 0314738F          ; 复杂空间运动路径
031471C1 TEST CL,0x04
031471C4 JE  03147306          ; 跳过本次直接位移
0314720B/223/23B              ; 否则把 delta 加到 XYZ
031472C3/D1                   ; 清理本次 +0x13C..+0x144
```

`bit2=0 & member+155 bit4=0` 时，`03147306..0314738A` 状态重置并跳到退出；**在这段直接代码中没有写 XYZ 或清理 +0x13C/+140/+144**。这只证明这次本函数**局部跳过**，**不证明真实 Shift 折返发生了跨 Tick 残留、速度错配或坐标跳跃**。`bit2=1` 时走复杂空间约束路径，`03147398/9B` 清 `member+155 bit4`，存在另外受门槛控制的增量/坐标更新。

## 2. bit0x02 不是 Shift 独占标志

普通成员构造器 `03052D20/34` 安装 `0x03912950` 类型虚表，已验证：
- `virtual+0x128 → 03084B5C`，`03084B90 OR member+108,0x06`。
- `virtual+0x130 → 03084C8C`，`03084CC7/C9/CB` 清 bit0x04、置 bit0x02。
- `virtual+0x138 → 03084BA0`，`03084BAA/BB9/BBE` 清 bit0x04、置 bit0x02 和 bit0x08。
- `virtual+0xF0 → 03164710`，`03164776 AND member+108,0xF5`，清 bit0x02 与 bit0x08。

更关键：**积分器本身**在后段 `03148182 MOV RCX,RBX → 03148189 MOV RAX,[RBX] → 0314818C CALL [RAX+0x130]`，可以有条件调用同类型状态写者；这发生在本次最初的 bit2 门槛判定之后，不会倒改本次已选分支。因此不能把 bit2 的所有更新强行归因于 B2 packet 或 Shift 键。

## 3. 同类型状态恢复和“自身位置别名”

`virtual+0x130` 在 `03084CE0` 对 `member+0x104==3` 进行检查，特定条件路径 `03084D85 CALL 03081D40`。后者在 `03081DB0` 条件性调用 `0305F534`（可置 bit2、清 `member+155 bit4`），后于 `03081ED6` 调用 `03164710` 清 bit2，最后 `03081EDB OR [member+155],0x04`，形成与前述直接积分相容的标志组合。**静态可达不等于每个 queued Shift 实际命中**。

在 `03081EBB LEA RDX,[RDI+0x88]` 和 `03081ECA MOV RCX,RDI` 后直接调用 `03164710`。后者将 RDX 保存为 RSI，并把 RSI 的当前位置复制到当前成员 `+0x88/+0x90`；因此该**具体调用现场**的位置源和目的地是同一对象字段，不能将其误报为外部坐标的瞬移。此前、期间的其它间接调用副作用尚未排除。

## 4. 目标时相与停止标准

扩展包装器在 `0310014C` 先 CALL `03146FF0`，在部分后续条件路径中才由 `03100233 → 03100247` 解析 `member+0x1E0` 的当前世界目标，并将方向/运动投影写到 `member+0x23C`。不能倒置这一时序，把后读的目标直接当成本次已执行的积分输入。

**下一轮只追**同一 queued MOVE 激活阶段成员 `bit2 / +155 bit4 / pending delta` 的状态关联；若无法静态连接实例身份，降低残留猜想优先级，转向 `+0x14C/+0x150` 世界目标驱动写者。不要再重复证明 Shift 挤压存在性。

**范围边界：** 未获同实例 Shift 实机因果证据；`root_cause_proven=false`；`native_patch_authorized=false`；不能全局强制清 bit2、改成员坐标或禁用原生渐进转弯、寻路、避障、RMB MOVE、Shift ATTACK。禁止修改 `main`，禁止上传原始游戏 EXE。
