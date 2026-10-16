# BSC N1 — 第 19 轮：0x030FDA9C 的条件性空路线返回（2026-10-16）

## 版本与证据等级

基于用户原始 Win64 `Warhammer3.exe`，完整 SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，PE32+ ImageBase `0x140000000`。本轮完全只读的独立原始 EXE 验证：**76/76 字节及 GNU objdump 指令起点、10/10 E8 目标、9/9 E9/JCC 目标；12/12 本地回归 PASS（含 1 项真实私有 EXE）**。

这不是正在运行的游戏分支命中、没有确认某次 Shift 折返出现空路线，更没有 Native gameplay 修复。

## 1. 两类不同的 NULL 返回边

已识别路线转换器 `0x030FDA9C`：

- `0x030FDAB9` 清零 `R15D`，`0x030FDAD2` 令 `EBX=R15D=0`。`RBX` 是该函数最终返回对象的寄存器。
- `0x030FDDAC` 调 `0x03125A1C`；`0x030FDDB6` 的条件将返回零时引向另一套构造路径。非零时 `0x030FDDBC` 比较候选计数 `[0x0436037C]` 与 `EBX(0)`，`0x030FDDC2 JBE 0x030FDEA3` 在候选数为零时跳过整段路线对象分配循环。
- `0x030FDEC9 JMP 0x030FE0A7` 进入清理尾部；`0x030FE0B8 MOV RAX,RBX`，`0x030FE0D9 RET`。沿上述分支所执行的指令均未改变 `RBX`，因此**若前置 solver 非零而候选数量为零，则转换器条件性返回 NULL；无需先有 OOM**。
- 另一路 `0x030FDEE6` 申请 `0x80` 字节对象，`0x030FDEF1` 在申请失败时跳至 `0x030FDF6F`，把 `RBX` 保持在零，再经同一返回尾部。

**必须保留的重大限制：** 尚未证明 `0x03125A1C` 返回非零与共享候选计数为零，在引擎的合法实际状态中能共同发生。可能存在求解器本身的隐含约束，所以这是**机器码有条件的分支结论**，不能写成“游戏通常会发出 NULL 路线”或声称已经发现 bug。

## 2. Manager 的“写路线、然后写处理位”没有 NULL 防护

原生 manager `0x03129092 CALL 0x030FDA9C`，于 `0x03129097` 写 `node+0x70=RAX`，紧接着 `0x0312909E` 写 `node+0x08` 已处理标记。在这段中没有独立的 `RAX!=NULL` 检查。普通 B `0x03AE00E8 +0x10=0x03281520` 检查 `node+0x08` 后读取 `node+0x70`，在其直接入口没有另设非空 gate。

因此**假设转换器真的返回 NULL**，静态上可以出现 `node+0x08=1` 且 `node+0x70=NULL` 的字段组合，但**尚未证明**它在用户 Shift 折返的任务实例中发生，也没有把它与同一兵牌成员相向运动的物理因果联系起来。

## 3. 下一步只有一个真正值得查的前置不变量

先逆向 `0x03125A1C` 的返回语义及其传递的共享候选容器，求证“返回非零且 `[0x0436037C]==0`”是否实际允许。若可证明原生成功必有非零候选，就排除此非 OOM 空路线假说；不要在零路线疑点上无穷追加函数。若确实允许，下一步仍须连接**同一个 queued MOVE 的 group generation、route 对象身份及两名 member motor goal**，才可授权补丁。

在任何情况下，不可全局强设 `node+0x08`、抹除合法旧方向投影、破坏 CA 渐进转弯、避障、普通 RMB 和 Shift ATTACK。用户早已证明原生 Shift 折返挤压存在，不要求再证明。

## 4. 可复验证据

- `maintenance_tools/native_shift_re/converter_return_guard_manifest_20261016.txt` — 固定 SHA 对应 76 个完整 opcode。
- `maintenance_tools/native_shift_re/audit_converter_return_contract_20261016.py` — 使用项目已有 `OriginalEXE` 做 PE/unwind/真实起点、E8/JCC、完整函数内 RBX 写入守卫。
- `tests/test_native_shift_re_converter_return_contract_20261016.py` — 不含 EXE 的合成负例和可选的私有真实 EXE 回归。
- 本轮本地独立档案同时提供标准库完整审计器、12/12 测试结果、上述静态 JSON 与反汇编摘录；不包含 EXE 或真实运行时指针。

**native_patch_authorized=false**。工作分支 `research/n1-native-shift-behavior-patch-20261009`，`main` 不修改。
