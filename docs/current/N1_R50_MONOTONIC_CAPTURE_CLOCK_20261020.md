# BSC 第17轮 / R50：R49 采样器单调时钟真实性补强（2026-10-20）

**研究性质：只读工具补强；未进游戏、未加载 DLL、未安装 Hook、未修复 Shift gameplay。**

## 本次核对已存在的研究分支

研究分支此前已经存在更完整的 R49 正式实现：`bsc_r49_guarded_passive_sampler_research.lua`、`r49_spatial_evidence_preflight.py`、20项 Lua 模拟和更严的 roster epoch 守卫；因此本轮**不覆盖已有 R49**。我另行制作的 R49 静态兼容性对照包只作为独立佐证，不是正式 R49 的替代品。

审读 R49 发现一项可以确认的数据协议缺口：`valid_opts()` 校验调用者 `opts.time_ms` 为整数且递增，`sample_inner()` 使用该值判断跨样本 `MAX_GAP_MS=250` 并原样写出。这仅证明调用参数格式正确，不保证两次采样真实时间间隔正确。若实际经过660ms而调用者传入120→130ms，离线预检会把长时间间隔视为10ms。R49 已有 `read_duration_us` 仅测**单次**耗时，不能代替**跨次**时钟。

## 新增实际代码与测试

- `maintenance_tools/native_shift_re/bsc_r50_monotonic_capture_adapter.lua`：手动调用的外层纯 Lua 包装器；使用 memreader Plus 0.13.0 的 `mr.ticks()`／`mr.elapsed_us(epoch)` 生成 `sample_id/time_ms`，禁止调用者自行指定这两个字段。少于1ms且取整同毫秒时直接拒绝，不伪造递增时间。异常/采样失败时不提交新序号；成功后验证采样器回传的样本序号、时间、`sample_type=sequential-not-atomic`、`native_patch_authorized=false`。重置时先调用 R49 自身 reset，然后清理 wrapper 时钟。
- `tests/test_r50_clock_adapter.lua`：真实 Lua 5.3 解释器 `texlua` 执行、全模拟 API 的 **10/10 PASS**。覆盖毫秒边界、660ms 真实间隔、伪造时间和序号拒绝、异常重试不推进序号、返回时间错配拒绝及同步重置。无需游戏 DLL。
- R49 独立对照静态验证：用户上传的新 EXE SHA `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496` 与 memreader Plus 0.13.0 / Derpy pack 源检查通过；独立 Lua 13/13 模拟、Python 8/8 测试通过（仅离线，不含 gameplay）。
- 资源包：`BSC_R50_MONOTONIC_CAPTURE_CLOCK_20261020.zip`（本地完整交付，带上次独立对照资料，不包含 EXE、DLL、第三方 MOD 内容）。

## 不应该夸大的结论

本轮修复的是**跨采样时钟来源可信性**，不是游戏引擎的同步屏障。R49 的完全 roster 字节复核仍无法排除 ABA；采样时间即使相近也不是全兵牌原子快照。`pcall` 无法保证另一个游戏工作线程析构时不会出现原生崩溃。R50 本身没有自动启动、写内存、调用原生函数或安装 Hook。

下一步必须依照 R49 preflight 继续做有限、低频、匿名的空间诊断；仅在拿到同一兵牌具体实例差异后才能决定目标生成或运动积分哪个才是实际错误点。保留原生 CA Shift、渐进转向、避障、RMB 与 Shift ATTACK；不改 main。

**证据状态：** `static_and_mock=PASS`, `game_live_sampling=NOT_RUN`, `atomicity=NOT_PROVEN`, `root_cause_proven=false`, `native_gameplay_patch_authorized=false`。
