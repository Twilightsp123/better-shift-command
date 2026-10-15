# BSC N1 — 第14轮：两种 MOVE 朝向如何进入路线节点和 A 类成员发包（2026-10-15）

## 原始证据与边界

固定用户原始 Win64 `Warhammer3.exe` SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，PE ImageBase `0x140000000`；所有地址均为 RVA。当前是**严格只读静态逆向**：83/83 真实原始指令字节及 GNU objdump 指令起点、15/15 直接 E8、5/5 条件跳转、1 个具体成员虚表槽，另检查两处真实无 unwind 叶函数终止。本地完整独立审计 **17/17 回归通过（其中一项使用真实原始 EXE）**；公开 CI 无私有 EXE 时跳过原文件验证。GitHub 内置紧凑版审计和 9 项测试，可重复核验相同 83 个站点；无 Native gameplay patch，无游戏运行命中。

## 一、两种朝向输入最终写在同一个字段

上一轮已确认后继 MOVE 在 `slot+0x9A & 2` 有两路原生参数：

- bit2 非零：`0x03025E76` 从 `slot+0x98` 取原保存的 16-bit 朝向，`0x03025E91` 调 `0x0301287C`；
- bit2 为零：当前 group 空间坐标参与计算，`0x03026015` 把转换后的 AX 变成 R8W，`0x03026022` 调相同 `0x0301287C`。

现在补齐真实类型链：`0x03012893 R8W→BX`；`0x03012935 R9W=BX`，`0x03012945 CALL 0x030ECAB0`。该严格定界的无 unwind 叶函数于 **`0x030ECAFA` 写 `temporaryRouteRecord+0x38=R9W`**。

`0x0301287C` 的输出随后走 `0x03012982 CALL 0x03008894`。其内部：

1. `0x030088D0 CALL 0x031219B0` 创建普通路线节点，`0x030088D5` 保存至 `routeDescriptor+0x18`。
2. 在 `0x03121A40 CALL 0x030EC9EC` 中拷贝路线记录，`0x030ECA24/28` **把记录+0x38 的 u16 朝向复制进 node+0x20+0x38，也就是 node+0x58**。
3. 仅在 `0x03121A82` mode helper 或输入记录 `+0x4C` 的有效性条件满足时，`0x03121A99 CALL 0x030FDA9C` 才将转换结果写 **node+0x70**（`0x03121A9E`）。不能声称每次普通节点构造后该指针都立刻有效。
4. `0x03008894` 还于 `0x03008900/0E` 把临时记录 u16 朝向复制到**路线描述符+0x44**，`0x03012987` 保存 `UnitRoot+0x270=routeDescriptor`。

所以这里存在两个不同的消费者字段：**`routeDescriptor+0x18 → node+0x70` 是路线几何对象；`routeDescriptor+0x44` 是原始 16bit 朝向**。严禁混同。

## 二、两类成员消费方式必须分开

**立即 group 分发**：`0x0302DB44` 的 `0x0302DBC9/D3/D7` 确实顺序读取 `UnitRoot+0x270 → descriptor+0x18 → node+0x70`，于 `0x0302DBDB CALL 0x030D5490` 下发给该 group。后者经过阵型策略 virtual+0x48 产生 `record[i]`，按索引绑定 `member[i]`，经具体成员 virtual+0x368 接收 packet。该链**属于这条即时分支**，不是“每个 queued Shift 后继路点立刻照此执行”的证明。

**shortTask 后续 A 分发**：`0x03279E40` 在 mode helper **非零**时才沿 A 路径。若临时参数 `+0x30==0`，`0x03279E78/7F/86` 从 `group+0xA10 → UnitRoot+0x270 → descriptor+0x44` 取朝向；若临时参数 `+0x30!=0`，则优先从临时参数 `+0x32` 取明确朝向，**不经过上述默认读取**。若比例值未达到原生有效门槛，还存在从 `descriptor+0x40` 获取比例的独立回退。选择后的朝向通过 `0x030D554C` 的临时记录 `+0x38`，在 `0x030FDA9C` 条件转换后调用 `0x030D5490`。mode helper 为零时进入**另一 B 家族**，不能将本 A 逻辑套用到那条分支。

从这一证据不能断言 deferred A 当前实例使用了此前 immediate 路线 node+0x70 的**同一对象**；也尚未证明实际相邻成员最终 motor goal 错误。

## 三、ABI 额外对照：queued/immediate 的第一栈布尔不同

`0x0301287C` 保存 R8W 之后，prolog `push rdi; sub rsp,0xA0`，callee `[rsp+0xD0]` 映射 caller `[rsp+0x20]`，`[rsp+0xD8]` 映射 caller `[rsp+0x28]`。

已检查的 queued 两处调用都设置第二布尔为 1，第一布尔为 0；即时 group 一处调用第二布尔为 1，第一布尔为 1。故在函数初始状态检查通过时，**这三处都选择外部 descriptor/普通节点分支**（第二布尔），并非某一路固有选择 `0x03012990` 的内嵌 descriptor。第一布尔可有条件影响 `0x030128D0 → 0x03041B28` 的队列预处理。此处不把这些模式绑定为玩家 Shift/RMB 键码。

## 四、下一步真正的缺口

已打通**命令朝向 → descriptor/node → A 类 record 生成输入**；仍缺的是**同一次 queued inherited MOVE 的实际 bigTask、shortTask、group generation 与两个 member action/motor goal 的对象身份和目标安装时间**。在这个缺口解决前不能修改 bit2、强制替换旧方向投影、清空 node/subtask，不能宣称 Shift 折返的士兵挤压已修复。

维护代码：`maintenance_tools/native_shift_re/audit_route_heading_to_member.py` 和 `tests/test_native_shift_re_route_heading_to_member.py`。本轮完整、独立可下载的本地证据包另提供带83条来源类别的 manifest、17项更细的测试、脱敏 JSON 和本中文研究记录，不包含游戏 EXE 或原始运行时内存地址。
