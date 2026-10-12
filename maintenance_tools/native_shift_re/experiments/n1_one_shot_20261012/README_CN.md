# BSC N1 / 真实来源采集 v3 — 2026-10-12

**用途：修复上一次已经成功的 18 秒实机采集中的日志丢失，不是 Native Patch，也不是游戏 MOD。**

上一次 2097 行 JSONL 包含有效折返数据，但 21,534 次队列管理器 Hook 淹没了来源记录。新版本按原生事件类型保留必要的来源／目标／队列事件、限制队列管理器日志、去掉没有结构证据的 `member+0x60`“阵型序号”判断。

## 不需要立刻重复测试

你的第一次有效日志已重新离线分析：见 `docs/current/N1_903_20261012_FIRST_VALID_SOURCE_TRACE_LOGGER_OVERFLOW.md`，完整脱敏复盘在同批完整交付包的 `REPORT_CN.md` 和 `reanalysis_sanitized.json`。这次新代码的本地原始 EXE、模拟器和 GitHub CI 回归测试已通过，但还没有在 Windows Frida 中运行；不宣称游戏内行为已经验证。

仅在决定需要补足真实 sender RETURN-RVA、同成员 packet 和 queued order 关联证据时，再选择执行**一次**新采集。

## 使用（仅在需要时）

把新 ZIP 整体解压到新文件夹；不要和早前 PTRFIX 包混用。单人自定义战斗，准备一队普通步兵，先把镜头与选中单位调好。该 Windows 机器已安装 `frida` 的话不需重新安装。在解压目录 PowerShell：

```powershell
$game = Get-CimInstance Win32_Process -Filter "Name='Warhammer3.exe'" | Select-Object -First 1
if (!$game -or !$game.ExecutablePath) { throw "战锤3尚未运行" }
python .\run_one_shot.py --exe "$($game.ExecutablePath)" --pid $game.ProcessId --seconds 18 --out .\bsc_once_source_v3.jsonl
```

出现 `TRACE_ACTIVE` 才操作一次普通右键折返 + 一次 Shift MOVE 连续折返，18 秒自动结束。输出 `bsc_once_source_v3.jsonl` 和 `bsc_once_source_v3_report.json`，保留它们即可；不要因为没有匹配等级就自行再跑第二轮。若初始化失败，保存终端报错，不重复尝试。

## 安全／离线条件

只对固定 SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` 的原始战锤3版本执行，通过 PID／磁盘 EXE／机器码保护后才开启 Frida。临时 Hook 修改并恢复游戏代码字节，读取目标/位置数据，但没有主动修改 MOVE 指令、目标或 EXE 文件。游戏运行时 Frida 插桩本身仍有崩溃风险。

包内 `verify_original_probe.py` 在包含 GNU objdump 的开发机上检查 14/14 原始 x64 指令入口；`test_probe_node.js` 和 `test_offline.py` 不进入游戏。真实用户的日志、游戏原始 EXE 不随包分发、不入公开 GitHub。
