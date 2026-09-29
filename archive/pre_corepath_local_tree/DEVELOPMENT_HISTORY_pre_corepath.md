# Better Shift Command — 开发与维护总记录

这份文档是 **v1.2.1 之后的长期工程记录**。它取代过去散落在根目录和 `docs/` 中的 R3/R4、SC1～SC6、诊断、BuildOnly、Package Check、Smoke Test 等阶段文档。

目标不是保存每一次实验输出，而是保存真正需要长期继承的内容：

- 当前架构为什么这样设计；
- 哪些结论已经被 WH3 实机证据证明；
- 哪些方案试过并被否定；
- SC1～SC6 每一刀到底解决了什么；
- 后续维护绝对不能随便破坏哪些不变量。

---

## 1. 当前正式基线

- **Release:** Better Shift Command `v1.2.1`
- **Controller:** `1.2.1`
- **Run ID:** `V1_2_1`
- **Build marker:** `BETTER_SHIFT_COMMAND_V1.2.1`
- **Native Bridge ABI:** `1.0.15-r4-evidence-v3-validated-userdata-root`
- **Platform:** Windows x64


v1.2.1 在 v1.2.0 的 SC1～SC5 行为基线上增加 **SC6 V3 Execution Identity Reconciliation**：当 CA Native active order 提前跳到 future canonical action 时，控制器使用 V3 exact execution identity 决定 adopt / rollback，并要求 SC5 physical recovery 只在当前 Exit MOVE 仍是 exact Native active execution 时运行。Native ABI 字符串继续保持 `1.0.15-r4-evidence-v3-validated-userdata-root`；旧 V2 evidence reader 导出仅保留兼容名称并 fail closed。

v1.2.0 的行为基线就是最后验证通过的 **SC5 EXIT REASSERT**。正式版收尾没有再改路线算法、接战算法或 Native 行为，只做了：

1. 正式版本身份统一；
2. 默认关闭高频 telemetry；
3. 让关闭 telemetry 后连昂贵的字符串拼接/格式化也尽量不发生；
4. 关闭只为测试存在的 generation/cancel observation；
5. 保留真正异常、拒绝和恢复类的稀疏日志。

因此 v1.2.0 **没有为了版本号好看而修改 Native ABI**。

---

## 2. 当前架构必须保持的职责边界

### 2.1 Lua Controller

Lua Controller 负责的是**命令语义和队列状态机**：

- 捕获玩家 Move / Attack；
- 建立 action / block；
- 判断 waypoint 是否可以 handoff；
- 跟踪 route debt；
- 管理 Attack hold、Exit route 和 recovery budget；
- 调度后续 Move/Attack。

它**不替代 WH3 locomotion**。我们只是决定什么时候把当前 active destination 换成下一个，真正的移动、转弯、阵型运动仍由 CA 原生 locomotion 执行。

### 2.2 Native Bridge

Windows Native Bridge 负责：

- 观察原生命令；
- 识别我们的命令 ACK；
- 提供 execution identity；
- 提供 EntitySnapshot / ContactPair 等物理证据；
- 向 WH3 提交 Controller 需要的原生 Move/Attack。

正式 Windows 构建使用：

- Visual Studio 2019 Build Tools；
- MSVC v142 x64；
- MASM / `ml64`；
- CMake。

ContactPair 使用专门的 **mid-function hook**，对应 `contact_pair_hook_x64.asm`。这条路径和普通 MinHook 函数入口 hook 不是一回事，因此 Windows Build + CTest 必须继续覆盖 MASM assemble/link 和 mid-function smoke。

### 2.3 Command root ≠ Evidence root

R4 最重要的架构结论之一：

> **命令身份指针不能顺手当作物理证据根。**

两者职责必须分开：

- **Command root**：证明 order / execution identity；
- **Evidence root**：证明 Entity / movement / contact 等物理状态。

过去实机逆向已经证明：一个能处理命令的 root，并不代表它的偏移就符合 Entity container contract。

因此 R4 的 evidence resolver 不再接受“这个地址看起来像指针”作为证明，而是：

1. 从 Lua userdata 生成候选；
2. 候选必须通过完整 EntitySnapshot validation；
3. 0 个有效候选 → fail closed；
4. 多个互相冲突的有效候选 → fail closed；
5. 无效 rebind 不能覆盖已经验证过的有效 root；
6. command lifetime 改变时，旧 physical root / owner generation 必须退休。

### 2.4 ContactPair 才是接触证据；`melee=true` 不是

目标特定的物理接触使用 ContactPair 两端 Entity，再通过 EntityOwnerIndex 映射回 Unit。

这套证据是：

- target-specific；
- sequence-specific；
- generation-specific。

旧 Attack 的 ContactPair 不能拿来证明后一个 Attack。

同时，最终实机已经明确证明：

> `melee=true` 会严重滞后，甚至单位已经跑出几十/上百米、真实 contact 已清零时仍可能保持 true。

所以后续代码**绝对不能**把 `melee=true` 单独当成“单位现在仍被近战黏住”的证据。

---

## 3. R3：第二次 Attack / Exit body cohort

实机失败链曾经是：

```text
Attack A
→ Exit P1
→ Attack A2
→ P2
```

P1 路线已经完成，但第二个 Attack 长期卡在 Exit evidence，因为旧 Evidence V3 要求 P1 的 exact active native order 在 route-complete 以后仍存在。

问题在于：WH3 到达 P1 后自然会退休这个 active order；于是 Controller 失去了后续 body-clear 所需的 cohort 身份。

R3 的修复是 **Frozen ExitBodyCohort**：

1. 只有在 P1 exact MOVE order 仍 live 且身份已证明时才能建立 cohort；
2. freeze 时绑定 generation / block / action / successor target；
3. P1 active order 退休后，只能使用已经冻结的不可变 cohort；
4. frozen evidence 不能反过来给 route-complete 之前的移动放行；
5. A2 仍必须证明自己的 exact Attack identity 和自己的 target-specific ContactPair。

这条规则一直保留到 v1.2.0。

---

## 4. R3.1 / R3.2：Lua 5.1 local 上限

R3 曾在 WH3 Lua 5.1 中直接加载失败：

```text
main function has more than 200 local variables
```

### R3.1

先把新增的顶层 local helper 移入已有 namespace，恢复可加载状态。

### R3.2

随后做结构性修复：

- 建立 `Core` namespace；
- 大量长期 helper 从 `local function xxx` 改为 `Core.xxx` / `R1.xxx`；
- self-contained native bootstrap 包进 closure；
- 主 chunk 长期 local slot 大幅下降。

长期维护规则：

> 新 helper 优先放进 `Core.xxx` / `R1.xxx` 或短 lexical scope，避免继续堆顶层 local。

---

## 5. R4 Evidence V3：验证过的物理证据

R4 实机审计确认：Native Move/Attack issuing 本身不是全局死亡，真正的问题是 Evidence V3 的 physical root 没有被可靠证明。

典型表现是：

- Native 已 authorized / armed；
- Move/Attack dispatch 和 ACK 存在；
- 但 `V3_EXIT_BODY_STATUS` 大量 `ENTITY_STALE`；
- 旧 userdata offset 假设无法稳定形成 EntitySnapshot / EntityOwnerIndex。

R4 因此形成目前的物理证据架构：

- validated userdata evidence-root resolver；
- 完整 EntitySnapshot 验证以后才发布 evidence root；
- ContactPair owner 映射要求当前 EntityOwnerIndex generation；
- missing / ambiguous evidence fail closed；
- lifetime change 清除旧 ownership / physical binding；
- FrozenHandoff 必须建立在已验证 EntitySnapshot 之后。

R4 还把 Controller 与 Native pending lane 从 **4 提高到 32**，消除多单位选择时人为的四个一组 batching ceiling，同时仍保持 per-unit ACK discipline。

Route debt 也从短时间固定 deadline 改为基于实际 progress 的 stall 判定，避免单位明明还在向旧 waypoint 改善却因为时钟到了就被判死。

---

## 6. 被放弃的 RC1 / RC2 convergence 线

曾经尝试过一次大范围 convergence / cleanup：同时删除或修改多个 runtime 模块、hook、packaging/maintenance 路径。

结果是实机 regression 出现以后无法进行可靠单变量归因。

RC2 诊断线还出现：

- `MODEL_TIME_UNAVAILABLE`；
- Battle Manager model time 异常；
- timer manager arithmetic-on-function 错误；
- 后续 UI/script callback 连锁异常。

曾经怀疑 hot-path `out()` 日志污染 model time，但把日志改为独立 sink 后问题仍复现，因此该假设被证伪。

最终结论：

> RC1/RC2 不是长期 baseline。以后行为修改必须尽量单变量，并由实机日志证明因果链。

---

## 7. SC1：Steering Corner

0815 实机证明：纯 Shift Move 路线在 waypoint 仍会明显减速/停顿。

旧架构只有严格的 waypoint/path-safe 语义，会让 WH3 把中间点持续当作 active arrival destination。

SC1 保留 `PATH_SAFE`，新增 `STEERING_CORNER`：

- 根据速度；
- formation width；
- 转角；
- current leg；
- next leg；

计算动态 turn corridor。

当 successor Move ACK 后，rounded waypoint 以 `STEERING_CORNER_HANDOFF` 完成，并且不创建 return route debt。

SC1 没有改 Move→Attack、FEG、Native Bridge、ContactPair 或 MASM。

---

## 8. SC2 EARLY：更早的 steering window

SC2 只改变一个变量：允许纯 Move→Move 的 effective steering window 更早接近原有 predictive threshold，同时继续受相邻 leg 比例 cap 保护。

09:48 实机证明：大量 waypoint 已经能在约几十米外提前 dispatch。

同时也证明：

> “所有顿挫都只是 steering gate 太晚”这个解释不完整。

仍有低速 PATH_SAFE / route-debt 相关现象，需要继续拆分。

---

## 9. SC3 SOFT DEBT：保留 waypoint 义务，但不无条件堵死后继 Move

PATH_SAFE predictive handoff 可能留下“旧 waypoint 尚未被实体轨迹真正满足”的 route debt。

旧做法是：只要有 debt，后续 handoff 全部 hard block。

SC3 改为：

- debt 记录本身不删除；
- 如果新的 successor chord 仍穿过所有 unresolved debt corridor → `SOFT_PRESERVED`，允许纯 Move→Move 继续；
- 如果新 chord 切离任意旧 corridor → 继续 HARD block；
- Move→Attack / final route / Exit 仍保持 hard semantics。

`SOFT_PRESERVED` 不代表 waypoint 被“算完成”。真实 position / crossing evidence 仍要最终偿还 debt。

10:20 前后的实机结果证明 soft debt 正常工作，但仍存在 `debt=CLEAR` 时的低速/停车，因此 debt 也不是最后所有顿挫的统一解释。

---

## 10. SC4 STALL ESCAPE：Controller corridor 与 WH3 arrival braking 的冲突

SC3 最干净的残余失败链是：

```text
successor 已存在
+ debt=CLEAR
+ route 仍被 TURN_CORRIDOR_REQUIRED 挡住
+ remaining 数秒不下降
+ WH3 先把速度降到 0
+ Controller 才终于允许下一个 Move
```

这揭示了真正的结构冲突：

- 我们希望中间 waypoint 是“转弯参考点”；
- 但 handoff 之前，WH3 仍把它当成“必须到达的 active destination”；
- 如果 Controller corridor 只差一两米仍不放行，CA locomotion 可能先进入 arrival/braking。

SC4 增加 `TURN_CORRIDOR_STALL_ESCAPE`：

- 只用于纯 Move→Move；
- 必须已经有足够 progress / movement history；
- 必须出现 stall 或持续无有效进展；
- escape margin 同时受 predictive threshold、绝对米数、current-leg 比例、next-leg 比例限制。

所以它不是简单把所有 corner window 全局放大。

---

## 11. SC5 EXIT REASSERT：ACK 不等于真的脱战

1044 实机又暴露一个与 waypoint 无关的问题：

```text
Attack hold 完成
→ BSC 提交 Exit MOVE
→ Native status=ACCEPTED
→ UI 已显示撤离命令线
→ 单位仍和敌军保持真实 ContactPair
→ 初期几乎不动
```

这正式证明：

> **Command accepted / UI command line ≠ physical disengagement completed.**

旧代码其实已有 bounded reassert，但 V3 capability 开启后只相信 `V3_EXIT_BODY_STATUS`。该现场恰好连续 `ENTITY_STALE`，于是 recovery candidate 被错误压成 false；而下一次采样前单位又可能已经开始缓慢移动，错过旧的 low-speed reassert window。

SC5 只补这一洞：

- exact V3 body evidence 正常时继续以它为权威；
- **只有当 V3 body status 因 `ENTITY_STALE` 不可用时**，才允许 ContactPair fallback；
- fallback 必须有 fresh enemy contact；
- 必须低速 / Exit progress 不足；
- 必须达到 bounded no-progress 时间；
- 仍受原 recovery budget 与 reassert interval 限制；
- `melee=true` 单独无效；
- `contacts=0` 时不重发。

这样补上了“命令被接受”到“实体真的离开接触”的闭环，同时避免每帧重复 `goto_location()`。

---

## 12. v1.2.0 正式发布收尾

最后一次 SC5 实机测试被确认行为已经足够满意以后，v1.2.0 明确停止继续改 gameplay algorithm。

正式版只做发布化：

- 版本身份改为 `1.2.0`；
- `DEBUG_TELEMETRY=false`；
- 高频 `dlog` 在调用点 DEBUG-gate；
- `Core.feg_log` release 模式直接返回；
- ATTACK / EXIT trace 不创建；
- test-only cancel/generation observation 不创建、不扫描；
- 保留稀疏 startup / fault / refusal / recovery 日志；
- Native / ContactPair / MASM 与 SC5 保持不变。

这也是为什么 Native ABI 继续保持：

```text
1.0.15-r4-evidence-v3-validated-userdata-root
```

---

## 13. v1.2.0 验证记录

整理前的正式 release closure 与整理后的公开树都验证了同一套 v1.2.0 行为。

整理后的公开树重新执行结果：

- **Release jobs: 17/17 PASS**
- **Mutation: 37/37 CAUGHT**
- **Portable Native CTest: 10/10 PASS**

Windows 正式发布仍必须在 Windows 上使用现有 VS2019 v142 x64 + MASM 重新编译：

1. `check_release_v120.py`；
2. CMake VS2019 x64 v142 configure；
3. Release build；
4. Windows CTest；
5. `verify_pe_toolchain.py`；
6. `build_release_v120.py`；
7. `verify_release_v120.py`。

然后只把最终 `.pack` 安装到 WH3 data；不要单独复制 DLL。

---

## 14. 后续维护不可随便破坏的不变量

1. **Command identity 与 physical evidence 必须分离。**
2. **不能用 sticky `melee=true` 单独证明当前真实接触。**
3. **Native ACK 不能当成 physical disengagement 已完成。**
4. **不能为了顺滑直接删除 route debt。** 只有 successor path 仍尊重旧 corridor 时才允许 soft continuation。
5. **Move→Attack 必须比纯 Move→Move 更严格。**
6. **短 leg / 相邻 waypoint cap 必须继续限制 steering / stall escape。**
7. **ContactPair 必须 target/sequence/generation specific。**
8. **缺失或歧义 physical evidence 保持 fail-closed。**
9. **避免继续增加 Lua main chunk 长期 top-level locals。**
10. **实机行为改动优先单变量。**
11. **Native ABI 只在 Native contract/behavior 真变化时改。**
12. **Production telemetry 默认保持关闭，并且关闭时避免字符串格式化开销。**
13. **Windows MASM mid-function hook 必须继续参加真实 Build/CTest。**

---

## 15. 为什么公开仓库不再保留旧阶段碎片

v1.2.0 公开树主动删除了：

- R4 / SC1 / SC2 / SC3 / SC4 / SC5 的旧 Antigravity 指令；
- R3/R4 单独修复说明；
- SC1～SC5 `READ_ME_FIRST` / Package Check / Validation 文本；
- SC1～SC5 controller/block `.diff`；
- 老 Phase B / baseline checksum 快照；
- 一次性 Live Smoke / Diagnosis 文档；
- 重复的 `controller_tests`；
- SC1～SC5 旧 candidate build/check/verify 脚本；
- 原始 research/reverse 笔记集合；
- 历史 validation output dump。

这些内容继续散落在 GitHub 只会让“当前正式版本到底该看什么”越来越不清楚。

真正需要长期保留的技术结论已经全部汇总在本文件。若未来确实要追溯某次原始实验，应该通过旧 release archive / Git commit 历史查找，而不是继续把阶段性垃圾堆在正式仓库根目录。

---

## 16. SC6：Exit canonical cursor 与 Native active order 失配

RMB differential 实机复现锁定了一个与 SC5 “MOVE 已 active 但身体尚未脱战”不同的问题。

真实失败链（`uid=1002 gen=8`）：

```text
Attack 1040
→ BSC Exit MOVE accepted / cursor=Exit
→ 玩家继续 Shift 追加 future ATTACK 1040
→ BSC canonical plan 仍认为 current=Exit MOVE、future=ATTACK
→ CA Native active order 实际变成 future ATTACK
→ UI/计划仍保留 Exit 线，但单位继续执行 ATTACK
→ 手动普通 RMB 的 nonqueued MOVE 才真正替换 Native ATTACK
```

关键不是“RMB 有神秘 combat-cancel flag”，而是 **Lua canonical execution 与 Native exact active execution 已经分叉**。

源码其实早已有 `reconcile_native_successor()`，设计上也已经定义：Native 如果提前执行 successor，handoff ready 时 adopt，否则 rollback current MOVE。但这层仍通过旧 `R1.evidence` 读取 V2 execution identity；生产运行时 V3 `execution_identity=true`，V2 已明确 retired。因此 reconciliation 无法获得 exact successor identity，只能降级到 `current_target()`，最终报：

```text
BLOCKED_EXECUTION_IDENTITY
CURRENT_TARGET_IS_NOT_ACTION_ID
```

但不会执行本来已经设计好的 rollback。

SC6 修复：

- 新增唯一 authoritative `R1.read_active_execution()`：V3 优先；只有 V3 capability 真不可用时才允许 V2 compatibility fallback；
- `R1.execution_matches_action()` 使用 exact execution identity：kind、engine sequence、journal receipt、unit lifetime，以及 ATTACK target / MOVE destination；
- reconciliation 每轮只读取一次 Native active execution；
- exact current action 匹配成功时保持当前；
- exact immediate successor ATTACK：handoff ready 才 adopt，否则 rollback current MOVE；
- exact later future canonical action：绝不跨越中间 action，记录 `NATIVE_FUTURE_OVERRUN` 并 rollback current MOVE；
- exact noncanonical active order：fail closed，不盲目覆盖；
- `current_target()` 只保留诊断用途，不再授权 transition / rollback；
- SC5 physical-disengagement watchdog 只有在 exact current Exit MOVE 已经是 Native active execution 时才运行，避免 execution recovery 与 physical recovery 互相打架。

Native 兼容面也同步硬化：旧 V2 read/bind API 名称继续存在以避免 ABI/API 表面断裂，但有效调用明确返回 `V2_RETIRED_USE_V3`，不再让旧名字静默读取 V3 schema。

### SC6 回归与 mutation

新增 V3 execution regression：

- `V3_ONLY_SUCCESSOR_READY`；
- `V3_ONLY_SUCCESSOR_EARLY_ROLLBACK`；
- `V3_FUTURE_OVERRUN_ROLLBACK`；
- `V3_IDENTITY_MISMATCH_NO_FALSE_ADOPT`；
- `SC5_REASSERT_REQUIRES_CURRENT_EXECUTION`；
- `NONCANONICAL_ACTIVE_ORDER`；
- `V2_COMPAT_FALLBACK`。

mutation gate 从 37 扩展到 **40/40 caught**，新增专门防止：

1. reconciliation 偷偷退回 V2；
2. 忽略 execution sequence 造成 semantic false-adopt；
3. future overrun 直接跳过 canonical intermediate action。

维护脚本 `audit_evidence_wiring.py` 额外保证 execution reconciliation 必须通过 V3-authoritative adapter，旧 V2 Entity/Combat 路径不得进入选定的 gameplay-critical 区域。

---

## 17. SC6 后的 Evidence wiring 审计结论

本轮针对“已有新架构但 gameplay 仍接旧版 provider”的模式做了专项审计。

发现的 behavior-critical 问题只有上述 execution reconciliation 一处：**V3 已是生产权威，但 reconciliation 仍读 V2**。

其余 V2 残留分两类：

- 旧 Entity/Combat physical helper：目前只在 legacy/debug telemetry 中使用，不参与当前 steering / FEG / Exit recovery 决策；
- Native V2 API 名：为兼容保留导出，但 SC6 后 fail-closed 为 `V2_RETIRED_USE_V3`。

维护原则因此补充：

14. **同一 evidence domain 只能有一个 production-authoritative provider。** 新 schema/capability 上线以后，behavior-critical code 必须经过统一 adapter，禁止各模块直接挑 V2/V3 reader。
15. **retired provider 必须 fail closed。** 不能仅靠 `capability=false` 阻止误用，同时让旧 API 名继续返回新 schema 数据。
16. **Execution identity recovery 必须先于 physical recovery。** 若 Native active action 都不是当前 Exit MOVE，不能把问题当作“MOVE active 但脱战慢”交给 SC5。
17. **semantic state 不能替代 execution identity。** `current_target()`、`melee`、UI command line、destination 等可用于诊断/physical evidence，但不能授权 canonical cursor 跳转。

