# BSC R80 — 成员本地导航候选选择及与原生 Shift 路段身份断点（2026-10-27）

**只读原始 WH3 EXE 静态分析；没有新游戏 Hook、战斗实机日志或 playable 修复。** 本项目缺陷是同一兵牌成员群体运动穿插、挤压，不存在一个专门的“挤压动作”。Win64 用户 EXE SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`，232531920 字节，ImageBase `0x140000000`，下列所有数值为 RVA。

## 一、已核对同一 member 的输入与导航暂存链
- `0x03072F1A E8→0x03076F64` 一条条件性成员调用。成员本地函数 `0x03076F7E LEA RDI,[member+0x718]` 保留当前成员的子控制器，`0x030771EC LEA R9,[member+0x910]` 提供同一个成员的关联输入记录，`0x03077221 LEA RDX,[rsp+0x40]` 提供临时目标输出，`0x03077212` 另给辅助输出。
- `0x0307722B E8→0x0311F34C` 使用 `RCX=member+0x718` **子控制器而非 member 本体/UnitRoot**。返回后 `0x03077243/4B` 把其结果复制至同成员 `+0x838` 目标暂存；原生额外状态满足时可进一步 `0x0307741D→0x0311E5DC` 存到 `+0x1E0/+0x1F0`（R79），并非每次必定提交。

## 二、实际三路候选来源：0x03132178
`0x0311F34C` 在入口保留 `RDI=RCX(子控制器)`、`RSI=RDX(输出)`、`RBX=R9(关联记录)`。可见输入表达式为：

```text
member controller = member+0x718
manager = [[[controller+0x08]+0x440]+0x160]
candidate reference = [[member+0x910]+0x10]
selector integer = [[controller+0x20]+0xA0]
0x0311F417 E8 -> 0x03132178(manager, local_position, candidate_reference, selector_integer)
```

`0x03132178` 精确字节/真实指令起点及分支核验：
1. 参数值整数 `3` **且** `manager+0x10` 非 NULL 时返回 `[[manager+0x10]+0x108]`；值 `3` **并非已证的阵型 Mode3**，更不是 Shift route leg。
2. 其它情况下，若输入 `R8` 非 NULL 且 `[R8+0x80]` 非 NULL，则返回该局部关联引用的 `+0x80` 字段值。
3. 否则使用 `[[manager+0x00]+0x440]+0x168` 处理器，通过 `0x031321BC E8→0x02F8FBD8` 执行后备查询；该后备目标的高层 MOVE 身份仍为 UNKNOWN。

## 三、同一成员子控制器自身的候选链表和选择副作用
候选函数返回值 `R14=RAX`；`0x0311F41C` 读取 `[controller+0x28]` (对应 member+0x740)，接着 `0x0311F436/43A` 读取每个 `node+0x10→payload+0x28`，`0x0311F43E CMP R14,RAX` 作**具体引用身份比较**。匹配时 `0x0311F53F` 直接更新 controller+0x28；不匹配时还可沿 `node+0x08` 遍历，并以候选方位与局部位移的查表投影正负进行条件前进（`0x0311F4C2/4C6`、`0x0311F522/526`）。`0x0311F530` 可能更新当前 cursor，`0x0311F54F` 保存 `controller+0x30` 的当前选中节点。由此证明的只是**成员局部候选选择/链表状态**，不证明具体成员正在切换原生 Shift 队列路段。

**静态交点的重要止损：** 此处取 manager 的路径 `[[member+0x720]+0x440]+0x160` 与历史高层 MOVE 链 `[[UnitRoot+0x38]+0x440]+0x160` 看起来同形，但两者的 context 指针**没有证明为同一个对象或同一任务代际**。不能因为字段偏移一致就强行串到 Shift。

## 离线证据及结论
私有准确 SHA 的 EXE 上：**98/98 完整原码、llvm-objdump 真实起点、8/8 E8、10/10 Jcc、5/5 PE UNWIND；37/37 本地测试**（包括 EXE + 指令起点校验）。完整 R80 ZIP 附所有原码记录、五段受限汇编、工具、测试日志、R79 历史包，不含商业 EXE。GitHub 本次公开精简版发布 **58/98 机器码、6/8 E8、3/10 Jcc、5/5 PE 所有者**和可运行 synthetic/负例测试，且公共 CI 的商业 EXE 用例应 SKIP。

**R81 优先：**只在有界范围内找 `member+0x910` 输入及 `[controller+0x20]+0xA0` 模式参数的具体构造/写者及其与 queued MOVE 的身份关联。若没有确切相同 task/route generation，就保留 UNKNOWN，不强制所有成员选择同一候选，不修改 Steering 或目标段索引。

`native_gameplay_patch_authorized=false`, `live_hook_authorized=false`, `root_cause_proven=false`, `main_unchanged=true`.
