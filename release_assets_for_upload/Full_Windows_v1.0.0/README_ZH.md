# Better Shift Command v1.0.0

Better Shift Command 用于改善《全面战争：战锤 III》的 Shift 队列战斗命令。

## 功能

- Shift 连续移动点之间更平滑的提前交接。
- Move -> Attack 预测交接，减少原版“到点停住、转身、再攻击”的顿挫。
- `Shift 移动... -> Shift 攻击 -> Shift 移动`：与指定目标实际近战累计约 3 秒后执行后续移动，适合骑兵脱战。
- `普通右键攻击 -> Shift 移动` 同样支持约 3 秒近战后的自动脱离。
- 玩家新的普通右键命令始终优先，会取消 Controller 的旧计划。

## 前置要求

- Windows x64 版 Total War: WARHAMMER III。
- `wh3_native_bridge.dll` 和 `minhook.x64.dll` 必须放在 `Warhammer3.exe` 同级游戏根目录。
- `.pack` 必须在游戏 Mod Manager（或兼容 WH3 Mod 管理器）中启用。

## 安装

### 推荐

双击 `Install_Full.bat`，按提示安装。

### 手动安装

1. 将 `data/better_shift_command.pack` 放进 `<战锤3>/data/`。
2. 将 `wh3_native_bridge.dll` 和 `minhook.x64.dll` 放到游戏根目录，与 `Warhammer3.exe` 同级。
3. 在 Mod Manager 中启用 `better_shift_command.pack`。

## Steam Workshop 用户

如果已经订阅 Workshop，Steam 会提供 `.pack`。只需要从 GitHub/Nexus 下载 **Native Bridge Only** 包并运行一次安装器。

## 卸载

运行 `Uninstall_Full.bat`，或手动删除这三个文件。安装器会备份被覆盖的同名文件；卸载器只删除与本版本 SHA256 一致的文件，并尽可能恢复备份。

## 游戏更新

Native Bridge 对关键游戏地址有字节 guard。WH3 大版本更新后如果地址变化，Bridge 会拒绝启动，直到发布兼容的新 Bridge。这是故意的安全保护。

## 源码与技术文档

GitHub 仓库提供 Lua/C++ 源码、实机验证记录、逆向说明和 CA 更新后的地址恢复手册。
