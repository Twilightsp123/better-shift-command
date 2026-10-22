# BSC R62 / 第28轮 — ±90° 原生选侧角进入路线候选几何的确切消费者（2026-10-22）

**目标**：让原生 CA queued Shift MOVE 连续折返更平顺、兵牌成员不穿插；保持原生路线、避障、普通 RMB、Shift ATTACK。**只读静态审计；没有 Native gameplay patch。**

## 输入与验证身份

用户新版 Win64 `Warhammer3.exe` 完整 SHA256：`9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`，232531920 bytes。本文地址全部 RVA，ImageBase `0x140000000`。在本地实际原 EXE 上完成 **82/82 完整指令字节及 objdump 起点、14/14 E8、9/9 条件跳转、11 个 PE unwind 函数** 检查；14/14 Python 单测通过（含真实 EXE），无 EXE 的公开运行 13 PASS / 1 SKIP。所有合成几何例子仅验证数学分支，**不代表玩家实机 Shift 证据**。

## 这次真正的新数据边：侧角有具体几何消费者

R57 已发现通用 `0x0310E450` 在关联对象状态允许时计算 `reference_heading±0x4000`，`0x0310E54C → 0x030FA978` 在临时路线记录 `+0x44` 保存派生的 uint16 朝向。本轮从原始调用现场明确闭合：

```text
route converter 0x03102B28
  0x03102CB8  RDX = &[RBP+0x60]      同一临时路线记录
  0x03102CD8  CALL 0x0310E450
    0x030FA9DE 写 [record+0x44] = 派生角
  0x03102CFA / 0x03102D29  仍有条件早退
  0x03102E04  R8 = &[RBP+0x60]
  0x03102E38  CALL 0x0312AAC4
    0x0312AB04  RDI=R8
    0x0312AB83  RDX=RDI
    0x0312AB99  CALL 0x03114BF4
      0x03114C2E RSI=RDX
      0x03114C6B CALL 0x0312214C 解析空间参考坐标
      0x03114CAA MOVZX EAX,WORD [RSI+0x44]
      0x03114C78 方向查表首址 0x03E8F360
      0x03114CB6 / CBC 使用派生角索引的两个 float 分量
      0x03114CD8 / CCD 写候选几何 work+0x1A8/+0x1AC
      0x03114D1D / D25 写候选归一化方向
```

**类型约束：** `0x03114BF4` 的 `RCX` 是路线候选工作对象，绝不是普通 soldier/member；`RDX` 是上述临时路线记录。数据链通过实际寄存器别名、原码和栈地址核对，**不是根据相同字段偏移拼接对象**。

该候选位置的浮点指令可表达为：

`Q_x = C_x - S * LUT[derived_heading][0]`

`Q_z = C_z - S * LUT[derived_heading][1]`

其中 `C` 经过坐标参考框架解析，`S` 来自候选工作对象 `+0x18`；**还没有证明 S 是转弯半径、阵型半宽或速度**。这是候选几何，不是直接写入 soldier+0x88/+0x90。

进入该分支至少受到 `0x03102CFA`、`0x03102D29` 的上游早退和 `0x03114C34`、`0x03114C46` 的候选对象/虚方法门槛约束；`0x0312ABA5` 还会控制后续求解流程。**静态可达不等于真实 Shift 同实例实际命中。**

## 到原生 B2 路线 node 的下一段条件数据链

同一新版 EXE 的 R37 证据，本轮重新通过机码约束：

- `0x03126A58` 路线 node 构造器只有在 mode helper=1 **或**输入 `record+0x4C=1` 时，于 `0x03126B41` 调用上述 `0x03102B28`，随后 `0x03126B46` 保存返回路线到 `node+0x70`。
- B2 创建时 `0x02F545DA` 再经同一 node 构造器，`0x02F545FF` 取 `node+0x70`，通过中间记录 `+0x28` 在 `0x03268D80` 写 `B2+0x60`。
- B2 直接／后备两条发送入口 `0x032769F2` 与 `0x03286445` 共享 `0x0326A994` 成员 packet 发送器。

这是**有条件的原生代码/字段路径**，不能推出求解结果一定非空、所选候选一定进入最终 route buffer、所有士兵 packet 一定携带该角度，也没有证明 Shift 折返时跨越选侧边界。

## 平滑转弯的可证伪候选（非 gameplay 结论）

R57 已证 side-heading 分支可在 reference 相对 input 从 -1 变 +1 时选择近乎相反的两个垂直角；若参考中心 C、S 固定且使用单位三角 LUT，则候选点的分离量可接近 `2*abs(S)`。纯合成测试 S=8，约16个数学距离单位；**当参考中心 C 同步补偿时，最终 Q 完全可能仍连续**。所以“角度有跳变”与“成员物理挤压”之间依然存在关键证据缺口。

## 明确止损与下一步

**下一轮只追** `0x03114BF4` 生成的 candidate work `+0x1A8/+0x1AC/+0x1B0/+0x1B4` 如何通过 `0x0312AAC4` 的后续求解与返回缓冲区影响具体 B2 node/成员 world goal。如果这些点只是临时候选且被纠正/丢弃，应立即降低 R57 选侧翻转方向，转向成员协调或更高层预瞄曲率。绝不直接改 `±0x4000`、强行固定左／右转、清空所有 packet/action 或用 Lua 替换 Shift。

完整审计源码 `audit_r62_side_record_to_candidate.py`、82 条 exact pin、单测、静态 JSON、原始指令摘录和 R61 全历史包在本轮离线资源 ZIP。**未执行游戏进程，无玩家新动态数据，native_gameplay_patch_authorized=false，main 不修改。**
