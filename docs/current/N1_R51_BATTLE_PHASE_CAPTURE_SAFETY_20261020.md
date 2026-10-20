# Better Shift Command R51（本对话第 17 轮）—— Battle 生命周期与无 Hook 读取窗口审计

日期：2026-10-20。目标：继续 R49/R50 的实验性无 Hook 成员读取工具，**判定 WH3 Lua BattleManager 是否提供可以保证战斗工作线程静止的采样窗口**。所有调研只用用户已有 MOD 实际代码、当前研究分支的 R49/R50 源码和 WH3 Battle Manager 公开接口定义。

**核心结论：尚未发现这种安全窗口。战斗脚本回调属于 Lua/UI 控制面，战斗成员 Tick 等 Native 更新可能在其它线程继续运行。** 因此 R51 是阶段／计时／错误结果拒绝协议，不是安全的游戏内采集包。没有原生线程同步屏障，不能宣称整队原子快照，也不能保证无 ABA / Use-After-Free。未运行游戏，没有加载 memreader DLL、没有运行 Hook、没有 gameplay Patch。

## 一、确凿的实际 Derpy MOD 证据

用户提供的 `derpy_third_person.zip` 在 `script/derpy_tp/` 下包含：

- `main.lua` 末尾：`bm:repeat_real_callback(frame, 1, "derpy_tp")`。它在 Lua/UI 实时计时中做控制输入，不是“工作线程 Tick 结束后”回调。
- `main.lua` 使用 `bm:time_elapsed_ms()` 区分**模型时间**与 `os.clock()` 实时；暂停状态由 `PAUSE_AFTER=0.5` 的无变化时间启发式推断，作者注明短暂暂停初期仍可能运行。模型时间不变 ≠ 模型对象稳定，暂停 ≠ 工作线程栅栏。
- `main.lua` 注册 `"Complete"` phase callback 来停止自身控制；`script/battle/mod/derpy_third_person.lua` 在 `"Deployment"`、`"Deployed"` 阶段显示 UI 状态，且拒绝多人战斗和 replay 的控制行为。这些阶段标识能限定研究控制器何时**拒绝**采样，但不能证明何时**可以安全**解引用指针。
- `platform.lua` 邮箱注释明确说明 Lua 线程调用 stop/walk builder 与工作线程的成员动作析构竞争曾经引发崩溃，因此作者将动作修改移至成员 Tick 的原生 cave。**这只是 Derpy 在修改成员动作时的实机经历，不直接证明任何特定只读内存获取已崩溃。**

外部接口说明：Warhammer III Battle Manager `bm:repeat_real_callback()` 是 UI 实时计时，`bm:repeat_callback()` 才绑定模型时间；`bm:register_phase_change_callback()` 观察 `Deployment/Deployed/VictoryCountdown/Complete`。见 https://chadvandy.github.io/tw_modding_resources/WH3/battle/battle_manager.html 。**两类 timer 和 phase change 都没有承诺 Native worker barrier。**

## 二、R49 / R50 已有能力与原有缺口

- R49 `bsc_r49_guarded_passive_sampler_research.lua` 只手动 `M.sample(unit,opts)`，有完整成员数组二次读取、代码变更检测、位置/动作字段预算、`read_duration_us`；但仅提供 **sequential-not-atomic** 证据，`opts.time_ms` 原来仍由外部提供。
- 研究分支后来已经有 R50 `bsc_r50_monotonic_capture_adapter.lua`，用 `mr.ticks()/mr.elapsed_us()` 生成可信的相对时间及序号，不允许调用者伪造 `time_ms`。本轮核对它存在于远端 HEAD，并作为正式依赖引用，不覆盖它。
- 即便 R49 完整成员数组前后相同，仍不能排除数组读入时暂时变化后恢复、成员析构后同地址复用、成员当前目标／速度在逐行读取之间改变，或战斗工作线程在这 5000 微秒内更新某些成员。

## 三、本轮实际新增 R51 原型（不自动加载）

文件：`maintenance_tools/native_shift_re/bsc_r51_battle_lifecycle_gate.lua`。

- `M.new(bm, R50, R49)`，生命周期监听回调只写本地 `phase/terminal` 状态；**不会在 `bm` 回调中调用 memreader 或读取士兵**，也不创建定时循环。
- 自动拒绝 Multiplayer、Replay；只有 `Deployed` 阶段的显式 `capture_once()` 才有机会进入底层工具；`VictoryCountdown` 或 `Complete` 后永久禁用本实例。
- 读取前后各调用 `bm:get_current_phase_name()`、`bm:time_elapsed_ms()`、`bm:is_multiplayer()`、`bm:is_replay()`；一旦跨阶段、模型时间推进或游戏模式变化则**丢弃**结果。
- 由 R50 自动生成 `sample_id/time_ms`，拒绝调用者输入；采样尝试最多 3 次（失败也计），禁止原始异常字符串流出。
- 底层结果必须声明 `sample_type=sequential-not-atomic`、完整 roster 守卫与 5000 微秒预算，且 Native Patch 未授权；本层额外写明 `worker_thread_quiescence_proven=false`、`engine_atomic_snapshot_proven=false`、`cannot_prove_no_memory_lifetime_race=true`。
- `experimental_unsynchronized_capture=true` 只为离线 API 模拟保留，**不是实机使用授权**。没有 proof 前，不能让玩家安装 R51 或自行开启选项。

在此强调：即使采样前后 `bm:time_elapsed_ms()` 相同，也没有原生线程同步屏障；**UI real callback 不是工作线程同步点**。R51 的通过结果不可宣称“线程安全”。

## 四、测试等级

- R51 Lua 5.3/texlua **23/23** 运行级模拟通过，实际调用了 R50 模块，覆盖 phase 登记、多人/录像拒绝、显式开启、跨 phase/model-time 丢弃、模型时间未变化仍标非原子、3 次尝试预算、结果协议、错误脱敏等；完全没有执行游戏或 DLL。
- R51 Python 静态反证覆盖 Derpy/R49/R50/R51 源码的 16 条实际接口约束，对假代码写入 API、增加自动 timer、在 phase callback 中增加 native read 等进行拒绝测试。
- 旧 R49 Lua 模拟 **20/20**，R50 Lua 模拟 **10/10** 重新执行通过；这些是回归，不是本轮新增实机证据。
- 使用用户 Derpy unpack 作为私有数据做静态检查；交付包不重发布第三方 `.pack`、Native DLL 或游戏 EXE。

## 五、下一步的止损与路线选择

1. **止损：不要继续把“选择 Deployed callback”和“减少读取时间”误认为 Native 原子观测。** 它们只是实验控制面，改善时间和生命周期拒绝条件。
2. 可以用录像/玩家已有原始位置数据继续做纯空间形变定量，但不能给它添加未采集的动作虚表和新旧目标。
3. 真要保证成员读取与生命周期配对，需要先静态审计一个 Native 线程内只读采样点及安全发布方案：确定当次 `member` 对象存活期、CPU volatile/non-volatile 保存、stolen instruction/branch/unwind、线程重入与每线程状态；将样本发布到固定大小无阻塞环形缓冲。**不能复制 Derpy 的写动作 Cave 就声称安全**。
4. 若无法证明原生探针的安全上限，则停止实机提案、继续静态定位动作与积分状态不一致的具体因果条件。仍不需要用户重复证明 Shift 缺陷。

**证据状态**：`derpy_source_static=PASS`、`r49_compatible=PASS`、`r50_monotonic_mock=PASS`、`r51_bm_mock=PASS`、`engine_atomic_snapshot_proven=false`、`real_game_read_tested=false`、`root_cause_proven=false`、`gameplay_patch_authorized=false`。
