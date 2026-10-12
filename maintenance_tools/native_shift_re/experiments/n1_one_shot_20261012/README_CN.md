# 修复版说明 — 2026-10-12 · PTRFIX

**此包替代 `BSC_N1_903_ONE_SHOT_NATIVE_TEST_READY_20261012.zip`，请勿再使用旧包中的脚本。**

你遇到的 `TypeError: cannot define variable 'ptr'` 是交付脚本顶层 `function ptr()` 与 Frida 内置的 `ptr` 冲突导致。旧版启动后从未达到 `TRACE_ACTIVE`，没有有效实机采集。现在已把助手函数改名、全部探针包在私有作用域内，并新增“Frida 内置 ptr 不可重定义”离线模拟验证。**这次是启动修复，不是 Native 游戏行为修复。**

解压这个新的 ZIP 到一个**新文件夹**，不要将个别文件混入旧包。已安装的 Python、Frida 无需重复安装。对战锤3的操作仍然只有同一队普通步兵 RMB 折返一次与 Shift 连续 MOVE 折返一次，采集默认 18 秒。**一旦再次报错，不要反复重试，只贴 PowerShell 最后几行；不要把本轮启动失败当成游戏运动结论。**

已离线验证：原始 WH3 EXE SHA 固定匹配，14/14 原始机器码及真实反汇编指令起点通过；Node.js 模拟包发送、成员接收和运动采样通过；追加 protected-ptr global collision 反例回归通过；Python 10 项测试中 9 项通过、1 项因为 CI 不提供游戏 EXE 而跳过。尚无 Windows 真机 Frida 脚本加载成功的结果。

---

# Better Shift Command / N1 — 一次性原生来源与折返运动采集（2026-10-12）

## 测什么？

这次**不再证明 Shift 有挤压缺陷**，也不测试多个参数。目标只有一个：**将游戏实际执行的成员发包者与同一成员的目标写入、目标反转和随后运动位置配对**，同时观察原生普通 MOVE 与排队 MOVE 相关入口是否命中。

已在上一次真实日志中发现：同组两名已采样成员在 group Tick **1584** 时相隔 **1 毫秒**提交几乎 180° 的新运动目标；其中一名在多个后续 Tick 中仍有向旧方向的运动位移。这提示应该区分**目标交接不同步**与**CA 渐进式物理转向**。不过旧日志没有证明该次折返究竟来自 RMB 还是 Shift，也只跟踪到两名成员。

新采集器修正了以下问题：

- 不再把通用延迟接收器命中当作已证实的 B 路线事件；采集原始成员接收函数的真正返回 RVA，并同时监听三个已确认的发送调用点：A `0x030D550F`、B 缓存 `0x03265D3F`、通用构造后改包 `0x03284B7B`。
- 记录发包所属任务、成员、群组、实际包和目标；遇到目标急剧反向后，以原生群组 Tick 对队形内分散位置的成员连续采样（最大 22 个模型，后续 18 个 group Tick），而不只是再次写目标时取样，区分目标切换与物理运动方向。
- 不再等 Python 主线程无限阻塞在 `session.detach()`；Frida JS 先撤销 Hooks，Python 子进程在卸载异常时由独立监督进程限时终止。仍然**不能保证 Frida 在你的机器上绝不崩溃**。
- **测试时间默认 18 秒**，不是 120 秒，更不要求一直折返。

## 先完成的验证（不是实机通过）

- 用户精确原始 EXE SHA256：`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`
- 14/14 个原生 Hook 入口：**字节守卫、PE 可执行节、unwind 原函数边界、独立 GNU objdump 指令起点 PASS**。
- 三条 A/B/改包成员虚调用的原生 6 字节与返回 RVA 一致 PASS；两处任务虚表与构造器→发送者 call 守卫 PASS。
- JavaScript `node --check` PASS；Frida API 离线模拟：**发送→接收→延迟分支→折返目标提交→Hook 撤销 PASS**。
- Python 10 项自动化测试（9 执行通过，1 按条件跳过）：错误 EXE 拒绝、来源匹配负对照、超时监督、模拟 Frida 假死卸载 PASS。
- **Windows 实机 attach 尚未执行**；工具是一次只读诊断，不是修复 DLL；Frida 临时插桩代码，不改 EXE 文件与游戏业务数据。发包和目标写入事件按成员抽样以限制开销；目标大角度反转判据对已识别成员逐个检查，转弯位置连续采样来自原生群组 Tick。

## 唯一一次采集如何运行

请在**单人自定义战斗**里先选好一队普通步兵，镜头对准平坦地面，游戏保持运行。解压本 ZIP 后，在该文件夹地址栏输入 `powershell` 回车。

首次使用才安装：

```powershell
python -m pip install frida
```

之后复制下面完整命令：

```powershell
$game = Get-CimInstance Win32_Process -Filter "Name='Warhammer3.exe'" | Select-Object -First 1
if (!$game -or !$game.ExecutablePath) { throw "战锤3尚未运行" }
python .\run_one_shot.py --exe "$($game.ExecutablePath)" --pid $game.ProcessId --seconds 18 --out .\bsc_once_source.jsonl
```

看到 `TRACE_ACTIVE` 后切回游戏，**同一队普通步兵**：

1. 先右键 MOVE 一次，再右键向相反方向移动一次（普通 RMB 对照）。
2. 用 Shift 连续安排前进→折返两段 MOVE 路线一次（保留 CA 渐进转弯）。

命令操作完成即可，不要反复调整或再测挤压。运行满 18 秒会**自动停止并保存**（采集时间不要求连续操作 18 秒），不是要求重复操作。运行成功会出现 `TRACE_FINISHED`，并自动生成同文件夹中的 `bsc_once_source_report.json`。

将这两个文件压缩一次上传到当前 ChatGPT 对话：

```powershell
Compress-Archive -Path .\bsc_once_source.jsonl, .\bsc_once_source_report.json -DestinationPath .\BSC_ONCE_RESULT.zip -Force
```

如果出现 `FAIL_CLOSED`、`TRACE_NO_SUMMARY`、游戏异常退出或卡住，**不要重试**，只发 PowerShell 末尾输出及已经生成的 `.jsonl`。监督者最多等待执行时间再加短暂的清理宽限，不会主动关闭战锤3。自动脱钩的运行行为仍需要这次 Windows 真实测试确认。

## 本轮收集什么？

- `NATIVE_MEMBER_SEND`：已证明的 A/B/构造后改包发送点，以及真实 member、group 和 packet。
- `MEMBER_RECEIVER`：公共成员接收器原始返回 RVA，能够检查发送者是否真正匹配，而不是仅凭 packet 指纹。
- `DEFERRED_PACKET`：确实进入延迟分支时记录上游来源；不再用 `B_DEFERRED_RECEIVE` 的误导性名称。
- `MOTOR_GOAL_REVERSAL`：旧/新 motor 目标方向夹角近似折返的真实写入。
- `GROUP_TICK_POSITION`：在原生群组 Tick 入口对最多 22 个阵型位置分散采样的成员连续记录 X/Z，持续不超过 18 个 group Tick；`POST_TURN_POSITION` 仍记录真实目标提交后的伴随位置。
- `QUEUE_MANAGER_ENTRY`、`QUEUED_CONTINUATION`、`NATIVE_MOVE_ISSUER`：原生发令上游的命中信息。它们仍不是玩家键盘输入的完整签名，**不能仅凭单独一次命中宣称 Shift 因果已证明**。

本工具不会把原始运行时地址、游戏 EXE 和私人日志自动上传任何网络服务。日志请只在本对话内提供。**即使运行成功，静态/观测验证通过也不等于已经修好 Mod。**
