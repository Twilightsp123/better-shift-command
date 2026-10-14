# BSC N1 / WH3 9.0.3 — 大任务、路线节点和成员发包共享的原生几何管理器

**2026-10-14，新增精确原始 EXE 的只读静态审计。** 固定 SHA256：`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，PE64 ImageBase `0x140000000`。本地原始 EXE **81/81** opcode + GNU objdump 指令起点 / PE unwind 或显式叶函数边界、**12/12** E8、**2/2** typed vtable PASS；同环境 **13/13** 单元测试通过（含原始 EXE）。这不是玩家 Shift 实机命中、碰撞证明或 Native gameplay 修复。

## 一、本轮真正新建的对象/字段链

过去已知道 `group+0x10` 是 `[UnitRoot+0x38]` 的**指针值**（从 `0x030C2C56 → 0x030C2D40 → 0x030C2D4E` 的构造器可证），`group+0xA10` 保存 UnitRoot。现在又从真实调用者的字段来源证明 **两类原生使用者共享 `[[context+0x440]+0x160]` 的几何管理器布局**，而不是因为字段名同为 `+0x160` 就猜对象相同：

```text
UnitRoot
  └── [UnitRoot+0x38] = context
        └── [context+0x440] = routeContext
              └── [routeContext+0x160] = manager
                     ├── manager+0x1F0 : 可遍历的大 MOVE task 链表
                     │     └── bigTask+0x160 : 此 task 自身的 nextSubtask（独立字段）
                     ├── manager+0x2D0 : 另一组路线节点列表
                     └── manager+0x18 : 多入口共用的 0x030FDA9C 转换器子对象
```

**静态指令证据：**

- 入口 `0x02DD5A2C` 的 `0x02DD5B5D` 从关联 context 的 `+0x440` 读取调用接收者，`0x02DD5B6C` 调用 `0x02DD579C`。后者自身也在 `0x02DD57CE/57D2` 读取其 `+0x08` 返回的 context，再到 `context+0x440`，为该对象的反向来源提供交叉检查；`0x02DD58D7` 取该 routeContext 的 `+0x160`，`0x02DD58DE` 调用 `0x03128E80`。
- manager 在 `0x0310ED2C` 的 `0x0310EDA7 → 0x030EE850` 创建大任务，`0x0310EE26` 首次保存到 `manager+0x1F0`；`0x03128E80` 的 `0x03128EA8` 从同一 `manager+0x1F0` 读取这些大任务，`0x03128F1D` 可调用 `0x0311DE74` 状态推进。**这一层证明了 manager 与大任务的所属关系。**
- group 成员发包分支 `0x030D554C` 在 `0x030D55AD/C7/DD` 读取 `group+0x10 → context+0x440 → routeContext+0x160`，于 `0x030D55E4` 使用 `manager+0x18`，`0x030D55F5` 调 `0x030FDA9C`，结果随后进入 `0x030D5603 → 0x030D5490` 的逐成员 `record[i]` 发包。

`0x02DD579C` 的调用者与 group 来源使用同一 context/routeContext 字段布局，这是程序层的对象类型/来源关系；**没有来自某次玩家输入的同一时刻指针样本**，仍不能说特定 Shift instance 必然进入两条路径。

## 二、三处使用**同一个转换器、同一种管理器子对象**，但输出目的不同

| 路径 | E8 原始调用 | 第一个参数 | 转换结果的用途 |
| --- | --- | --- | --- |
| 先前原生路线描述符创建 `0x031219B0` | `0x03121A99 → 0x030FDA9C` | `LEA RCX,[manager+0x18]`（`0x03121A91`） | 保存到本地路线节点 `+0x70`（`0x03121A9E`） |
| manager 中路线节点处理 `0x03128E80` | `0x03129092 → 0x030FDA9C` | `LEA RCX,[manager+0x18]`（`0x0312908E`） | 保存到另一路线节点 `+0x70`（`0x03129097`） |
| group 成员发包 `0x030D554C` | `0x030D55F5 → 0x030FDA9C` | 读 `routeContext+0x160` 后 `ADD RCX,0x18`（`0x030D55DD/E4`） | 作为 `0x030D5490` 阵型 `record[i]` 生成器输入 |

其中 `0x03008894` 的路线创建在 `0x030088C2/C9` 同样读取 `context+0x440 → routeContext+0x160`，随后调用 `0x031219B0`，进一步核对第一条路径的来源。

转换器 `0x030FDA9C` 一进入就通过 `0x030FDAC0` 保存第一个参数到 `RSI`；在两个受状态约束的原生分支写入 `RSI+0x1D0`（`0x030FDEB0`、`0x030FE095`）。当第一个参数为 `manager+0x18` 时，该字段就是 **`manager+0x1E8`**。它证明多入口共用同一类可变计数空间；**不能将它命名为路线 generation ID，也不能认为每次调用都加 1**。

## 三、条件性交接、先后关系和负证据

在 `0x03128E80` 一次 manager Tick 的函数顺序上，`0x03128F1D` 的大任务状态推进在 `0x03129092` 的路线节点转换之前。大任务 state=1 仅在公共生成器成功且重新计算 `bigTask+0x24 == 1` 时，才将旧子任务引用移到新子任务的 `+0x20`，并覆盖 `nextSubtask+0x48..+0x54` 的旧朝向投影。**这不是证明在同一次调用里一定发生了该投影并随后产生碰撞。**

同样重要：`manager+0x2D0` 路线节点与 `manager+0x1F0` 大任务是两个不同对象列表；目前**仍缺具体 `bigTask.nextSubtask` 如何成为 `0x030FDA9C` 第二参数所指路线记录的真正字段级桥接**。虽然它们共享管理器，不得将 `bigTask+0x160`、`routeContext+0x160` 或 `node+0x70` 三者强行判为同一个指针。

以前已通过机器码证明成功 MOVE→MOVE 任务继承时在允许清退条件下会移除旧 shortTask。因此本轮不会再拿旧 shortTask “自动复活”当根因，也不建议清除大任务 `+0x158` 或取消旧方向投影。普通 RMB 和 Shift 都使用相同原生机制；本轮无键位实例身份或碰撞因果证明。

## 四、下一处最小、可落地的原生比较

沿 `manager+0x1F0` 的大任务及其 state=1 `nextSubtask+0x20/+0x48..0x54`，追踪 `manager+0x2D0` 的节点创建输入与节点 `+0x20/+0x70`；精确比较同一 manager 中二者的数据传播，明确哪一条允许旧目标映射影响新阵型记录。另要保留 CA 的按成员朝向修正 `0x0307F478` 和位置修正 `0x0307F5C8`，不能重写成瞬转。

只有真正证明具体成员目标索引或新旧路段对应异常，才制作带 SHA、线程/ABI 和失效回滚保护的最小 Native Patch；当前 `native_patch_authorized=false`。无需玩家重复证明 Shift 挤压。

## 五、交付物

- 只读审计源码：`maintenance_tools/native_shift_re/audit_shared_move_geometry_manager.py`
- 13 项测试：`tests/test_native_shift_re_shared_move_geometry_manager.py`
- 脱敏结果：`maintenance_tools/native_shift_re/evidence/20261014_shared_move_geometry_manager_static.json`
- 当前报告：`docs/current/N1_903_SHARED_MOVE_GEOMETRY_MANAGER_20261014.md`

原始 EXE 与用户含指针的 JSONL 不上传 GitHub。只提交研究分支，不修改 `main`。


## 2026-10-14 第13轮 · B 家族大任务引用→旧子任务几何→路线节点的类型化静态链（最新）

**重要纠错：** `0x03AE00E8`、`0x03AE0108`、`0x03AE0128` 是由三个不同构造器实际安装的相邻虚表；`0x03281408` 真实属于**第三张** `0x03AE0128+0x10`，尽管该槽地址数值上也等于第一张表+0x50。绝不能跨对象类型拼接。短期 MOVE task `+0x74` 影响辅助对象是否沿 `0x03263E7C→0x03263D68` 将关联大任务指针写入 `aux+0x20`（并对非空任务引用增加 `+0x18` refcount）。B 型任务构造器 `0x03263AB0` 把该辅助对象放到自身 `+0x58`；类型化 `+0x10→0x03281408→0x03281444` 依当前节点、`aux+0x20` 及 `task+0x158` 条件，分叉到普通 `0x031219B0` 或大任务特化 `0x03121ABC` 路线节点构造。特化构造器 `0x030ECB10` 以**独立第六个 ABI 参数**读取大任务 `+0x80/+0x84/+0x88/+0x90/+0x98/+0x158`，`0x030FE1E4` 沿旧子任务 `+0x08` 链将各自 `+0x18` 几何输入关联为原生路线，结果存 `node+0x70`，同时将 `node+0x08` 初始标记有效，因而随后一般重算并非无条件立刻覆盖它。原始 SHA `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` EXE 实际完成 **168/168 opcode/objdump，22/22 E8，5/5 JCC，3/3 RIP vtable install，3/3 typed slots**；本地 **18/18 回归 PASS**。详见 `docs/current/N1_903_TYPED_BIGTASK_B_ROUTE_NODE_BRIDGE_20261014.md`、新只读审计与测试。**未证明某个玩家 Shift MOVE 实例命中 B 类型，也未证明 node+0x70→record[i]→motor goal 的错误因果；禁止 Native gameplay patch，禁止清空旧 subtask 以破坏原生渐进转弯。**


## 2026-10-14 第13轮追加：A 逐成员记录与 B 类型路线节点在同一次分发中互斥（原码反证）

对确切 EXE 的 `0x03279E40` 再做机器码审核：`0x03279E69` 的 `JE 0x03279EBA` 选择 B 类型；走 A 分支则在 `0x03279EB3` `CALL 0x030D554C` 逐成员发包后，`0x03279EB8` **无条件 `JMP 0x03279EDD` 跳过 B 工厂**；B 分支才在 `0x03279ED8 CALL 0x03263AB0` 构造 `0x03AE0128` B 任务。这是不同的单次调用控制流，**不能将 B 路线节点 `node+0x70` 直接接成该次 A `record[i]` 输入**；如果确实存在跨 Tick/缓存跨模式关联，必须另有真实消费者对象与实例证据。新原始 EXE 实测计数 **170/170 opcode+objdump、23/23 E8、5/5 JCC、1/1 A→B 排除跳转、3/3 RIP vtable、3/3 typed methods**，本地 **19/19** 单元测试 PASS。仍无可授权 Native gameplay 补丁。
