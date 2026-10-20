# BSC R52 / 本对话第18轮 — 用实际 memreader Plus 0.13.0 与新版 WH3 原生 EXE 理清 RMB/Shift 差异

## 本次审计的实际文件

本轮直接解包用户给的 memreader_plus.zip（PFH5，15项）、derpy_third_person.zip（27项），并对用户的新 Warhammer3.zip 中游戏 EXE 做完整 SHA256 校验：`9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`。PE 时间戳 `0x6acec6f4`，ImageBase `0x140000000`。以下均为当前新版 RVA。

本地可复现只读审计在真实 EXE 上严格核验 **26/26 完整机器码与 objdump 指令起点、4/4 直接 E8、2/2 跳转目标**。实际三个归档配合跑通 **10/10 unittest PASS**。**全部是静态证据；没有安装 Hook、调用第三方 DLL 或完成 Windows 实机 RMB/Shift 运行时对照。**

## 物理键盘动作 ≠ 原生队列语义

Derpy 实际 `keys.lua` 将 Right mouse 定义为 Windows VK `0x02`，Shift 定义为 VK `0x10`；`platform.lua` 调用 `mr.call(fn.GetAsyncKeyState, "int16(int32)", vk)` 读取物理键态。这说明 memreader Plus 可以辅助获取玩家当时键态，**不意味着它已经知道哪个 native order 是这个按键产生的**。

在新版 EXE 的原生 MOVE 统一入口 `0x030374CC`，已重新确认：

- `0x03037500 MOV R14B,R9B`：`R9B` 是进入队列流程的 append/replace 控制位。
- `0x03037503 MOV RDI,R8`：`R8` 是命令描述符。
- `0x030377A6 TEST R14B,R14B`，非零时还有 `Root+0x2F88` 对 40 条容量的检查。
- `0x030377BF MOV DL,R14B` → `0x030377C2 CALL 0x02F5540C`。
- 管理器 `0x02F55421 TEST DL,DL`；`0x02F55423 JNE 0x02F55445`。**DL=0** 进入旧队列清理调用 `0x02F55440→0x02F3EFBC`；**DL!=0** 跳过此清理块并按条件追加。
- `0x030377DF MOV R9,RDI` → `0x030377E8 CALL 0x0300E170`，将描述符交给新 MOVE slot 构造器。
- `0x030377ED JMP 0x03037A6E`，明确跳过同一函数中的 `0x03037A69 CALL 0x03032C48` 即时 Group 创建。

**结论：真正可确认的是 native REPLACE vs APPEND，而不是直接观察到物理 RMB / Shift 键专属函数。** 普通 RMB 可能进入 queue replace；Shift 可以触发 queued append，但脚本、AI、内部重发也可 append，故绝不直接将 `R9B=1` 命名为“玩家 Shift”。

## 第二层：MOVE 描述符与后继转向几何

新原码 `0x0303752E/0x0303755C/0x0303759E/0x030375B7` 依次检查 `descriptor+0x5A` 的 `0x20/0x40/0x04/0x02`。`0x0303777D OR BYTE PTR [RDI+0x5A],0x06` 是**特定条件路径**下的正规化，不是所有 Shift 必执行的命令。

旧版 R12/R13 已追踪到 descriptor+0x5A → slot+0x9A，后继 slot bit2 决定预存朝向还是取当前 Group 空间基准；它解释原生队列后继路段的条件几何差异，但并未证明哪次真实 Shift 折返在这个阶段首先造成队内穿插。本轮核验了新版入口，但不能冒称旧版全套下游地址在新版都已重新验证。

## memreader Plus 全栈能力与限制（来自实际 pack + 私有静态 DLL）

- pack 0.13.0 包含 loader/boot、Native DLL、sites.lua、agree.lua、运行报告和崩溃上下文等共15项；Native DLL 静态解出 231936 字节、SHA256 `e26d0e2ff665f2611e94e13a7566653ea7e3791db6b945f1f191577bc83a491b`。x64 PE 导出 `luaopen_memreader_plus`，导入 `VirtualProtect`、`SuspendThread`、`ResumeThread`、`RtlLookupFunctionEntry` 等；只完成**静态识别，未执行 DLL，更未完整反编译每个 native 实现**。
- `read_original` / `read` 核验原机码与当前机码；`find_patterns` 支持有边界的版本定位；`hook`、`hook_site`、`hook_info` 支持观察与脚本线程计数；`patcher(owner)`、`batch`、`cave` 提供补丁归属和原字节检查。Cave/relocation 等有进程级生命周期限制。
- **Lua Hook 只覆盖游戏脚本线程**，其他线程原生调用绕过回调，`other_thread_calls` 可辅助辨识。不能凭没记录到的 Hook 认定 Shift 指令没有执行。不得在高频成员 Tick 上直接假设安全。
- 所以 memreader Plus 是原生观测与可回退补丁的**基础设施**，不是自带 Shift/RMB 根因分析器。

## 下一处真正可否证的研究点

优先追踪玩家输入到 **实际 native MOVE 调用者**，把物理 VK 0x02/0x10（仅辅助）、caller return RVA、匿名 UnitRoot、R8 描述符、R9B、descriptor+0x5A、queue slot、slot bit2 和后继激活串到**同一个 command 实例**。

至少四个对照：空队列普通 RMB、已有 Shift 队列后普通 RMB 替换、已有 MOVE 后 Shift 追加、非玩家内部 append。只有排除内部调用者和时间差，才能把原生 append 归因于玩家 Shift。

本地交付完整代码：`BSC_R52_MEMREADER_PLUS_RMB_SHIFT_NATIVE_20261020.zip`（只读 SHA-locked 审计、完整中文版报告、10项测试、真实三归档脱敏静态 JSON、无 Hook Lua 指令检查辅助），不包含游戏 EXE 或第三方 DLL。GitHub 本文用于维护结论；不要把此报告当成真实 Windows 实机 Hook 命中或 gameplay 修复。

`root_cause_proven=false`，`gameplay_patch_authorized=false`，不修改 main。
