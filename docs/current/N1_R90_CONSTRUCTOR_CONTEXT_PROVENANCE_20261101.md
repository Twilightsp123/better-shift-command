# Better Shift Command — R90 原生 Root→Member 上下文构造来源与 C 类型归属（2026-11-01）

## 0. 结论等级

**本轮新成果：**首次在原版《Total War: WARHAMMER III》的同一个精确 EXE 中，将 R89 的 C 类对象构造参数通过 G/K/子配置对象传递到 UnitRoot 的 `+0x38`，再联系 R82 已找到的普通士兵 `+0x58` 构造来源。这是一条**有条件的原始构造链**，不是因为几个对象恰好有同样偏移就认作同类。

**明确保留：**这条代码路径还不等于某次实机玩家 Shift 折返的动态实例与该事件分发器必然相同；未证明构造后所有上下文不被替换、所有士兵属于此路径，或接触订阅者写入士兵的实际运动字段。因此没有 gameplay 修复或 Hook。

源文件：用户原版 `Warhammer3.exe`，232531920 字节，SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`。AMD64 / PE ImageBase `0x140000000`。文中地址均为 RVA，所有确认指令由本轮 LLVM 原生反汇编和原始机器码检查交叉验证。

## 1. C 本体如何被交给 G 和 K（相对于 R89 的新增身份桥）

- C 构造器 `0x02D98420–0x02D99A8B` 内：`0x02D9846D MOV RDI,RCX` 保留当前正在构造的 C；`0x02D98D8E MOV [RBP-0x40],RDI` 与 `0x02D98D92 MOV [RBP-0x38],RDI` 将**同一 C 指针**放到相邻两个栈槽。
- `0x02D99069 LEA RDX,[RBP-0x40]`，`0x02D99070 E8→0x02D9A004` 以描述符指针构造 G。因此 G 构造器 `0x02D9A046 MOV RAX,[RDX+0x08]` 读取的确定是栈 `[RBP-0x38]` 中刚保存的 C 指针；`0x02D9A04A MOV [RCX+0x08],RAX` 把它写入 G+0x08。`0x02D9A043 MOV R14,RDX` 保存描述符指针，非另一个 C 对象。
- G 构造器后续 `0x02D9A7F7 MOV RDX,R14`、`0x02D9A80E E8→0x02D9F9C8` 用同一描述符构造下游 K；K 构造器 `0x02D9F9F4 MOV RAX,[RDX+0x08]`、`0x02D9F9FB MOV [RCX+0x08],RAX` 同样复制 C→K+0x08。
- G 的另一个独立字段 `G+0xF0` 在 `0x02D9A373 E8→0x02DA0800` 后由 `0x02D9A381` 发布为 P；R89 已证明 P+0x1D8 的虚表 `+0x10→0x02DD06F0`。这是与下游 K 共同来源的 G 的两个**不同字段/子系统**，不能把 K 或 P 误说成成员对象本身。

这里的严格正结论是 **C→G/K 构造期间的上下文指针值来自同一个已命名的 `0x02D98420` 构造对象**。执行顺序、条件分支与运行期替换仍须额外核验，故不是动态单实例覆盖证明。

## 2. K→子记录→配置对象→UnitRoot 的指针传播

- `0x02DA052D MOV RCX,RBX`、`0x02DA0530 E8→0x02DB690C` 允许 K 在自己的初始化函数中进入建成员/Root 的下游。`0x02DB6934 MOV RDX,[RBX+0x08]` 读取保存的上下文 C；`0x02DB694C MOV RDX,[RDX+0x64540]` 显示它还有很高的偏移布局；这与 C 构造对象约 `0x64818` 字节的已知分配规模相符，但**单凭大偏移本身不构成类型证据**。
- `0x02DB6981 MOV RDX,RBX`、`0x02DB6999 E8→0x02D953D4`：K 作为输入描述符传入子记录构造器。后者 `0x02D95408 MOV RAX,[RDX+0x08]`、`0x02D9540F MOV [RCX+0x08],RAX`，把 K+0x08 的 C 指针传给子记录+0x08。
- `0x02D955B2 MOV RDX,RBX`、`0x02D955B5 E8→0x02D95D98` 创建配置对象。`0x02D95E3C MOV RAX,[RDX+0x08]`、`0x02D95E44 MOV [RCX+0x138],RAX` 让配置对象+0x138 取得 C。它**不是** C 对象自身的 +0x138，不能混淆对象类型。
- 在特定下游循环 `0x02D96607 MOV RDX,RSI`、`0x02D96613 E8→0x02D91E74` 进入 Root 分配包装器。包装器 `0x02D91E96 MOV RBP,RDX`、`0x02D91EB3 MOV RDX,RBP`、`0x02D91EBE E8→0x0300C998` 将配置指针交给 Root 构造器。注意 wrapper 还有其它调用入口；不能外推所有 Root 都这样创建。

## 3. Root+0x38 的真实 setter：本轮关键新发现

在 `0x0300C998–0x0300D47B` 中，按原始 x64 Windows 调用约定，此时 RCX 是正在构造的 Root、RDX 是上述配置对象：

| RVA | 实际指令 | 身份含义 |
| --- | --- | --- |
| `0x0300C9B4` | `MOV RAX,[RDX+0x138]` | 从配置对象读取 C |
| `0x0300C9BF` | `MOV [RCX+0x30],RAX` | 写 Root+0x30 |
| `0x0300C9C6` | `MOV RAX,[RDX+0x138]` | 再次读取同一配置字段 |
| `0x0300C9D1` | `MOV [RCX+0x38],RAX` | **原生 Root+0x38 writer** |
| `0x0300C9E5` | `MOV R10,[RAX+0x440]` | 后续将该上下文当成含 +0x440 结构的对象 |

还在成员相关处理器 `0x03012F44` 的 `0x03012FE7→0x03012FEB→0x03012FF2` 看到：`[Root+0x38]→[C+0x440]→[G+0x1E0]`。这是和 Root 初始化独立的结构消费者。

R82 已证明：在指定创建路径中 `0x03013235` 将 `&Root+0x30` 传入普通成员构造器 `0x03052BA8`，其基础构造器 `0x03141810` 读取 `[RDX+0x08]`、`0x03141814` 写入 `member+0x58`。因为 `RDX=&Root+0x30`，这就是 `[Root+0x38]`，不是 RDX 的任意 8 字节。成员自身 `0x03052F62/66/6D` 又把它传入内嵌局部控制器 `member+0x718/+0x720`。

于是有界数据图为：

```text
C ctor(this = RDI)
  -> stack descriptor[-0x40,+0x08] = C
  -> G+0x08 = C
  -> K+0x08 = C
  -> child+0x08 = C
  -> config+0x138 = C
  -> Root+0x30 / Root+0x38 = C
  -> member+0x58 = C      (bounded member constructor path)
  -> member+0x720 = C     (bounded embedded controller init)

另外同一 C 构造器:
  C+0x440 = G
  G+0xF0 = P
  P+0x1D8 virtual receiver slot +0x10 -> 0x02DD06F0
```

这在字段来源层面消除了 R89 的一个主要疑点：**对于这条受控构造路径，entry member+0x58 的上下文有可回溯的 C 构造器来源。** 但不意味着接触发生时该成员上下文仍指向同一次 G/P，尤其没有证明运行期线程、对象生命周期和玩家 Shift route generation。

## 4. 有界止损：为什么还没有找到“挤压”根因

`0x030852A7` 虚接收器与 `0x02DD06F0` 事件分发构造链已有更强的类型来源。但真实事件接收函数仅经订阅者 `vtable+0x10` 判断后通过 `subscriber->vtable+0x08` 发布记录。R89 已审的直接方法没有已确认的成员 pending/XYZ 写回；本轮**没有识别一个经过注册者类型闭合的具体订阅者及其运动写入**。

因此：

- `C_TO_ROOT_MEMBER_CONSTRUCTOR_PROVENANCE = STATIC_PROVEN_ON_BOUNDED_PATH`
- `CONTACT_RECEIVER_CONSTRUCTOR_TYPE = STATIC_SUPPORTED_ON_BOUNDED_PATH`
- `ALL_RUNTIME_INSTANCE_IDENTITY = NOT_PROVEN`
- `CONTACT_SUBSCRIBER_TO_MEMBER_MOTOR = NOT_PROVEN`
- `SHIFT_CROWDING_ROOT_CAUSE = NOT_PROVEN`
- `LIVE_HOOK = false; GAMEPLAY_PATCH = false`

**后续优先级：**R91 只允许查一个有明确注册代码的 `0x02DD0763` 订阅者，问它是否通向普通成员运动字段；若找不到、或仅为事件广播则止损该路线。然后转向本项目更核心的“同一个 Shift 路段不同成员转向阶段和世界目标怎样同步”，不再重复 member+0x738、A packet=最终目标、Lua 重发 MOVE、全局改积分器等已否决的方案。

## 5. 检查、交付与对照

原始 EXE 验证结果：**67/67 完整原码字节与 LLVM 指令起点、12/12 E8 调用目标、67/67 PE unwind 对应检查，涉及 14 个不同的函数归属**。独立 Python unittest **27/27 PASS**（含真实 EXE 两项）；公开环境 **25 PASS / 2 SKIP**（SKIP 是商业 EXE 缺失，不得写成实机通过）。

R90 资源包含：本报告、14 段实际原生反汇编、原始机器码 pin 清单、PE/指令/E8 审计器、单元测试、原始验证 JSON、原始测试日志、SHA256 清单、R89 完整 ZIP 作为嵌套历史。**不包含或重新分发商业游戏 EXE**。GitHub 维护状态写入单独 `GITHUB_STATUS.txt`；最终 Actions 结果未确认前不能声称 CI 成功。