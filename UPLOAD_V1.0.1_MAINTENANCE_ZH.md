# v1.0.1 GitHub 档案维护上传

此目录已经是完整的 v1.0.1 仓库替换树。请在本地克隆仓库根目录执行，而不是只把文件覆盖后漏掉删除/移动：

```powershell
git checkout main
git pull --ff-only
# 将本维护包内容完整同步到仓库工作树；注意 release/better_shift_command.pack 已移动到 release/v1.0.0/
git add -A
git commit -m "Archive v1.0.1 self-contained Steam release"
git push origin main
```

建议提交后检查：

```text
README.md -> Current release baseline v1.0.1
docs/00_CURRENT_STATUS.md -> v1.0.1
src/lua/better_shift_command.lua -> CONTROLLER_VERSION 0.2.6
src/native_bridge/src/lua_module.cpp -> 0.5.1-per-kind-calibration
docs/validation/V1.0.1_RUNTIME_VALIDATION.md -> exists
docs/deployment/STEAM_SELF_CONTAINED.md -> exists
tools/release_v1.0.1/ -> exists
release/v1.0.0/better_shift_command.pack -> historical old binary
```

不要把 TESTFIX A/B ZIP、Antigravity 临时输出目录或本机 `output/build_*` 目录提交到主仓库。
