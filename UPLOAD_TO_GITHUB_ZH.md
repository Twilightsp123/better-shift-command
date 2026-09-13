# GitHub 上传步骤 — Better Shift Command v1.0.0

## 1. 新建仓库

仓库名：`better-shift-command`

建议 Description：

`Smooth Shift movement, predictive attack handoffs, and timed disengagement for Total War: WARHAMMER III.`

Public / Private 由作者决定。正式公开发布前先决定项目 LICENSE；`LICENSE_DECISION_REQUIRED.md` 说明了这个未决项。

## 2. 上传仓库内容

将本目录中的内容上传到仓库根目录。`release_assets_for_upload/` 目录中的二进制 ZIP 是 GitHub Release 资产，可不长期提交到 Git history；如果希望仓库更干净，可以在首次 commit 前删除该目录，Release 时单独上传里面三个文件。

必须长期保留在 GitHub 的核心档案：

- `docs/00_CURRENT_STATUS.md`
- `docs/01_COLD_START_RECOVERY.md`
- `docs/native/ADDRESS_RELOCATION_PLAYBOOK.md`
- `docs/native/HOOK_AND_GUARD_TABLE.md`
- `docs/native/KNOWN_NATIVE_STRUCTURES.md`
- `docs/native/REVERSE_ENGINEERING_HANDOFF.md`
- `docs/history/FAILED_APPROACHES.md`
- `docs/validation/HF5_RUNTIME_VALIDATION.md`
- `src/native_bridge/`
- `src/lua/`

这些文件是长期恢复项目的权威入口，不应只放在本地聊天归档里。

## 3. 首次 commit

建议 commit message：

`Release Better Shift Command v1.0.0 runtime-validated baseline`

## 4. 创建 tag / Release

Tag：`v1.0.0`

Release title：`Better Shift Command v1.0.0`

上传：

- `BetterShiftCommand-v1.0.0-Full-Windows.zip`
- `BetterShiftCommand-NativeBridge-v1.0.0-Windows.zip`
- `SHA256SUMS.txt`

这些文件在 `release_assets_for_upload/`。

## 5. 发布后固定维护规则

- CA 未更新、16 guards 全匹配：不要重新逆向，直接按 `01_COLD_START_RECOVERY.md` 实机 smoke。
- CA 更新导致 guard mismatch：按 `ADDRESS_RELOCATION_PLAYBOOK.md` 重定位已知语义角色，不重新研究 Shift 基础语义。
- 新 Controller 功能不得覆盖/删除 `FAILED_APPROACHES.md` 中的历史反例。
- 每个新的 runtime-validated baseline 必须更新 `00_CURRENT_STATUS.md`、`VERSION_HISTORY.md` 和 validation 文档，并打新的 Git tag。
