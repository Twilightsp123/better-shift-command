# BSC N1 第31轮：Group 重建期间的旧绑定与新对象生存代际（2026-10-17）

## 重大方法纠正

固定原始 `Warhammer3.exe` SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，ImageBase `0x140000000`。**72/72 原字节及 GNU objdump 指令起点、15/15 E8、4/4 真实直接调用者；20/20 本地回归 PASS（含私有原始 EXE），无 EXE 时19 PASS/1 SKIP。** 没有游戏动态命中或 gameplay patch。

第30轮回放器 `group_pool_binding_replay_20261017.py` 过于严格：它遇到「Root 当前绑定仍指向某 Group，而该 Group 被 return」就无条件抛错。但是原生 **`0x0301B8E4`** 的完整函数证明以下顺序：

1. `0x0301B902 CALL 0x030197A8`：清退当前 Group 容器；它会经 `0x030197E0→0x0302C2D4` 将对象归还池，`0x0302C2F2/F5` 按空闲链 LIFO 压回。
2. `0x0301B91F CALL 0x0301B834`：从**同一个池**重新 checkout；`0x0301B874/B0` 取出并推进池空闲链头，可能立即复用刚归还的对象地址。
3. `0x0301B946` 逐成员挂到新 Group，`0x0301B968` 做初始化。
4. **直到 `0x0301B96D` 才直接执行 `MOV [UnitRoot+0x32F8],RBX`。** 对这个完整 unwind 函数反汇编没有更早的同根直接写 `[RSI+0x32F8]`。

因此 **Root 的旧 Group 引用可能在重建调用中暂时指向已退役的生命周期**；如果刚归还对象又被取出，前后同地址可能对应不同 incarnation。**但不能宣称已经证明有真实的野指针解引用、并发访问或内存破坏**：被调函数及虚方法的间接副作用/其它线程没有全面排除，而且尚未在玩家的 queued Shift 实例观察到这个分支。

原始 `0x0301B8E4` 的全部4个真实 E8 调用点：`0x0301A284`、`0x030200EF`、`0x0302DB8E`、`0x0303DCFF`。其中 `0x0302DB44` 是此前确认的即时 Group 构造路径，**不能据此直接把它归为玩家 Shift 队列的激活行为**。

## 本轮修正代际模型

新增 **`group_rebuild_transaction_replay_20261017.py`**（纯离线）使用有界 `rebuild_begin`/ `rebuild_end` 范围：

- 在一个明确的重建范围内，旧组归还但 Root 仍绑定可以出现，标记 `root_pointer_stale_during_transaction=true`，**拒绝把中途快照当作稳定采样**。
- 同一对象别名按真实 `return→checkout` 增加 pool checkout incarnation，即使指针字节不变；`bind` 更新 root binding revision。
- 重建范围结束仍保留旧代绑定，fail-closed；范围之外的 return-with-binding 标记为**作用域不足／需要核实**，不宣称 CA 不可能这样做。
- 一次 live Group 重绑定只增加 binding revision，而不应创造新的 checkout generation。
- 未观察 checkout、重入、丢事件、线程/原子性未知时保留 UNKNOWN；合成快照不是游戏原子屏障。始终 `root_cause_proven=false` 和 `native_patch_authorized=false`。

回归包含「先 return 后同地址立即 checkout，无中间 clear」、「重建中 snapshot」、「同 incarnation 重绑定」、「缺少入口/结尾」、「错误原始版本」、「不覆盖原始 EXE」。新增 20 项回归的本地完整结果全部 PASS。

**本轮解决了采样数据身份模型的反例，不是已定位兵牌士兵穿插的根因。** 后续只应考虑完整 Group 生命周期事件、MOVE 后继槽与成员 Tick 的同一实例绑定；若静态无法证明跨成员的稳定时窗，就不能基于 Root 指针相等推断目标一致。玩家已确认的 Shift 连续 MOVE 折返缺陷无需再次证明。

## 代码与安全

- `maintenance_tools/native_shift_re/group_rebuild_transition_pins_20261017.txt`（72精确字节）
- `maintenance_tools/native_shift_re/audit_group_rebuild_transition_20261017.py`（SHA、PE/unwind、E8所有4个 caller、LIFO和真实直接写入时序）
- `maintenance_tools/native_shift_re/group_rebuild_transaction_replay_20261017.py`（修订的合成事件模型）
- `tests/test_native_shift_re_group_rebuild_transition_20261017.py`（20项定义，原始 EXE CI skip）
- 完整独立资源包 `BSC_R31_NONATOMIC_GROUP_REBUILD_20261017.zip`，包含前轮归档、审计和测试；不含游戏 EXE/用户指针。

**不更新 main，不修改游戏，不删除 CA 原生队列、渐进转弯、寻路、避障或 Shift ATTACK。** 当前状态：`native_patch_authorized=false`。
