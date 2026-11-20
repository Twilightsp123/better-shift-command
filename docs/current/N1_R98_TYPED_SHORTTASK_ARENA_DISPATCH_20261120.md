# BSC R98 — 有类型 Root/shortTask arena 调度器与执行清退边界（2026-11-20）

**新成果：R97 的 `TYPED_SCHEDULER=NOT_PROVEN` 在静态层面已闭合。** 本轮不是增加虚调用猜测，而是通过 Root 构造、原生 MOVE 队列项、slot 构造、任务分配登记和 Root 更新指针，证明同一 arena 的读写及特定 shortTask `vtable+0x10` 调用者 `0x03048624`。完全静态只读，无 Hook/实机/游戏修复。

原始 `Warhammer3.exe`：232531920 bytes，SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`，AMD64，ImageBase `0x140000000`；以下均为 RVA。

## 1. 从 Root 到实际任务容器的有类型来源

1. Root 构造函数 `0x0300C998` 用 R15 保存原始 Root，`0x0300CB85 LEA RAX,[R15+0x2FA0]`，随后 `0x0300CC16 MOV [R15+0x280],RAX`。因此在该构造路径中 `Root+0x280 = &Root+0x2FA0`。
2. queued MOVE 入口将 `&Root+0x278` 交给 `0x02F5540C`；`0x02F55465..7B` 使用索引计算队列项 `QueueEntry=Root+0x288+index*0x120`，`0x02F5548F MOV [RCX+0x10],RAX` 把 `[Root+0x280]` 放进 QueueEntry+0x10。
3. MOVE slot ctor `0x0300E170→0x0300D8C8` 在 `0x0300D901/905` 从 QueueEntry+0x10 复制到 `MOVE_slot+0x18`。于是该合法构造路径内的 slot arena 指向 `&Root+0x2FA0`。
4. `0x0302B188` 从 MOVE_slot+0x18 读取 arena，`0x0302B195→0x02F34FD8` 分配 `0xA8` 字节 shortTask，`0x0302B1B3→0x02F31778` 构造具体任务。分配器 `0x02F35013` 将 `(task_ptr,size)` 16B 登记到 `arena+0x200+index*0x10`，`arena+0x240` 为记录数量。
5. Root 更新 `0x0304874C` 在 `0x03048879 LEA RCX,[RBX+0x2FA0]`，`0x03048880 E8→0x03048624` 直接调用任务调度器。同一个 Root 内嵌 arena 在原生 slot 创建及更新调度路径两侧完全对应。`0x02DDBFF4/FF7` 也展示了上游持有的 Root 指针通过直接 E8 进入 `0x0304874C`，但不构成工作线程保证。

## 2. 真正调用 callback 的调度器

`0x03048624` 在 `0x03048644` 读取 arena+0x240 数量，在 `0x03048667..70` 算出 16B 记录位置并取出任务指针，在 `0x0304867A` 读取任务 vptr。`0x0304867D/7F` 比较本轮 index 与读到的 count-1，最后记录走 `0x03048681 CALL [RDX+0x10]`，其余记录走 `0x030486A2 CALL [RDX+0x18]`。

具体 shortTask 构造器 `0x02F317BB/C2` 安装 vtable `0x03AC1310`：`+0x10 → 0x02F5B1E4`（真正 callback）；`+0x18 → 0x008D3C60`（原码 `C2 00 00`，RET）。因此本调度路径中，**处于当前记录栈尾的这个具体 shortTask 才执行该主要回调，靠前的同类任务在 +0x18 槽无动作**。其它任务类型可能有非空的 +0x18；callback 可以改变 arena 状态，不能把这条控制流草率解释为所有 Shift 任务每 Tick 的固定全局排序。

## 3. 执行完成之后的清退边界

`0x03048681` 返回后，`0x03048684 INC [task+0x1C]`，`0x03048687 CMP [task+0x18],1`。满足条件时 `0x03048692 E8→0x02F54D58`，该函数处理 arena 尾部回收记录并在 `0x02F54DAA` 调用相应任务 vtable+0x00 进行清理。调度器另一分支还在 `0x030486ED` 调用虚表+0x00。具体回调末尾 `0x02F5B5C3 MOV [task+0x18],AL`，提供条件性终止标志写入来源。

以上证明**该直接调用栈中的回调→状态检查→有条件清退的顺序**，不证明其它线程不会干预。arena+0x250/+0x251/+0x254 在这段代码里用于流程门槛和计数，不能直接解释成 OS 锁、对象 pin 或 queued MOVE 路段 generation。R94 的 Group 对象池 ABA 风险及 R97 的 task+0x80 可变 slot 状态别名仍然有效。

## 4. 本轮验收及止损

本地原始 EXE 静态复核：15 个有界代码范围，**326/326 完整 opcode 与 LLVM 真指令起点，9/9 E8，5/5 具体任务虚表槽，27/27 语义锚点，12 个不同 PE unwind 所属函数范围**。真实 EXE 20/20 unittest PASS，公共无 EXE 17 PASS/3 SKIP。合成负对照覆盖任务栈尾调用、清退与下一任务进展、同地址跨代和 Group ABA；它们都不是游戏内捕获。完整原码与测试在 R98 ZIP，含 R97 完整历史 ZIP；不包含商业游戏 EXE。

`R98_TYPED_SCHEDULER_STATIC=PASS`、`R98_ARENA_IDENTITY_STATIC=PASS`、`R98_CALLBACK_CLEANUP_ORDER_STATIC=PASS`；**`THREAD_EXCLUSIVITY=NOT_PROVEN`、`GROUP_LIFETIME_PIN=NOT_PROVEN`、`ACTUAL_SHIFT_ROUTE_GENERATION=NOT_PROVEN`**。依照先前 BSC 强制成功标准，`SEARCH_CANDIDATE=false`、`ROOT_CAUSE_PROVEN=false`、`GAMEPLAY_FIX_PROVEN=false`。

**下一项唯一验收**：从已类型化的 Root 更新 `0x0304874C` 外层确认真正工作线程/排他阶段和 Group 生命周期保证，并确定可跨 slot→task→回调关联的原生路线代际；不能满足就不装 Hook、不要求玩家实机，不重新搜索已经确认的 `vtable+0x10` 调用者。禁止 Lua 重发 MOVE、全局改运动积分或 Shift 队列。