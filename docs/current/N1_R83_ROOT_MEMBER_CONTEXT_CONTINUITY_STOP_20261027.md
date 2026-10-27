# BSC R83 — Root 与成员控制器上下文连续性：有界止损（2026-10-27）

**研究对象**：同一兵牌在原生 queued Shift 连续 MOVE 折返时发生群体运动穿插和挤压。挤压不是 CA 单独的原生动作。本轮不安装游戏 Hook，也不更改普通 RMB、Shift ATTACK、原生转向或避障。

**原始 EXE**：用户提供 Win64 Warhammer3.exe，SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`，232531920 字节，ImageBase `0x140000000`。下文均为 RVA；不混同运行时 ASLR 地址。

## R83 的新证据

**第一项：正确对象类型的初始化与读取。** R82 已证的构造字段来源保留：Root 成员生成函数 `0x03012F44` 中 `0x03012FE7` 读取 `[Root+0x38]`；经构造器可成为 `member+0x58`。普通成员构造器 `0x03052F62` 读取 `member+0x58`，`0x03052F6D` 写入内嵌控制器 `member+0x720`。Group 构造叶函数 `0x030C7DBC` 从传入的 Root 描述符形成相同源字段、写 `Group+0x10`。这些是不同的**构造时点**，并非一条 Shift 任务代际链。

**第二项：对有限的原生 MOVE/Group 函数，没有观察到可归属 Root 或成员的直接重绑定。** 经完整 PE 函数范围反汇编检查了 `0x03012F44`、`0x03020534`、`0x030209EC`、`0x030374CC`、`0x0302AE74`、`0x02F5B1E4`、`0x03052BA8`、`0x03076F64` 等，以及 Group 上下文复制叶函数。可见 `0x0303753D/572/658/750` 等 Root 上下文读取，`0x03020A75` 是将 Group 指针写入 `Root+0x32F8`，**不是重写 `Root+0x38`**；类型确定的 `member+0x720` 8B 写点为普通成员构造器中的 `0x03052F6D`。这不是全 EXE 写者穷举，更没有排除虚调用、间接别名与其他线程。

**第三项：两处很容易误报的写者已按寄存器身份驳回。** `0x0300B178` 的 `0x0300B19F` 将 Root 相关输入 RDX 保存到 RBX，同时 `0x0300B1A9` 将另一辅助对象 RCX 保存在 RDI。该函数会用 RBX+0x32F8 读 Root 的 Group，但 `0x0300B23A MOV [RCX+0x38],R9` 写的是**另一对象**的字段，而 `0x0300BAD6 MOV BYTE [RDI+0x720],AL` 只写该辅助对象的一个字节，不能当成普通成员 8 字节上下文指针的写入。这是有类型/寄存器证据的负结论。

## 严格证据等级

当前原始 EXE 本地核验 **49/49 机器码与真正 llvm-objdump 指令起点、5/5 E8、9/9 PE unwind 函数、1/1 无 unwind 叶函数**；**22/22** 本地 unittest PASS，包含 EXE 与 LLVM 反汇编两项。公开 GitHub 提供 SHA-pinned 49 pin、5 E8、范围校验器及合成负例，商业 EXE 测试在公开 CI 应 SKIP。完整本地材料在聊天 `BSC_R83_ROOT_MEMBER_CONTEXT_CONTINUITY_STOP_20261027.zip`，含相关 ASM、完整校验器、测试与 R82 归档；不含商业 EXE。

**扫描边界：**尝试的全 `.udata` 反汇编普查在执行预算内未完成，**不得用其宣称全引擎不存在字段写入者**。本轮只凭已完整定界的具体函数做结论。

## 关键因果判断与 R84

共享 context 并**不等于**共享 `MOVE slot / shortTask / route generation`。就算 Root+0x38 指针在一次战斗里不变，管理器下的路线仍可以替换。因此 R82 构造同源并非 Shift 折返成员同步的证明，也不能据此给所有士兵强制写同一个目标。

**R83 决策：** `ROOT_CONTEXT_RUNTIME_REBIND_IN_CHECKED_PATHS=NOT_OBSERVED`；`GLOBAL_CONTEXT_IMMUTABILITY=UNKNOWN`；`SAME_SHIFT_MOVE_EPOCH=UNKNOWN`；`CROWDING_ROOT_CAUSE=UNKNOWN`。

**R84 只允许调查已类型化成员控制器 `member+0x738` 的一条具体运行期赋值/换代路径**，看它控制的局部候选选择是否与原生路段一致；若仍不能证明，同样止损，不再用“地址数量”冒充修复进展。没有安全原生实例级证据之前禁止 live Hook、替换 CA Shift 或发布补丁。

`gameplay_patch_authorized=false`; `main_unchanged=true`.
