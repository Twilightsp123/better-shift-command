# BSC N1 — 2026-10-14 原生 MOVE 的 UnitRoot→Group→成员目标双入口（精确 9.0.3 EXE）

## 本轮实证与版本

使用用户已提供的原始 `Warhammer3.exe`，SHA256 **`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`**，PE ImageBase `0x140000000`。新增只读原码审计：**98/98 opcode 和 GNU objdump 真实指令起点、15/15 E8、2/2 类型化虚方法表指针、3/3 RIP-relative 虚表安装、原生类型叶函数结尾及 1/1 直接跳转门槛均 PASS**。本地回归 **10/10 PASS**，包含真实原始 EXE 检查。没有游戏进程、Hook、内存写入、DLL/PACK，故证据等级为 `EXACT_ORIGINAL_EXE_STATIC`。

## 一、真正构造出了两个指向 UnitRoot 的 group 字段

```text
0x0302DB44 (UnitRoot MOVE route updater)
  → 0x0301B8E4 构建 group
       0x0301B90F R8 = UnitRoot
       0x0301B91F E8 → 0x0301B834
          0x0301B84A 保存 R8 到 ctor 参数+0x08
          0x0301B8B7 E8 → 0x030C2C3C
            0x030C2C56 读 ctor 参数+0x08 = UnitRoot
            0x030C2C5A 形成 UnitRoot+0x30
            0x030C2C61 E8 → 0x030C2D40（无 unwind 的已定界叶函数）
              0x030C2D40/48 读 [UnitRoot+0x38]
              0x030C2D44/4E 写 group+0x08 和 group+0x10
            0x030C2C7D 写 group+0xA10 = UnitRoot
       0x0301B96D 写 UnitRoot+0x32F8 = group
```

其中 0x0301B834 的 ctor 参数寄存器传播并非按临近字段猜测：函数入口 `RAX=RSP`，`push rdi; sub rsp,0x40`，`[entry_rsp-0x20]` 正好是 `[rsp_after_prologue+0x20]+0x08`，随后传给 `0x030C2C3C`。

**已确认的静态结构**：`group+0xA10 = UnitRoot`；`group+0x10 = [UnitRoot+0x38]`（**指针值**，不是 `UnitRoot+0x38` 这个地址本身）。群组对象与其持有的上下文指针必须区别对待。这是当前跨函数的真正**字段来源证明**，而非从两个结构“都有 +0x160”推断同一对象。

## 二、原生 MOVE 建立的 `UnitRoot+0x270` 在后继任务中被再次消费

### 发令阶段的即时目标下发

`0x0302DB44` 先通过 `0x0302DB8E → 0x0301B8E4` 构建 group。随后 `0x0302DBC4 → 0x0301287C` 配置路线。在已检查的条件路径下，路线描述符有两种物理形式：

- 堆/外部描述符：`0x03012982 → 0x03008894` 构造，`0x03012987` 将结果写入 `UnitRoot+0x270`；
- 内嵌目标描述符：`0x030129E5` 把 `UnitRoot+0x1E8` 的内嵌对象指针写入 **同一个** `UnitRoot+0x270`。

随后 `0x0302DBC9/D3/D7` 从 `UnitRoot+0x270 → [route+0x18] → [child+0x70]` 提取传给 `0x0302DBDB → 0x030D5490` 的几何输入。**不能假定这个函数在所有条件下都新建描述符或给每个成员赋同一目标。**

### 任务回调阶段的条件性二次下发

`0x03025D70` 是 MOVE 槽位 `vtable 0x0390B4F0 + 0x08` 的原生处理函数。`0x0302609B/A8` 由 `slot+0x10` 的包装对象得到 UnitRoot，`0x030260AF → 0x02F2C734` 构造一个**短期任务对象**，在 `0x02F2C74D` 保存 `shortTask+0x08 = UnitRoot`，安装 `vtable 0x03ABBE18`。该虚表 `+0x10 → 0x02F561E8`。

在 `0x02F561E8` 的**状态条件成立**后，`0x02F563F4/FD` 顺着 `shortTask+0x08 → UnitRoot+0x32F8` 得到上面构造的 group；`0x02F56404` 直接调用 `0x03279E40`。

`0x03279E40`：

- 先按 `group+0x10 → [+0x440] → [+0x150]` 检查 `0x02DC2E04` 模式门槛。`0x03279E69 JE 0x03279EBA` 表明此条件失败会跳过 `0x030D554C` 的 A 族目标分发。
- 对部分任务参数未提供有效朝向/缩放值的情况，通过 `group+0xA10 → UnitRoot+0x270` 再读取此前配置的 `route+0x44` 朝向码及 `route+0x40` 标量。
- 只有该原生条件路径成立，才在 `0x03279EB3` 调用 `0x030D554C`，并进一步于 `0x030D5603` 调用 **相同的**成员发包函数 `0x030D5490`。此处不能称为每段 Shift 必运行两次发包。

## 三、路线创建与条件性群组发包共有一条具体上下文字段来源

原生路线描述符构造器 `0x03008894`：

```text
UnitRoot+0x38 [load] → context+0x440 [load] → routeContext+0x160 [load]
  → 0x031219B0 → 将返回值保存到 routeDescriptor+0x18
```

原生群组目标适配 `0x030D554C`：

```text
group+0x10 [load] = [UnitRoot+0x38]
  → context+0x440 [load] → routeContext+0x160 [load]
  → 指针再 +0x18 → 0x030FDA9C
  → 0x030D5490
```

**两条路径访问的字段来源表达式相同**：`[[[UnitRoot+0x38]+0x440]+0x160]`，但它们各自使用不同的转换函数，输出对象/目标值不能强行判为完全一致或完全不同；同时，并没有特定玩家 Shift 实例的指针配对，所以不能称其在某次指令中一定指向相同运行时对象。

关键负证据：**`routeContext+0x160` 与继承式 MOVE 大任务的 `bigTask+0x160` 仍没有已证实的指针别名关系**；也不能把新确认的短期任务 `shortTask+0x08` 与队列槽位 `MOVE slot+0xA0` 中有条件复用的“大任务”混为同一对象。

## 四、对真正 Native 挤压修复的影响

新增证明的是真实程序中**两套几何输入准备路径、一个共有群组及同一成员发包点**。结合前轮已证明的 `member[i] → record[i]` 配对，以及 packet 朝向/位置二次修正，现在可具体检查：

1. 同一 `UnitRoot` 的一次**继承式 MOVE state=1** 是否使两个发包入口引用不同的 route generation；
2. 如果生成的 `record[i]` 与成员身份顺序不匹配，错位发生在 group strategy 生成、群组成员序列变更，还是后续个人位置/方向修正；
3. 最终 motor goal 的交叉是否来自记录错配、局部动作生命周期差异或合法 CA 避障，而非仅从端点直线相交得出结论。

这些 **目前还没有同一 Shift MOVE 实例因果闭合**。不可直接清空 `task+0x158`，也不可禁用渐进投影、修改 `record+0x22`、统一成员朝向或强行重排阵型索引。没有授权 Native gameplay patch，不要求玩家重测已确认挤压。

## 五、交付与运行

源码 `maintenance_tools/native_shift_re/audit_move_group_common_context.py`，回归 `tests/test_native_shift_re_move_group_common_context.py`，脱敏静态证据 `maintenance_tools/native_shift_re/evidence/20261014_move_group_common_context_static.json`。可重复只读验证：

```powershell
python maintenance_tools/native_shift_re/audit_move_group_common_context.py --exe "C:\path\Warhammer3.exe" --out ".\N1_outputs\move_group_context.json"
```

本轮没有修改原始 EXE、DLL、PACK 或 `main`；不会上传私有原始游戏文件或 Frida 指针日志。


## 2026-10-14 原生短期 MOVE Group 当前指针晚绑定与对象池重用（最新严格负/正证据）

新增 `audit_move_group_generation_latebind.py` 和同名前缀回归，固定 SHA 原始 EXE 通过 **91/91 opcode/unwind/objdump、19/19 E8、3/3 类型虚表**，13/13 本地测试 PASS。`0x0301B8E4` 每次路线重建先通过 `0x030197A8 → 0x0302C2D4` 把旧 group 送回 `context+0x150+0x58` 对象池，虚表 `0x0390F5F0+0x10=0x030C61D4` 的回收析构以 edx=0 跳过释放对象本体，再由 `0x0301B834 → 0x030C2C3C` 重新使用并写 `root+0x32F8`。短期任务 `0x02F2C734` 保存 `task+0x08=UnitRoot`，状态回调 `0x02F561E8` 到分发点才在 `0x02F563F4/FD` 读取**当前** `root+0x32F8`，把与短任务关联的临时参数交给 `0x03279E40`。后续清理检查 `0x02F5652D/7B` 在调用之后且受状态门槛限制。**指针相等并不保证 group 同代，可能发生对象池 ABA**，离线已给出有/无回收、任务已清退的对照反例。仍未证明真实 Shift 存在“旧 shortTask 在新 group 重建后继续进入回调”的时序，不能认定 Shift 挤压根因，不得改 EXE / Native gameplay。详见 `docs/current/N1_903_MOVE_GROUP_GENERATION_LATEBIND_20261014.md`。


## 2026-10-14 — 大任务推进、路线描述符与成员发包共用原生几何管理器（新类型化审计）

新脚本 `maintenance_tools/native_shift_re/audit_shared_move_geometry_manager.py` 直接在固定 SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` 原始 EXE 上通过 **81/81 机器码+unwind/objdump指令起点、12/12 E8 直接调用、2/2 typed vtable**；本地 **13/13 单元测试 PASS（含真正 EXE 校验）**。中文独立报告：`docs/current/N1_903_SHARED_MOVE_GEOMETRY_MANAGER_20261014.md`。

经原始 ctx+0x440→routeContext+0x160 字段来源确认的 **manager** 同时支持三路调用 `0x030FDA9C(manager+0x18)`：路线描述符构造 `0x03121A99`，管理器路线节点生成 `0x03129092`，group目标适配/成员发包 `0x030D55F5`。关联上游 `0x02DD5A2C→0x02DD579C→0x03128E80` 读取该 manager，遍历 manager+0x1F0 的 bigTask 并通过 `0x0311DE74` 推进任务；此前证明的继承式 state=1 投影仍只在原生门槛成功时执行。转换器的某些分支写 `converter+0x1D0 = manager+0x1E8` 计数/状态字段，**未证明它是 generation ID**。这属于强于“函数复用”的静态管理器身份链，但 **manager+0x160 与 bigTask+0x160 不是已证实的指针同一性**；输出分别落在不同路线对象，不能宣称发生了目标代际错配或 Shift 物理挤压。正常成功 MOVE→MOVE 交接清退旧 shortTask 的反证继续有效。未授权 native gameplay patch，不修改 main/原始 EXE/含指针日志，不要求用户重复实机折返。
