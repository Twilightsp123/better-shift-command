# BSC Native N1 — 第20轮：求解器虚方法的临时记录类型纠错（2026-10-16）

## 输入与独立验证

用户原始 Windows x64 `Warhammer3.exe`，完整 SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，PE ImageBase `0x140000000`，本文均用 RVA。独立离线只读验证 **60/60 opcode 与 GNU objdump 指令起点、8/8 E8、3/3 JCC、11/11 测试 PASS**，包括实际原始 EXE、错误 SHA 与 Python -O fail-closed。这仅是静态控制/数据流证据，不是游戏运行命中，不授权 gameplay patch。

## 最重要的纠正：solver 的 R8 不是原始 B node+0x20

先前考虑用普通 B fallback 初始 `record+0x00=NULL` 排除 `0x03125B3D` 路径，**这个推断不成立**，原因是调用者中间新建了工作记录：

1. `0x030FDCD8/DB` 为 `0x030F5AE4` 提供 converter-local `[RBP+0x60]` 的目标地址。`0x030FDCE9` 为真实 E8 调用。
2. `0x030F5AE4` 经 `0x0311D0CC` 取变换后数据，`0x0312D088` 获得路线/辅助对象指针；`0x030F5B2B` 写 `work+0x00`，`0x030F5B30/36` 分别写 **两个 DWORD 到 work+0x08 和 work+0x0C**，并写其它参数。这里的 work 不是原始 node+0x20。
3. `0x030FDD78` 以**同一个** `[RBP+0x60]` 作为 R8 传入 `0x03125A1C`；其 `0x03125A5C` 保存在 RDI。`0x0310FBA0` 检查这个 work+0x00 指针及虚表+0x10 的返回门槛，只有返回 AL=1 才在 `0x03125AFD` 进入特殊路径。
4. 特殊路径 `0x03125B0B` 读取 **QWORD [work+0x08]** 并在 `0x03125B3D` 用作 virtual+0x08 调用的对象；返回对象保存在 R15（`0x03125B67`），`0x031267F9` 再调用 **R15 的 virtual+0x18**。这不能被命名为原始 B node/group 的虚方法。

## 不可跨越的证据边界

临时 work+0x08/+0x0C 从两次 32 位复制得到，却在特殊路径按一个 64 位对象指针解释。该**类型冲突值得继续类型化检查，但不证明游戏存在非法解引用**：必须首先证明 `0x0310FBA0` 允许本具体构造记录进入特殊路径，且相应内存确实是合法对象指针。当前没有这些事实，也没有该返回对象的具体 typed vtable。

因此此前“返回码1的 virtual+0x18 清空候选数量，导致转换器返回NULL”仍是**未证、低优先级**的猜测。不能全局改 converter、node+0x08、路线标志或普通 B member packet。

前轮 result2 需要正候选计数的同线程静态门槛仍保留；result1 的类型、可达性及共享候选容器副作用仍未知。优先停止在 NULL 假说上无限扩张，回归实际运动证据支持的相邻成员 `record[i]、member+0x328 action、member+0x1E0 motor goal` 比较；只有具体同实例因果成立才设计补丁。用户已确认的 Shift 连续折返挤压无需重新证明，保留原生 CA queue、渐进转向、避障、普通 RMB 与 Shift ATTACK。

## 维护文件

- `maintenance_tools/native_shift_re/solver_temp_record_provenance_pins_20261016.txt`：60 个固定原始指令；
- `maintenance_tools/native_shift_re/audit_solver_temp_record_provenance_20261016.py`：严格 SHA、PE/unwind、E8/JCC、typed operands 的 GitHub 只读版；
- `tests/test_native_shift_re_solver_temp_record_provenance_20261016.py`：8 项回归（没有原始 EXE 时跳过 1 项）；
- 独立 ZIP `BSC_R20_SOLVER_RECORD_PROVENANCE_20261016.zip` 含 standalone PE helper、审计器、11/11 本地测试日志、脱敏 JSON、反汇编与中文记录，不含原始 EXE。

`native_patch_authorized=false`，仅维护 `research/n1-native-shift-behavior-patch-20261009`，禁止修改 main。
