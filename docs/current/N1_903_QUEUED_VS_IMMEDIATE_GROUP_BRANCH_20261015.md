# BSC N1 — 队列 MOVE 与即时 Group 重建分支互斥及后继朝向来源（2026-10-15，第13轮）

## 二进制与证据等级

目标是用户给出的固定 Win64 原始 `Warhammer3.exe`，SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`；所有地址为 PE ImageBase `0x140000000` 下的 RVA。

第13轮对原始 EXE 的只读验证：**37/37 完整指令字节和 GNU objdump 真正指令起点、17/17 E8 直接调用、5/5 E9/JCC 目标**，再用同一 unwind 所属函数内的静态 CFG 可达性检验确认两路互斥。本地完整验证 **11/11 PASS（其中1项使用用户原始 EXE）**。GitHub 新增的合同测试有12项，其中1项在没有私有 EXE 的公开 CI 必须 SKIP。这里的证明等级是 **EXACT_ORIGINAL_EXE_STATIC + SYNTHETIC_CONTRACT**；并非用户 RMB/Shift 键位的运行时辨识、不是物理碰撞根因验证，也没有 Native gameplay patch。

## 一、纠正此前可能误追的 group 代际假设

同一统一 MOVE 函数 `0x030323C8` 有互斥的两条控制流。**不可以把这两条模式分支简单命名为 RMB 与 Shift，也不能只凭 R9B=1 命中就认定玩家按 Shift。**

**常规队列分支（`0x030326A2`）**：

- 在适用的 mode/命令标志条件下，`R14B (=入口R9B)` 非零时，先检查队列容量 `root+0x2F88` 是否达到40，满时直接跳过下令。`R14B=0` 时可绕过该“追加队列已满”检查。
- `0x030326BB` 把 `R14B` 传入 `DL`；`0x030326BE CALL 0x02F50410` 依据 DL 决定清旧队列或保留追加，再由 `0x030326E4 CALL 0x030090BC` 初始化新 MOVE 槽位。
- **`0x030326E9 JMP 0x0303296A`**：完成这条分支后直接进入返回段，**跳过本次函数体内的 `0x03032965 CALL 0x0302DB44`**。对整个该 unwind 函数做保守分支 CFG 可达性分析（两侧 JCC 都遍历）也不可能从 `0x030326A2` 到达那个即时 group 调用点。

**另一条 group 几何/成员发包分支（`0x030326EE`）**：

- 上游可因 `0x0303248A` 的 mode 条件或 `0x03032494` 的命令标志判断进入；另有 `0x0303249E` 等条件跳向队列分支。这是原生**模式/命令字段的分派**，不是玩家键位直接映射。
- 在进一步原生条件允许时，经 `0x03032965 CALL 0x0302DB44`；这个入口内部有严格的调用顺序：
  1. `0x0302DB8E CALL 0x0301B8E4`：回收/重建 group，可写 `UnitRoot+0x32F8`；
  2. `0x0302DBC4 CALL 0x0301287C`：配置 `UnitRoot+0x270` 路线描述符；
  3. `0x0302DBDB CALL 0x030D5490`：按 `member[i]/record[i]` 条件性下发目标 packet。
- 已核对从该分支入口可到达上述调用点，但**不是声称此分支的每个早退状态都必然执行三次动作**。反向 CFG 也证明该分支不能到达上面的入队调用。

**新反证：** 曾考虑“Shift 每次追加路点就立即回收旧 group，因而当前 shortTask 在同一次入队里必遭新 group 替换”。上述真实控制流排除**常规 queue 分支直接**通过 `0x0302DB44` 做这种事；其他游戏更新函数、间接回调、后续真实 group 重建仍可能存在。不能据此证明完整生命周期中 group 一定不变。

## 二、后继 MOVE 激活的真实顺序及 Group 空间输入

后续队列槽位真正激活时执行 `0x03025D70`。其整个原始函数内有 **15 条已解码直接 call**，未见直接调用 `0x0302DB44` 或 `0x0301B8E4`（这只是**直接 call 的负证据**，不排除其它路径或虚函数）。

- 原始 `0x03025E91` 和 `0x03026022` 是两个有条件的 `CALL 0x0301287C`，先为 UnitRoot 配置路线描述符。
- `0x030260AF CALL 0x02F2C734` 之后才创建新 shortTask；已有第12轮证据说明该 shortTask 能通过 `shortTask+0x80=&MOVEslot+0xA0` 读取当前槽位 bigTask。
- 更具体的 `0x03025FB8 MOV RCX,[RCX+0x32F8]`，接着 `0x03025FBF ADD RCX,0xB38`，于 `0x03025FC6 CALL 0x02D4BE38`。该 helper 再执行 `ADD RCX,0xB8`，即对 **group+0xBF0** 的空间记录调用 `0x0311D0CC` 转换，取回其 X/Z 分量。调用者使用这个结果与目标输入求水平角，`0x03025FEE CALL 0x0118309C` 后进一步缩放、转换，再交给 `0x03026022` 路线配置。
- 因此在**已证条件路径**中，后继 MOVE 的新路段朝向计算依赖**当前 `UnitRoot+0x32F8` group 的空间参考**。这是原生渐进转向可能正常需要的几何连续性，**不能将此来源本身判为错误**。

后续 shortTask 的 `0x02F563F4` 读取 `shortTask+0x08=UnitRoot`，`0x02F563FD` 在发包前读取**当时**的 `UnitRoot+0x32F8`，`0x02F56404` 条件性调 `0x03279E40`。它不在任务构造时永久锁定某个 group generation。

## 三、对 RMB vs Shift、根因调查和补丁位置的结论

1. **相同模式的队列 MOVE** 无论 `R9B=0` 替换还是 `R9B!=0` 追加，在本函数的入队路径都跳过**即时的** `0x0302DB44`；所以不能把这一个 group 调用点当成 RMB 专用，亦不能说 Shift 追加必立即 group 重建。
2. 两种队列语义区别依旧存在于 `0x02F50410` 和后续 MOVE→MOVE old bigTask 条件继承。但仅凭那一点，不能推出最终成员目标差异。
3. 新的精确研究目标是：**队列后继槽位激活时，从当前 group+0xBF0 获得空间基准并设置新路线 → 当前 group 晚绑定 → 按个别成员 packet/action/motor goal 生效**，确认两名相邻成员是否使用不一致的空间参考或路线代际。
4. 静态 CFG 和局部指令证明不足以认定真实 Shift 折返出现该错配，更不能取消 group 空间转换或旧方向投影，否则可能破坏正常 RMB、Shift ATTACK、渐进转弯和避障。

## 四、可复现证据与维护

- `maintenance_tools/native_shift_re/move_dispatch_branch_split_manifest.txt`：37 个原始指令编码、17 条 E8、5 条 JCC/E9；
- `maintenance_tools/native_shift_re/audit_move_dispatch_branch_split.py`：固定完整 SHA、unwind、原始字节、objdump 指令起点、真实分支目标、函数内 CFG 可达性、group/shortTask 静态链；
- `tests/test_native_shift_re_move_dispatch_branch_split.py`：合成 CFG 与反例、错误 SHA fail-closed、禁止覆盖原始 EXE、私有真 EXE 完整检查；
- 本地报告和 JSON 均没有原始游戏 EXE、DLL 或用户运行时指针。

**native_patch_authorized=false**。没有游戏内修复验证；继续只研究研究分支 `research/n1-native-shift-behavior-patch-20261009`，不改 main，不要求用户再次证明折返挤压。
