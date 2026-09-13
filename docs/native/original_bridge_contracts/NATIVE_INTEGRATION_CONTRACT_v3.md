# Native Adapter 接线契约 v3

## 1. 正式边界

本文件保留旧契约中“无法归因的自身命令不能当外部命令继续执行”的要求。v0.4.1 实现了已提取路径上的原生接线，但没有证明所有存储生命周期和转发路径，因此默认关闭生产发令；不会把要求降成“看起来像自己即可”。


## 1.1 v0.4.4 runtime correction

The first controlled v0.4.2 battle proved native Move/Attack observation and revision increments but never reached the physical witness gate. The blocker was not the copy/stage hook ABI: it was publication metadata admission. `0x142C68624` constructs the singleton subject vector at `cmd+0x10=count`, `cmd+0x14=capacity`, `cmd+0x18=array`; Move `0x142D6DA64` stores `is_queued` at `cmd+0xA8` and `fast` at `cmd+0xA9`. v0.4.1 read fabricated selection offsets and read Move queued from `+0xA9`, so real publication scopes were rejected before tracking.

v0.4.4 uses the constructor-backed layout. External packets may establish a **physical calibration witness** even when optional descriptor metadata cannot be decoded, but such a packet is always `owned=false` and can never produce `OUR_CONTROLLER`. Controller-owned publication still requires exact singleton recipient, queued bit, issue token, and expected revision.

## 1.2 v0.4.5 consumer authority correction

Real-game v0.4.4 telemetry proved `selection_seen=3`, `selection_resolved=0`, `native_packet_seen=0`. Therefore `0x142DCAF24` is no longer provenance authority. v0.4.5 hooks the real synchronous BCQ handlers `0x142D95F8C` (Move) and `0x142D95A50` (Attack), resolves an exact tracked physical interval at handler entry, and exposes that packet only through the active thread-local HandlerScope until handler return. The selection hook remains diagnostic only.


## 2. 已实现的受控路径

```text
Lua issue_verified_command(kind, queued, uid_string, revision_string, callback)
 -> 单单位 snapshot / issue
 -> 显式受保护 callback
 -> 对应 Lua common Move 或 Attack 入口（kind/queued/L/调用次数检查）
 -> 对应发布包装器，读取真实 singleton recipients 和 queued
 -> writer begin/finalize：提交精确 span 和 metadata；失败写入自身 writer abort flag
 -> 已提取的 fixed-buffer/vector/staging 复制路径传播同一逻辑 packet
 -> selection reader 读取实际 data/start/length/cursor
 -> x64 unwind 动态调用帧仍存活时，关联原生 per-unit Move/Attack
 -> 核心 gate 检查身份、单位寿命、expected_revision
 -> 通过后才调用原函数；捕获实际 slot/engine_seq/outcome
 -> journal 值副本；Lua 验证分页后 acknowledge
```

原生复制输入、目的地址、范围或边界不匹配时不按内容查找。不把所有 Lua 发令、同线程调用或相同目标当成本 Controller。

## 3. 精确事实与实现假设

| 项目 | 使用方式 | 覆盖边界 |
|---|---|---|
| writer buffer | `queue+8` 内联地址；`buffer+0x5000` u32 cursor | 不把 `[queue+8]` 当指针 |
| writer finalize | 正常回填 u16 包长；失败回退 cursor | 保留 payload 旧字节，不能用字节还在判命令有效 |
| reader | `+0x10` data，`+0x18` length，`+0x1C` start，`+0x20` cursor | 仅在 start+7 与 end 精确匹配已跟踪 span 时关联 |
| frame | RtlVirtualUnwind 得到动态 activation | 需要 Windows 实际执行验证；没有 unwind 证据就不建立关联 |
| storage generation | sidecar 自有代次，跟随已经观察到的覆盖/释放/复制 | 不声称存在原生 generation 字段；未观察路径不在证明范围 |
| native bool | AL bit pattern 判 accepted，EAX 完整转发 | 非零高位不能制造 accepted |
| seq | 只有唯一合法槽位才读取；0 有效 | 不用序号间隔推丢包，也不用 seq 充当 source |
| Halt | 保留原函数，更新 Bridge revision，seq 为空 | 不声称引擎 Halt 自增全局 sequence；不提供自身 verified Halt |
| 批次 | 当前原生自身发布只允许 singleton | 核心多单位测试不等于游戏完整批次已接通 |

## 4. 为什么不能生产放行

仅对已观察存储范围建立 sidecar，不能证明每个自身命令必然经过所有被 Hook 的复制/消费/销毁入口。未观察的复制可能失去归属，未观察的回收/原地覆写可能留下错误标签。只“不猜成自己”还不足以保证旧自身命令不会作为 UNKNOWN 到达原函数。

同样，Host mutex 只串行化经过本宿主的入口，不能自动覆盖所有原生线程/异步副作用。函数调用后的成功返回不等于所有未来异步写入已受保护。

所以默认模块中的 `exact_source/verified_issue/release_approved` 保持 false。`physical_path_witnesses_ready` 仅是覆盖样本诊断。默认生产策略即使样本就绪也不允许 arm。实验构建使用独立显式开关，仅用于开发验证，安装器拒绝它。

## 5. 失败处理

自身发布元数据不能建立时，使用已核对的 writer abort flag 请求原生 finalize 回退；不能把 allocator 改为返回 NULL，不能跳入未执行 prologue 的 epilogue。若 abort flag 不能写入，则记录 indeterminate/fault 并停用后续自身发令，不宣称已零副作用回滚。

已归因自身命令过期、取消、重复消费时，核心拒绝且不调用原生执行入口。原函数已经开始后出现异常/重入，记录 INDETERMINATE；不谎称没有副作用。外部未归因入口保留原生行为。

这些原则在合成内存/原生 callback fixture 中验证；正式放行仍需要实际原生覆盖与执行证据。
