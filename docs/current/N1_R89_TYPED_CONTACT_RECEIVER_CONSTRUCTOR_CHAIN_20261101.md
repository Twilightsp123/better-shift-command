# Better Shift Command — R89 有类型接触虚接收器构造链（2026-11-01）

## 一、本轮真正的新发现

相对于 R88 已证明的 Steering `entry member+0x58 → C+0x440 → G+0xF0 → P+0x1D8 → vtable+0x10` **读侧指针链**，R89 在用户给出的当前原始 `Warhammer3.exe` 中找到相应 **C / G / P 构造与发布链**，并具体解析了 P 的 `+0x1D8` 虚方法实现。

**游戏文件**：232531920 字节，SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`；PE AMD64、ImageBase `0x140000000`；所有地址均为 RVA。

### 链 A：构造的 C 类型发布 G

在 PE unwind 函数 `0x02D98420–0x02D99A8B` 中：

- `0x02D9904E: LEA R14,[RDI+0x440]`：保存 C 的 `+0x440` 槽位地址；此处 RDI 为当前构造对象。
- `0x02D99070: E8 → 0x02D9A004`：在分配非空路径用 `RCX=allocation` 构造 G。
- `0x02D990A6: MOV [R14],RAX`：把 G 构造返回结果（或分配失败路径的零值）写入 C 的 `+0x440`。

这不是对原始 EXE 中 `[C+0x440]` 随意猜测的 setter；源地址和下游构造器被真实 E8 连通。

### 链 B：G 发布 P

`0x02D9A004–0x02D9AD82` 中：

- `0x02D9A02F: MOV RDI,RCX` 保持构造实例 G。
- `0x02D9A357: MOV ECX,0x37E8`：申请 `0x37E8` 字节 P 类型大小，之后按空指针条件分流。
- `0x02D9A373: E8 → 0x02DA0800`：把已分配内存传入 P 构造器。
- `0x02D9A381: MOV [RDI+0xF0],RAX`：把 P（或分配失败的零值）发布到 G 的 `+0xF0`。
- `0x02D9AD5C: MOV RAX,RDI`：G 构造器正常返回原 G 指针。

因此这个具体 C/G/P 构造链与 R88 读侧两级字段偏移一致。**但这还不能独立证明 Steering 当前入口 member+0x58 指向的运行期 C 一定是这里构造的 C 类实例**。尚须从 `[Root+0x38]` 的上游构造源或可靠实例证据闭合类型，不得将偏移相同误当全局类同一。

### 链 C：P 内嵌虚对象 +0x1D8

`0x02DA0800–0x02DA2CD6` 中使用同一 P 对象的不同偏移：

- `0x02DA09DC`: `LEA RAX,[RDI+0x1D8]`，子对象早期初始化；初始虚表可能在后续被重设，不能只看第一个 setter。
- `0x02DA0FDF`, `0x02DA1AD7`, `0x02DA2065`：另有 `P+0x898/+0x1F98/+0x3718` 内嵌子对象初始化，与 `0x0300BC91...0x0300BCA6` 另一原生调用处的 P+0x898 使用形成独立结构对应。
- `0x02DA209D`: `MOV RAX,[RBP+0x40]`；`0x02DA2107: LEA RCX,[RIP+...]` 得到完整 VTable RVA `0x03AB1B48`；`0x02DA210E: MOV [RAX+0x1D8],RCX`。
- 从真实 EXE 虚表 `[0x03AB1B48 + 0x10]` 读取指针，等于 `0x140000000 + 0x02DD06F0`，对应合法 PE unwind 函数 `0x02DD06F0–0x02DD07DF`。

这是**有类型构造路径下**的虚表槽解析，不是 R88 期间无对象来源的 `+0x1D8` 原码关键词搜索；仍未全局排除继承覆盖和运行期替换。

## 二、接收方法的直接行为（真实汇编）

具体候选虚方法 `0x02DD06F0` 以 `RCX = receiver_this`、`RDX = 局部接触记录指针` 调用：

- `0x02DD070B: MOV R14,RDX` 保存记录参数。
- 从 `receiver_this` 的 `+0x10/+0x20` 等字段读取订阅者指针集合和计数，辅助函数 `0x0132C544` 合并/处理当前集合。
- 循环中从容器取出 `RSI = subscriber`，在 `0x02DD0753` 调 `subscriber->vtable+0x10`，检查 AL 条件。
- 条件成立时，`0x02DD075D: MOV RDX,R14` 恢复原始接触记录，`0x02DD0763` 调 `subscriber->vtable+0x08` 转交给订阅者。

**限定结论：**此方法直接实现订阅者分发边界；在受审直接函数体中没有确认普通成员 XYZ `member+0x88/+0x8C/+0x90` 或 pending `member+0x13C/+0x140/+0x144` 写入。其下游任一具体订阅者是否会写运动字段，仍然**未证明**。

不能把这个函数当成“已经证明的局部避障力修正器”，也不能因为它自己不直接写运动就认为 contact 永不影响士兵。

## 三、独立的字段类型对照

在另一原生函数 `0x0300B178–0x0300BDD6`：

`0x0300BC91 MOV RCX,[RAX+0x440]` → `0x0300BC98 MOV RCX,[RCX+0xF0]` → `0x0300BC9F ADD RCX,0x898` → `0x0300BCA6 E8→0x01C3ADF0`。

辅助函数 `0x01C3ADF0` 使用候选容器的 `+0x10/+0x20` 数组、`+0x0C/+0x1C` 计数，按值判重并追加元素。说明这里的 P+0x898 是一类订阅/登记集合接口或类似注册表项，不是士兵物理 XYZ。

该独立调用为 C/G/P 的布局提供进一步交叉验证；但 `C` 在两个不同调用上下文中的对象类型同一性仍须上游证明。

## 四、验证纪律与结果

- 实际原始 EXE：**26/26** 完整机器码、**26/26** LLVM 真实指令起点、**3/3** E8 目标、**8/8** PE unwind 归属、**1/1** `VTable+0x10` 实际方法地址均 PASS。
- Python unittest：**14/14 PASS**（其中 2 个读取真实 EXE，另 12 个是纯代码契约）。
- 不带商业 EXE 的公共测试：**12 PASS / 2 SKIP**；不能把 CI 的 SKIP 说成真实 EXE 通过。
- 无运行游戏、无 Hook、无 Windows 实机动态验证、无 gameplay patch；不修改商业 EXE。

## 五、研究止损和下一项工作

目前最值得补的两条**精确身份边**：

1. 从 R82 `[Root+0x38] → member+0x58` 的上游构造参数，判断 Root 的上下文究竟是否为 `0x02D98420` 创建的 C 类型；如果类型无法闭合，不能将 `0x02DD06F0` 宣称为已实机确定的唯一接收实现。
2. 若上述同一性成立，再选择**一个** `0x02DD0763` 的注册订阅者类型，追踪其 `vtable+0x08` 是否在同成员、同 Shift route generation 内写 pending、速度或世界目标。若没有明确有类型注册来源则应止损，研究重心转向成员转向相位与阵型空间目标。

**严格状态：**`C_G_P_CONSTRUCTOR_CHAIN=STATIC_PROVEN`; `P_1D8_VTABLE_SLOT10=STATIC_PROVEN_FOR_CONSTRUCTED_TYPE`; `MEMBER_CONTEXT_C_TYPE_IDENTITY=NOT_PROVEN`; `CONTACT_SUBSCRIBER_TO_MEMBER_MOTOR=NOT_PROVEN`; `SHIFT_CROWDING_ROOT_CAUSE=NOT_PROVEN`; `LIVE_HOOK=false`; `GAMEPLAY_PATCH=false`; `main_unchanged=true`。