# BSC R97 — shortTask 构造/回调的路段身份与所有权边界（2026-11-20）

**严格按成功标准：** `SEARCH_CANDIDATE=false`、`ROOT_CAUSE_PROVEN=false`、`GAMEPLAY_FIX_PROVEN=false`。本轮是匹配原始 `Warhammer3.exe` 的只读原生数据流研究，尚未证明某次玩家 Shift 挤压的具体因果或可安全 Hook。

## 1. 原 EXE / 源证据

EXE 232531920 字节；SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`；PE x64 / ImageBase `0x140000000`。RVA 下述；完整本地 R97 ZIP 有 11 段机器码反汇编、522 条冻结完整字节与 LLVM 真指令起点、16 个 E8、5 个任务虚表槽位、25 个语义锚点、审计器及日志；匹配原 EXE 21/21 unittest，通过；公共模式 19 PASS/2 SKIP。

## 2. 任务构造尾调用并非调度执行

`0x0302B188/18C/195` 从 MOVE slot+0x18 取得 arena，以 0xA8 大小调用 `0x02F34FD8` 分配对象。分配器更新 arena+0x240 块计数、+0x244/+0x248 空间记账，这些不是已证明的 Shift route generation。`0x0302B1B3` 构造 shortTask，末尾 `0x0302B1E2` 跳转到任务虚表+0x08。

现版 shortTask vtable `0x03AC1310`：+0x00=`0x02F36E84`；**+0x08=`0x008D3C60`（C2 00 00 = RET）**；+0x10=`0x02F5B1E4`；+0x18 同样 `0x008D3C60`；+0x20=`0x02F5D560`。故构造尾调用不是运行任务的调度器。原 EXE 的可执行 PE sections 中未发现 E8 rel32 直接到 `0x02F5B1E4`；此负结论**不排除虚表间接调用**。具体 scheduler 执行者/线程/对象 pin 尚未类型化。

## 3. 构造期和回调期在不同时间读取 Group

`0x02F31778` 构造器拷贝 descriptor+0x4D 到 task+0x7D，descriptor+0x50 指针到 task+0x80。若 task+0x7D 为零，`0x02F31866→0x02F54510` 在构造阶段经 task+0x08 Root 读取当时 Root+0x32F8 Group（`0x02F54542`、`0x02F54621`）并条件性进入 B 路线分发 `0x0327ED4C`。非零时 `0x02F31803→0x02F53FDC`，需要时再经 `0x02F3185F→0x02F4666C` 保存状态。上述是互斥受条件路径，不是每次构造都执行。

后续回调 `0x02F5B1E4` 在特定门槛下 `0x02F5B3F0` 取 task+0x08 Root，`0x02F5B3F9` **再次**取其 Root+0x32F8 Group，`0x02F5B400→0x0327ECA4` 分发 A/B。两次取得的 Group 尚无 engine-owned generation/生命周期等价证明。R94 的 Group 对象池 ABA 风险仍有效，不能把指针值相同认作同一 incarnation。

## 4. 关键别名：task+0x80 并非冻结状态值

`0x0302AEDB` 保存 `&MOVE_slot+0xA0`；复制到 descriptor+0x50 后由 `0x02F318EB/EF` 保存为 task+0x80。`0x02F53FDC` 先读这个字段地址；若非零，再读该地址**当前**的值；字段地址为 NULL 才使用 task+0x98 fallback。若地址有效但值为 NULL，不会转 fallback。`0x02F4666C` 也按 task+0x80 是否为 NULL 区分写到 `*[task+0x80]` 还是 task+0x98。此链说明任务身份可能依赖可变别名，但**没有证明真实 Shift 发生 slot 错代**。

具体析构入口 `0x02F34A24` 在门槛成立时还读取当时 Root+0x32F8，并处理 task+0x98、+0x90 引用计数；仍不能证明外层 scheduler 排他和 Group pin。

## 5. 止损 / 下一唯一验收

`S1_TASK_CONSTRUCTION_AND_ALIAS=STATIC_PROVEN`；`S1_TYPED_CALLBACK_SCHEDULER=NOT_PROVEN`；`S1_SAFE_LIVE_SNAPSHOT=BLOCKED`；`SHIFT_ROUTE_GENERATION=UNKNOWN`。不得安装 Hook、在后台轮询临时 Group、盲改 append/route/物理积分。

下一阶段仅尝试定位**一处有类型的 task vtable+0x10 调度调用者**，需要从具体任务数组/arena 到该 shortTask 实例闭合来源，证明执行期间的线程、对象生存期和 route/slot 代际；只找到 `FF 50 10` 指令不算成功。若查不到则停止无界调度器搜索，回到可验证的首个运动分歧假说。两次用户实机机会限制不变。