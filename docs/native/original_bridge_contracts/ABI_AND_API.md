# v0.5.0 Lua 接口契约

绑定游戏导出的 Lua 5.1 C API；`lua_Number=float32`。不装第二个 Lua VM。所有 u32 标识为 canonical 十进制字符串。数字字段仅用于坐标、有限计数与原始小字段。

| 函数 | 返回 |
|---|---|
| version() | `0.5.0-attack-native-token` |
| number_abi_probe() | number `16777215`, number `1.5` |
| exact_id_probe() | string `4294967295`, string `16777217` |
| capabilities()/get_status() | 实际状态表，生产放行标志不伪造 |
| start_observer(true) | true，或 false/error |
| begin_battle(session) | **一个** epoch string，或 nil/error |
| end_battle(epoch) | true，或 nil/error |
| get_battle_epoch() | epoch string |
| get_unit_revision(uid_string) | revision string，或 nil/error |
| read_journal(epoch,after,count) | records,metadata（最后返回的 serial 作 next_after） |
| acknowledge(epoch,after) | true，或 nil/error；禁止跳过未读前缀 |
| arm_verified_issue(false) | 显式停用，true 或 nil/error |
| arm_verified_issue(true) | 默认构建拒绝 NATIVE_RELEASE_NOT_APPROVED；实验构建需 accepted MOVE + accepted ATTACK + 至少一个 handler + 零 fault |
| issue_verified_command(kind,queued,uid,revision,callback) | issue string + PENDING_NATIVE_ACCEPTANCE，或 nil/error |

发令 callback 仅允许一次与元数据匹配的 singleton 原生 Move/Attack，单位不能临时切换成别的对象；闭包返回不等于已受令，以 journal 的最终状态为准。用 `lua_pcall` 收束 Lua 异常。绑定调用本身不持有跨 Lua longjmp 的 C++ RAII 锁。

新 pack 与新 DLL 版本锁配套安装。旧 v0.2.2 客户端的版本锁是正确的，因此新 DLL **不是旧 pack 的无条件 drop-in 替代**。回滚时 DLL 与 pack 成对恢复。保留旧 journal 字段形状，不凭此声称旧版本检查会自动通过。

本包没有完整原生批次，也没有自身 verified Halt。`flags_valid_mask=0` 明确表示未复用旧 DLL 的位定义；各保留字段按独立有无检查。不得把 0 当作旧位定义已经验证。

## v0.4.6 path telemetry

`get_status()` additionally returns decimal-string counters: `publish_seen`, `publish_parsed`, `publish_unparsed`, `writer_begin_seen`, `writer_finalize_seen`, `writer_committed`, `copy_seen`, `stage_seen`, `selection_seen`, `selection_resolved`, `native_packet_seen`, `native_packet_mapped`, `native_attack_token_bindings`, plus `last_path_stage`.

v0.4.6 also adds decimal-string telemetry: `handler_seen`, `handler_resolved`, `handler_missed`, `last_reader_data`, `last_reader_a`, `last_reader_b`, `last_reader_cursor`, and `last_reader_end`. `selection_*` remains diagnostic only; a zero `selection_resolved` does not block exact provenance when `handler_resolved` succeeds.


## v0.4.6 physical lineage
`physical_spans` now counts lineage fragments rather than whole-packet-only spans. Public Lua API semantics are otherwise unchanged.

### v0.4.6 reader-lineage diagnostics

`get_status()` also returns decimal-string `last_reader_lineage_bytes` and `last_reader_lineage_fragments`. They are telemetry only. Neither field participates in exact packet resolution or source attribution.

## v0.4.7 experimental telemetry

`get_status()` additionally exposes `handler_calibration_ready` (boolean) and `handler_token_bindings` (decimal string). `physical_path_witnesses_ready` remains the stricter physical mapping diagnostic and is not rewritten to true by handler-only calibration.

## v0.5.0 accepted-calibration telemetry

`get_status()` additionally exposes:

- `experimental_calibration_ready` (boolean)
- `accepted_move_seen` / `accepted_attack_seen` (boolean)
- `handler_move_seen` / `handler_attack_seen` (decimal-string counters)

`handler_calibration_ready` remains the older strict two-handler diagnostic and is no longer the ExperimentalIssue arm predicate.
