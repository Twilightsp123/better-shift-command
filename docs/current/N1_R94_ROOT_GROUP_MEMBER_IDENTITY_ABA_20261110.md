# BSC R94 — 同一 Root / Group / member 结构身份与对象池复用风险（2026-11-10）

## 0. 三项成功判据与真实状态

- **SEARCH_CANDIDATE = false**：没有找到参与实际 Shift 折返并解释首个成员运动分歧的具体原生决策点。
- **ROOT_CAUSE_PROVEN = false**：没有同一 Shift task / route generation 的成员动态轨迹和因果反事实。
- **GAMEPLAY_FIX_PROVEN = false**：没有原生修复补丁与游戏内对照验证。

本轮属于 R92–R93 指定的 S1 工作：**S1 静态结构身份链已完成；S1 可安全运行期采样尚未达标。** 这是有明确边界的进展，不意味着挤压已解决。

输入 EXE：用户原始 `Warhammer3.exe`，232531920 字节；SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`；PE AMD64、ImageBase `0x140000000`。下文地址均为 RVA。只读静态分析，未读取游戏进程、未 Hook、未修改游戏文件。

## 1. 静态来源链现在具备双向验证点

当前版本 `0x030209EC`（RCX = Root）是一个受既定调用者条件约束的 Group 重建路径。原始代码证明：

1. `0x030209FB` 取 `&Root+0x3280`，`0x03020A0A` 调 `0x0301E8B0` 清理该根对象维护的旧 Group 列表。
2. `0x03020A17` 传入当前 Root；`0x03020A27` 调 `0x0302093C` 创建新 Group。
3. `0x0302093C` 读取所属上下文 `+0x440 → +0x150 → +0x58` 的回收链表，弹出一个对象节点；`0x030209BF` 调 `0x030C7CB8` 对节点重新构造。
4. `0x030C7CD2/D6 → 0x030C7DBC` 以 `Root+0x30` 为描述符，令 Group `+0x08/+0x10` 来自 `[Root+0x38]`；`0x030C7CF9` 明确把 Root 写入 **`Group+0xA10`**。
5. `0x030C7DBC` 初始化 `Group+0x20/+0x28`，当前具体 Group vtable `0x03914450` 的 `+0x00` 等于 `0x030CC50C`。
6. `0x03020A2C/36` 读取 Root **`+0x188` 成员指针数组和 `+0x184` 数量**，循环将每个成员传入 `0x030E54EC`。
7. `0x030E554E` 末尾跳往 `0x030CC4AC`：后者使用 `0x01325DA4` 追加到 Group `+0x20` 开始的成员向量。该容器 `+0x20` 为容量 DWORD、**`+0x24` 为数量 DWORD、`+0x28` 为成员指针数组**；`0x01325E2C` 增加数量。
8. 紧接着 `0x030CC508` 通过 Group vtable `+0x00` 调到 `0x030CC50C`；`0x030CC512` 将 Group 指针写入 **`member+0x300`**。
9. Group 成员处理和 `0x030D7130` 后处理执行之后，才在 `0x03020A75` 写 **`Root+0x32F8 = Group`**。`0x030DA51C` 的阵型 fanout 再使用 Group `+0x24/+0x28` 按成员索引发包。

因此，**在这条构造/发布路径之内**，可建立以下可核对的指针关系：

```
Root R:
    [R+0x32F8] = Group G
    [R+0x184]  = root_member_count
    [R+0x188]  = root_member_ptr_array
    [R+0x38]   = context C

Group G:
    [G+0xA10] = R
    [G+0x10]  = C  (特定构造路径)
    [G+0x24]  = group_member_count
    [G+0x28]  = group_member_ptr_array

Member M in G's member array:
    [M+0x300] = G  (通过 Group vtable+0x00 赋值)
    [M+0x58]  = C  (此前 R82 证明的特定成员构造路径)
```

同一实例的上下文 C 与 Group/member 的双向身份相符，是 **S1 结构一致性判据**，不能当作真实 Shift 路段身份或线程安全证明。

## 2. 本轮重要负证据：对象池 ABA 风险和失效边界

### 2.1 旧 Group 先回收，新 Group 后发布

`0x0301E8B0` 处理 `Root+0x3280` 内旧 Group 引用容器，逐个调用 `0x030313D8`。后者先调用对象 vtable `+0x10` 进行回收清理，随后把旧节点链入上下文管理的空闲链表。新 Group 构造函数 `0x0302093C` 使用的正是这类上下文池节点。

**`0x030209EC` 函数自身在旧 Group 清理前没有直接把 `Root+0x32F8` 清零，只有构造与后处理完成后的 `0x03020A75` 发布写入。** 该函数的独立直接指令无另一个 `+0x32F8` 存储；其他调用者/间接副作用及外部同步尚未全部排除。

这意味着一个异步只读观测器如果只采用 `Root.group` 的“读取前后同一指针”验证，可能被地址复用欺骗。即使两次采样看似结构一致，也不能证明它们属于同一个生存期的 Group（ABA 问题）。

### 2.2 成员的 Group 反向指针有**条件性**清除

Group 对象具体虚表 `0x03914450` 的 `+0x10 → 0x030CB250 → 0x030C97C4 → 0x030C9820`，在相关销毁分支中：

- `0x030C9837/3B` 取得 `Group+0x10` 的上下文 C 与 `C+0x440`。
- `0x030C9842/49` 检查该控制对象 `+0x94`；**不为 0 则跳过本次遍历清除**。
- 允许遍历时，`0x030C984B/4F` 取得 `Group+0x28` 和 `Group+0x24`，逐个成员在 `0x030C985B` 清除 **`member+0x300`**。
- `0x030C98AC/B5` 释放原成员指针数组。

因此：不能把旧成员 `member+0x300` 非空自动视作当前有效 Group，也不能只检查 `Group+0xA10` 相等就授权跨帧读取。**条件性跳过**不是说必然留下悬垂指针；只是这条销毁路径没有无条件证明它会被清除。

### 2.3 反例验证

离线构造两套记录：在第一代 Group `G` 含成员 M1/M2 时，一套样本完全自洽；旧 Group 回收后同地址 `G` 再次用于 M3/M4，另一套样本也完全自洽。两套样本 `Root.group == G`、`G.root == Root`、每个成员反向指针一致，但仍不是同一代 Group。`tools/r94_identity_contract.py` 的 `inspect_pair()` 明确返回 `ABA_OR_INTERLEAVING_NOT_EXCLUDED`，不得误判为连续身份。

这只是指针生存期逻辑反例，不是宣称实机一定发生了复用冲突，更不是玩家 Shift 挤压的原因。

## 3. S1 可验收和不能验收的内容

**通过：** 该版本原版 EXE 的 Root/Group/member 结构字段、成员向量真实追加来源、Group vtable 赋值的成员反向指针、Group 回收和发布之间的代码级先后次序、条件性反向指针清除分支。

**未通过：** 从原生 Shift 任务获取可信 Root 的实际运行期入口；跨 Tick / 线程的锁、同步点或不会被复用的 generation/epoch；没有中断于销毁或重建中间阶段的安全只读快照机制；同一游戏 Shift 路段身份。没有通过这些检查之前，**不准以独立后台轮询的方式读取成员指针，尤其不能为了追踪而占用 Derpy 使用的成员 Tick Hook。**

**观测器的暂定 fail-closed 协议**：先由经验证的游戏所属线程/稳定阶段产生具有生存期证明的一份聚合记录，然后在离线做 `Root.group↔Group.root↔member.group`、成员数组/数量、Group/member context 一致性、任务 route identity、时间和 world goal 对齐检查。当前只实现记录校验器，没有尝试获取进程内数据。即使记录自洽，校验器也只标记 *结构一致*，**不会**标记为 *可安全异步读取*。

## 4. 原始 EXE 核验与交付

- 精确 SHA/PE/ImageBase、**85/85** 完整指令原始字节及 LLVM 指令起点；**9/9** E8、**2/2** E9、**2/2** 精确 Group vtable 项；**15** 个不同 PE unwind 函数范围，6 个无 unwind 机器码 pin。
- 公共无 EXE：**14 PASS、1 SKIP**；匹配原始 EXE：**15 PASS**。测试包括八类错误成员/Group 组合、A/B 地址复用反例、错误 EXE/hash/manifest fail-closed。
- 本地研究包包含：中文报告、完整 85 pin manifest、16 段原始反汇编、审计器、离线结构校验器、测试结果、SHA256 清单、完整 R93 历史 ZIP；不含商业游戏 EXE。
- GitHub 研究分支文档与公共契约测试另行记录；`main` 禁止变更。

## 5. 下一轮只做一项关键事情

**R95：先证明某个真实的游戏线程/原生调用点可以在 Group 发布后且未开始回收时安全产出一个完整快照，并能绑定原生 Shift task/route generation。** 如果做不到，先只完成 S2 的 world-goal 数据转换静态验证，**不向用户发起任何实机测试**，也不通过异步悬垂指针轮询伪造同一实例。

`S1_STATIC_STRUCTURE = PASS`；`S1_LIFETIME_SYNCHRONIZATION = NOT_PROVEN`；`S1_QUEUED_SHIFT_INSTANCE = UNKNOWN`；`S2_WORLD_GOAL = PENDING`；`SEARCH_CANDIDATE=false`；`ROOT_CAUSE_PROVEN=false`；`GAMEPLAY_FIX_PROVEN=false`。