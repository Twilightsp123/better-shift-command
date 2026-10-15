# BSC N1 — 队列 MOVE 与即时 Group 重建分支互斥及后继朝向来源（2026-10-15，第13轮）

## 二进制与证据等级

目标是用户给出的固定 Win64 原始 `Warhammer3.exe`，SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`；所有地址为 PE ImageBase `0x140000000` 下的 RVA。

第13轮对原始 EXE 的只读验证：**41/41 完整指令字节和 GNU objdump 真正指令起点、17/17 E8 直接调用、6/6 E9/JCC 目标**，再用同一 unwind 所属函数内的静态 CFG 可达性检验确认两路互斥。本地完整验证 **13/13 PASS（其中1项使用用户原始 EXE）**。GitHub 新增的合同测试有12项，其中1项在没有私有 EXE 的公开 CI 必须 SKIP。这里的证明等级是 **EXACT_ORIGINAL_EXE_STATIC + SYNTHETIC_CONTRACT**；并非用户 RMB/Shift 键位的运行时辨识、不是物理碰撞根因验证，也没有 Native gameplay patch。

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

- `maintenance_tools/native_shift_re/move_dispatch_branch_split_manifest.txt`：41 个原始指令编码、17 条 E8、6 条 JCC/E9；
- `maintenance_tools/native_shift_re/audit_move_dispatch_branch_split.py`：固定完整 SHA、unwind、原始字节、objdump 指令起点、真实分支目标、函数内 CFG 可达性、group/shortTask 静态链；
- `tests/test_native_shift_re_move_dispatch_branch_split.py`：合成 CFG 与反例、错误 SHA fail-closed、禁止覆盖原始 EXE、私有真 EXE 完整检查；
- 本地报告和 JSON 均没有原始游戏 EXE、DLL 或用户运行时指针。

**native_patch_authorized=false**。没有游戏内修复验证；继续只研究研究分支 `research/n1-native-shift-behavior-patch-20261009`，不改 main，不要求用户再次证明折返挤压。

## 五、第13轮继续：slot+0x9A bit2 的命令描述符来源与分支反证

新增独立只读审计 `audit_move_slot_bit2_provenance.py`：固定用户 EXE **19/19 原始指令字节及 objdump 起点、2/2 E8、3/3 JCC** PASS，另检查无 unwind 叶函数结尾。两个本地审计模块合计 **23/23 单元测试通过**（含两项真实 EXE）。公开仓库中的两个测试模块合计定义 24 项，其中两项需要用户私有 EXE，不能把没有 EXE 的 CI 当原码实测。

此处已经闭合真实 typed 字段来源：

1. 统一 MOVE `0x030323FF MOV RDI,R8` 把当前**命令描述符指针**保存在 RDI；入队路径 `0x030326DB MOV R9,RDI` 把它传给 `0x030326E4 CALL 0x030090BC`。
2. 这个 MOVE slot 构造器 `0x030090C6 MOV RBX,R9`，`0x030090DB LEA RCX,[slot+0x40]`、`0x030090DF MOV RDX,RBX`，`0x030090E2 CALL 0x03009100` 复制描述符至槽位。
3. 经真实无 unwind 叶函数 `0x03009100..0x030091D1`，源 `descriptor+0x5A` 的低 7 位用逐位 XOR/AND 操作搬运到 `(slot+0x40)+0x5A=slot+0x9A`。最关键的 bit2 由 `0x03009186..0x03009190` 复制；合成 128×128 个源/初始目的位组合验证了此逐位结果与 source 低7位一致。这里**不能**假定高 bit7 也被复制。
4. **源可以在复制前被 CA 原生代码修改。** 在符合路线几何重整条件的入队支，`0x03032679 OR BYTE [descriptor+0x5A],0x06`，故强制设置 bit1 和 bit2；`0x0303249E` 与 `0x03032577` 等原生 JCC 可直接到 `0x030326A2`，绕过这次 OR。
5. 后继 MOVE 激活 `0x03025E5B TEST BYTE [slot+0x9A],0x02`、`0x03025E69 JE 0x03025F79`。只有 slot bit2 为零，才能**经这条分支**读取当前 group+0xBF0 空间位置基准来重算朝向。由逻辑与真实机码共同证明，执行过上述 `OR 0x06` 的本次命令**不会**选中这条特定采样分支；绕过 OR 且 bit2 原先为零的命令则可能选中它。

这是一条实际的 `命令描述符旗标 → 可能的命令几何归一化 → MOVE slot 旗标 → 后继转向几何输入选择` 的有类型数据链。**它不是键盘 Shift 键身份、不是哪个兵模最终目标在游戏内出错的证据。** 修改 bit2 可能直接改变原生路线/避障行为，当前禁止 gameplay patch。

新增源码 `maintenance_tools/native_shift_re/audit_move_slot_bit2_provenance.py`、测试 `tests/test_native_shift_re_move_slot_bit2_provenance.py`，原始 EXE/包含进程地址的 JSONL 不提交 GitHub。下一步沿这两个 bit2 分支比较具体成员目标记录与动作代际，优先查是否存在生成不同但成员未同步切换的目标。

## 六、同一个路线配置器的两种 R8 朝向参数来源（当前优先）

继续在 `0x03025D70` 同一原始 unwind 函数的两条分支检查 Route Configurator 的参数来源：

- `slot+0x9A & 0x02 != 0`：在 `0x03025E76 MOVZX R8D,WORD PTR [MOVEslot+0x98]` 直接使用槽位保存的朝向码。此后至 `0x03025E91 CALL 0x0301287C` 没有新的 R8 写入（按原始解码顺序核查）。
- `slot+0x9A & 0x02 == 0`：`0x03025E69 JE 0x03025F79` 进入当前 group 空间坐标采样；经 `0x02D4BE38 → 0x0311D0CC` 得到 X/Z，`0x0118309C` 计算角度并由 `0x00531E54` 转换，`0x03026015 MOVZX R8D,AX` 交给 **同一个** `0x03026022 CALL 0x0301287C`。此后至 CALL 同样无 R8 写入。

由此，**在后继队列 MOVE 的这两个具体条件分支中，首次明确对照的原生路线几何参数差异就是 R8 朝向码的来源**：预存的 slot 方向 vs 当前 group 空间位置导出的方向。旧任务状态继承可能影响传入的其它字段，但本节不把它们等同于上述 bit2，也不把 bit2 当用户 Shift 键。

新增两处原始字节及 decoded instruction-start 验证（`0x03025E76`、`0x03026015`），完整第一审计现为 **41/41 opcode/starts、17/17 E8、6/6 JCC/E9**；两审计本地共 **23/23 PASS**（2 项使用私有原始 EXE）。下一步优先验证这两个 R8 输入最终形成的 `UnitRoot+0x270` 路线描述符是否在成员 `record[i]` 的空间坐标/朝向处造成错误的成员交叉；现在不能直接判定其中一个更“正确”，也不能统一设置 flag。
