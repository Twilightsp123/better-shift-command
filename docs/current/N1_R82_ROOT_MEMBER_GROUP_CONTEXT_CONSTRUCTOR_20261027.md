# BSC R82 — Root / Member / Group 上下文构造来源（2026-10-27）

**新证据：已证明两条原生构造路径从相同的 Root 字段取上下文；未证明同一 Shift 路段的运行时身份。**

源为用户本地原始 Win64 Warhammer3.exe，SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`，大小 232531920，PE ImageBase `0x140000000`。以下均 RVA。只读静态审计；没有运行游戏或安装 Hook。

## 成员侧的实际数据流

`0x03020534` 以原生 UnitRoot 对象为 RCX，在 `0x03020621` 调 `0x03012F44`。该函数保存 `RSI=Root`；在两条受条件保护的成员创建路径中，`0x03013235/0x03013578` 执行 `LEA RDX,[RSI+0x30]`，`0x03013273/0x030135B6` 调普通成员构造器 `0x03052BA8`。

该构造器通过 `0x03052BD5/0x03052C57` 保持同一 RDX，再通过 `0x03052CA0→0x030F31D8→0x031417F4` 进入基础构造器。在 `0x03141803/10` 读取 `[RDX+0x08]`，并在 `0x03141809/14` 写成员 `+0x50/+0x58`。由于 RDX 是 `Root+0x30` 的**地址**，来源明确是 `[Root+0x38]`。普通构造器随后在 `0x03052F62/66/6D` 把这个值传入内嵌成员控制器 `+0x718/+0x720`。

## Group 侧的实际数据流

现版 `0x030209EC` 用 RCX=Root，在 `0x03020A17` 向 `0x0302093C` 的 R8 传同一 Root；后者在 `0x03020952` 将 R8 写入局部 Group 描述符 `+0x08`，并在 `0x030209BF` 调 `0x030C7CB8`。Group 构造器 `0x030C7CD2/D6` 从描述符恢复 Root 并构造 `Root+0x30` 地址，经 `0x030C7CDD` 调无 unwind 叶函数 `0x030C7DBC`。后者将 `[Root+0x38]` 写入 `Group+0x08/+0x10`；同时 Group 构造器 `0x030C7CF9` 保存 `Group+0xA10=Root`。新 Group 在 `0x03020A75` 才发布到 `Root+0x32F8`。

## 证明范围与反证

**对于同一个 Root R，如果两种对象分别由上述构造路径建立，那么它们的上下文来源表达式均为 `[R+0x38]`。** 这是字段/类型级别的正证据；它们是在不同时间读取的，因此**不意味着值在两个时点必然一样**，也不意味着两个上下文指针相等就属于同一 Root、同一 Shift MOVE 任务/route generation。

本轮没有验证上述函数对全体成员、所有 Group 或玩家具体 queued Shift 折返都必然执行。普通成员构造器另有其它直接调用者，未经逐个上游类型化，不得外推。也未排除 Root+0x38 运行期替换、member+0x720 后续重绑定、对象池复用等。

## 校验与下一步

在用户匹配 SHA 的实际 EXE 上通过 **43/43 原始机器码及 llvm-objdump 指令起点、8/8 E8、8/8 PE unwind 函数、1/1 无 unwind 叶函数；22/22 本地 unittest**（包括两项真正使用 EXE 的检查）。公开 CI 不包含商业 EXE，仅验证固定字节清单/协议，原 EXE 测试应跳过。

完整离线 `BSC_R82_ROOT_MEMBER_GROUP_CONTEXT_LINK_20261027.zip` 含所有测试、源码、9 段反汇编、原始 EXE 静态结果及 R81 历史归档，不包含游戏 EXE。

**R83：**有界审计 `Root+0x38` 运行期写者与 `member+0x720` 的保持性，判别是否存在跨构造时点的上下文改变。未证明时不得强行修改成员控制器、原生 Shift、转向速度或装 Hook。

`constructor_source_link=CONDITIONAL_PROVEN`; `same_shift_generation=UNKNOWN`; `crowding_root_cause_proven=false`; `native_gameplay_patch_authorized=false`; `main_unchanged=true`.
