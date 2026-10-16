# BSC N1：第25轮原生成员 Tick 互斥分流与伪速度写者排除（2026-10-16）

## 验证范围

固定用户原始 WH3 Win64 EXE，SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，ImageBase `0x140000000`，以下均 RVA。使用原始 EXE 严格验证 **66/66 原机器码/objdump 真正指令起点、8/8 E8、8/8 E9/JCC 跳转目标、1/1 组件类型虚表槽及两个构造器安装点**。独立本地 **14/14 PASS**，包含真实私有 EXE、错误 SHA 和 `python -O` fail-closed。GitHub 测试源码有15个用例，原始 EXE 测试在公开环境无二进制时跳过；**不可声称 CI 已经 PASS**。

## 实际数据控制流

成员 Tick `0x03081EB4` 的真实有条件子图：

| 条件 | 本次可证行为 |
|---|---|
| `member+0x108 & 0x08` | `0x03082272` 调成员虚表+0x498，随后 `0x03082278 JMP 0x030823A9`，跳过下述两种分支 |
| bit0x08=0，`member+0x108 & 0x04`，`member+0x324` 为 `0x04` 或 `0x10` | `0x030822CB` 取 `&member+0x328`，`0x030822D2 CALL 0x03080F4C` 更新内嵌 action；随后 `0x030822E4 JMP 0x030823A9`，**本次不走邻近计算** |
| bit0x08=0，bit0x04=0，且 `member+0xB20==NULL` | `0x030822F9 CALL 0x03054B84`，随后 `0x03082301 CALL 0x03088808` |
| bit0x04=0 但 `member+0xB20!=NULL` | 改走 `0x030823A0` 的成员 virtual+0x490，**不是保证进入邻近计算** |
| bit0x04=1 而 `member+0x324` 不是上述两个状态 | 进入其它条件处理；**没有证明总是进行邻近计算** |

这是一条真实的**逐成员状态互斥处理**；只要同一兵牌的成员在转弯时状态不同，在相同 Tick 可以采用不同更新子路径。但未证明用户实际 queued Shift 折返发生状态分叉，不能据此认定挤压原因或修改状态位。

`0x03080F4C` 处理的是 `&member+0x328` 的短动作子对象，按自己字段 `+0x154/+0x10/+0x18` 对 `virtual+0x08/+0x10` 进行有条件调用。它**不是这里的直接速度写入器**。

## 错误速度写入假说的实质排除

原 EXE 中 `0x03085D89 MOVSS [RBX+0xE0],XMM0` 看起来命中 member+0xE0，但**实际对象类型不同**：

- `0x0304E82A/0x0304E83B` 以及 `0x0304FFB9/0x0304FFC3` 安装**组件表** `0x03ACD0D8`；
- 该表 `+0x10` 的真实函数是 `0x03082CD4`，其两处内部调用 `0x03082E40/0x03082E6D` 指向 `0x03085AC0`；
- `0x03085AC0` 的 `RCX→RBX` 是该**组件 this**。同一组件 `+0xE4` 被当成 BYTE flag；在 `0x03085D89` 写的 `+0xE0` 仍属于该组件。
- 只有 `0x03085D06` 才从 `[RBX+0x08]` 获取一个**另有身份**的对象，之后 `0x03085D0A/12` 读取那一对象的 `+0xE0/+0xE8`。不能把两个字段根混成一个 member。

这项类型反证不排除组件间接影响运动，但禁止把 `0x03085D89` 盲用作士兵速度修复位置。

## 下一步唯一优先的因果判断

集中检查 `member+0x108` 的 bit0x04 何时更新、`member+0x324` 何时从 4/16 转换至邻近运动路径对应状态，是否在同一 queued MOVE/group generation 的两个相邻 member 中出现不同 Tick 分流。若双方始终同分支，则排除此异步动作假说，再查真正的速度或避障冲量提交者。没有绑定同一 Shift 实例前，不能全局改成员状态、禁用渐进转弯或删除 CA 避障。

**本轮无游戏补丁；native_patch_authorized=false；不要求用户再证明已确认的 Shift 内部挤压。** 仅维护 `research/n1-native-shift-behavior-patch-20261009`，不动 main，不上传 EXE 或原始用户指针日志。

### 文件

- `maintenance_tools/native_shift_re/member_tick_motion_type_manifest_20261016.txt`
- `maintenance_tools/native_shift_re/audit_member_tick_motion_type_20261016.py`
- `tests/test_native_shift_re_member_tick_motion_type_20261016.py`
- 完整本地包 `BSC_R25_MEMBER_TICK_TYPED_MOTION_GATE_20261016.zip`：14项本地日志、独立可运行工具、中文分析与脱敏 JSON。
