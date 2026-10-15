# BSC N1 — 2026-10-16 第18轮：fallback node1 的原生管理器重算与有效性门槛

固定用户原始 Windows x64 EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，PE ImageBase `0x140000000`；地址全为 RVA。独立只读机器码审计 **78/78 指令与 GNU objdump 起点、9/9 E8、9/9 JCC、1/1 普通 B 类型虚表槽** PASS；本地**13/13回归通过**，含真实原始EXE、错误SHA与 Python -O 守卫。代码 `maintenance_tools/native_shift_re/audit_b_fallback_manager_retry_20261016.py`，测试 `tests/test_native_shift_re_b_fallback_manager_retry.py`。本地资源包有完整 JSON、disassembly 与回归日志。仅静态证据，不宣称实际 Shift 游戏进程命中。

## 1. 纠正“fallback 必须等 mode helper 变为1”

普通 B `+0x08=0x03271B0C` 在 `aux+0x60=NULL` 时通过 `0x030ECA50` 准备普通节点 `node1` 的输入。叶函数 `0x030ECAA4` 设置 `record+0x48=0xFFFFFFFF`，`0x030ECAAB` 设置 `record+0x4C=0`。`0x03271C04` 调 `0x031219B0`，生成 `node+0x04=1, node+0x08=0, node+0x70=NULL` 并通过 `0x0310E770` 链接进管理器 `+0x2D0` 的节点链。构造当次仅当 mode helper 为1或 record+0x4C为1才能立即转换，因此 fallback 可能留待下次管理器更新；这并非死节点。

**另一条直接已证重算路径：** `0x03128E80` 扫描 `manager+0x2D0`。对 `node+0x04!=0、node+0x08==0` 且预算许可的节点，于 `0x0312907E` 取 `RDX=&node+0x20`，`0x03129085 CALL 0x0311BE18` 进行验证；结果非零时 `0x03129092 CALL 0x030FDA9C` 转换，写 `node+0x70=RAX`，再设 `node+0x08=1`。此路径不要求再次调用 `0x03121A82` 的 mode helper=1 创建分支。

处理预算：`0x03128EC6` 赋 `R13D=1`，本节点循环 `0x03129038` 设 `EBP=0`，`0x03129073/76` 比较 `EBP<1`，`0x0312909B` 在一次通过验证的转换尝试后递增 EBP。**因此每次此管理器调用最多一次此类重算尝试**，不是宣称每帧一定更新或节点队列总是含两代对象。

## 2. 真正的后续验证值来自 UnitRoot 状态

`0x0311BE18` 若 `record+0x48!=0xFFFFFFFF` 直接返回它；若为哨兵值则沿 `[record+0]` 取上下文；此为空时沿 `[record+0x08]→+0xA10` 取得 UnitRoot，再调用无 unwind `0x03037A48`。该叶函数依据 `root+0x98` 指针及其 `+0x04` 状态，返回 `root+0xA4` 或 `root+0x184` 字段。fallback 记录 `record+0` 已设零、`record+0x08` 来源于关联 group，因此它依赖**后续 UnitRoot 的动态验证值是否非零**，而非“mode 必然从0变1”。

## 3. 必须保留的边界

管理器转换后写 `node+0x70`，紧接着写 `node+0x08=1`，未在中间要求返回的 RAX 非空；普通 B 后续 `+0x10=0x03281520` 检查 `node+0x08`，随后读取 `node+0x70`，这一入口也没有独立的非空判断。**若转换器返回NULL，静态上允许“已处理=1、路线NULL”的条件性组合**，之后此管理器重算门槛因+0x08非零而关闭。尚未证明 `0x030FDA9C` 会在真实 Shift 折返时返回NULL，也没证明这和兵牌挤压有关，禁止直接更改有效标志或跳过 CA 路线生成。

**下一步唯一数据缺口：** 继续从 `0x030FDA9C` 的返回路线对象类型/有效性和引用生存期入手，比较是否真的存在空路线或被不同 group generation 消费。旧 shortTask 正常清退、普通 B 共用成员生成器、fast/fallback 发包互斥的静态反证继续有效。不要求用户重复游戏折返；不修改 `main`、原始EXE或公开上传 Frida 指针日志。`native_patch_authorized=false`。
