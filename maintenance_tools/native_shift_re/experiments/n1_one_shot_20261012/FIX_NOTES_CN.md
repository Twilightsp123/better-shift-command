# PTRFIX — 修复 Frida `cannot define variable ptr`（2026-10-12）

- **故障阶段**：Frida Script.load/初始化；原先脚本内顶层 `function ptr` 与 Frida 自带 `ptr` 不可重定义函数发生变量绑定冲突。上一次测试没有进入 `TRACE_ACTIVE`，与游戏命令或 Shift 运动无关。
- **修复 1**：重命名辅助函数 `ptr` → `readMemberPointer`，只更改 JavaScript 内部指针读取辅助函数的标识符，不更改任何原生目标包或 Hook RVA。
- **修复 2**：整个脚本套入独立 IIFE 作用域，避免后续其他助手函数与 Frida 全局命名冲突。
- **修复 3**：Node 的 Frida mock 现在将内置 `ptr` 定义为不可写、不可配置的全局属性；新的 `test_frida_globals.js` 特别验证旧版声明在该环境中应当报错、新版安全隔离。
- **修复 4**：Windows 启动器在附加游戏进程前添加 JS 全局冲突静态防护；脚本完全没有进入 ready 时明确显示 `TRACE_SETUP_ABORTED_BEFORE_ACTIVE`。
- **验证**：`node --check one_shot_native_source.js` PASS；`node test_frida_globals.js` PASS；`node test_probe_node.js` PASS；`python -m unittest -q test_offline.py` 10 项（9 pass, 1 skip）；`verify_original_probe.py` 对原始 WH3 EXE 14/14 PE/unwind/objdump/字节守卫 PASS。
- **未声称**：修复不代表 Frida 已经在用户 Windows 游戏中成功加载；没有游戏运行时新的 JSONL；没有 Native 修复 DLL；没有修改原始游戏 EXE。

完整启动说明请阅读 `README_CN.md`。实验失败请保存控制台报错，停止重复测试。
