# BSC 第32轮 — 成功 MOVE→MOVE 移交并不直接重建 Group；真实任务回调晚绑定（2026-10-17）

## 结论与验证

原始 Win64 `Warhammer3.exe` SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，ImageBase `0x140000000`，地址均 RVA。本轮独立审计 **39/39 原机器码与 GNU objdump 真实指令起点、13/13 指定 E8 调用、7个 PE unwind 函数**；本地 **16/16 回归 PASS（包含真实原始 EXE）**，无 EXE 时15 PASS/1 SKIP。GitHub 审计器采用同一原始码约束，公开 CI 的原始 EXE 测试必须跳过，不能直接声称 CI 通过。

## 一、与上一轮 Group 重建器之间真正存在的边界

成功 queued MOVE 继承逻辑（先前已有证据，今轮再次核对）：
```
0x030445AB  后继 MOVE 接收兼容大任务
0x030445B1  移出原 MOVE
0x030445BC  条件清退旧 shortTask
0x030445CB  清理调度引用
0x030445D3  CALL 0x030433B0
0x030433E3  CALL 0x03043424
0x0304346B  CALL [vtable+0x08]
0x0304348B  CALL [vtable+0x10]
```

**原码查完整函数**：`0x030433B0` 只有直接 E8→`0x03043424` / `0x02F4FD10`；`0x03043424` 只有 E8→`0x02F4FD5C` / `0x030376C8` / `0x02F3A0D4`。这两层**没有直接**进入上一轮的 `0x0301B8E4` Group 重建器。

相反，即时 Group 构造器 `0x0302DB44` 在 `0x0302DB8E` **直接**调用 `0x0301B8E4`，该重建器四处真实直接 E8 入口分别为 `0x0301A284`、`0x030200EF`、`0x0302DB8E`、`0x0303DCFF`（第31轮已验证）。**没有直接调用不能排除上述队列激活虚方法、后续 Tick 或回调间接到达重建器**。不得宣称完全排除 queued Shift 中的 Group 重建。

## 二、优先分析已实机命中的 MOVE 工作链的回调时相

旧 V3 实机资料已确认 `0x03025D70→0x0301287C→0x02F2C734`，并未证明 `0x0302DB44` 命中。原生短期 MOVE task `0x02F2C734` 把 UnitRoot 存到 `task+0x08`。它所属的 `0x02F561E8` 回调在一条明确的成员发包分支中：

```
0x02F563F4  MOV RCX,[task+0x08]     ; UnitRoot
0x02F563F8  LEA RDX,[RSP+0x50]     ; 新组装的输入记录
0x02F563FD  MOV RCX,[RCX+0x32F8]  ; 此时当前 Group
0x02F56404  CALL 0x03279E40       ; Group 进入 A/B 分派
```

该函数还在 `0x02F5627B`、`0x02F5649E` 的条件路径再次读取 **UnitRoot+0x32F8**。真正的 `0x03279E40` 先调用 `0x02DC2E04` 检查模式，在条件下进入 `0x030D554C`（A 发包）或 `0x03263AB0`（B 群组路线任务），没有依据断言某个玩家 Shift 实例永远选 A/B。

**下一根数据边：同一次后继 queued MOVE 的 shortTask 创建代际→回调晚绑定当前 Group→A/B 分派的路线引用→每名 member 的 world goal。** 尚未在同一次玩家实机轨迹确认 Group 和路线代际冲突，也尚未定位挤压根因。

## 三、研究去重纠错

早在2026-10-14写入 `docs/current/N1_903_AI_HANDOFF_20261011.md` 的文档段落，已有 `0x0301B8E4` 池回收→再获取和 `UnitRoot+0x32F8` 晚绑定证据。第30～31轮虽然新增细粒度审计和旧回放器反例纠正，但不应称“首次发现对象池复用”。后续停止独立验证空闲链表，不再用原码守卫数量代替与真实挤压相关的因果证明。

**依旧无游戏补丁，native_patch_authorized=false。** 保留 CA 原生 Shift、渐进转弯、避障、普通 RMB 和 Shift ATTACK；只维护 `research/n1-native-shift-behavior-patch-20261009`，不动 main。不会要求玩家重复证明已确认的折返穿插。

## 本轮文件

- `maintenance_tools/native_shift_re/queued_latebind_pins_20261017.txt`
- `maintenance_tools/native_shift_re/audit_queued_group_latebind_20261017.py`
- `tests/test_native_shift_re_queued_group_latebind_20261017.py`
- 完整离线资源 `BSC_R32_QUEUED_GROUP_LATEBIND_20261017.zip`（本地16项单测、实际原始 EXE 静态证据、人工反汇编及前后文，不包含游戏 EXE）。
