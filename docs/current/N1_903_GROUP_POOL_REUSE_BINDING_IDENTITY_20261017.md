# BSC 第30轮 — Group 对象池复用与 UnitRoot 当前 Group 绑定（2026-10-17）

基准：用户原始 Win64 Warhammer3.exe，SHA256 518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a，ImageBase 0x140000000。只读原码审计 **120/120 完整原始指令和 objdump 起点、21/21 E8、11/11 个同函数内的 Group 指针写点 PASS**；本地 15/15 回归 PASS（包括真正原始 EXE），无 EXE 时 14 PASS + 1 SKIP。没有 Windows 运行时命中，也没有 gameplay patch。

## 一、已证明原生 Group 对象池确实回收并复用

- 0x0301B834 从池 owner+0x58 获取空闲链头。0x0301B874 读取头指针，0x0301B8A8 读取旧头的 next，0x0301B8B0 推进 owner+0x58。池为空时 0x0301B881/886 经分配入口补充对象。返回的 Group 指针可再分配到另一个逻辑生命周期。
- 0x030197A8 遍历 Group 容器，通过 0x030197E0 调 0x0302C2D4。后者在对象 virtual+0x10 清理后，0x0302C2F2 将旧链头写入被归还对象，0x0302C2F5 将它重新放在 free-list 头。真正存在 checkout→return→recheckout 的原生循环。
- 因此同一裸指针地址不保证同一个 Group 生命周期。这里只证明可复用机制，不代表用户 Shift 折返已经出现地址复用。

## 二、UnitRoot+0x32F8 并不是单调的 Group 代际编号

- 0x03007CE8 初始化 UnitRoot+0x32F8 为 NULL；0x0301B96D 将新 Group 绑定到 UnitRoot+0x32F8。
- 0x0301DC0C 中同一 RSI=UnitRoot 有 11 条向 +0x32F8 写入 QWORD 的原生指令：0301DC59、0301DC8E、0301DCC6、0301DCF0、0301DD1A、0301DD49、0301DE7D、0301E0E7、0301E197、0301E1EA、0301E205。它们来自不同条件分支，不能断言一次调用11条全执行。
- 0x03039D9C 保存旧指针，再调用 0x0301DC0C 更新；然后验证新指针及 group+0xA18，需要时通过 UnitRoot+0x3298 数组首项重新绑定。数组计数在 +0x3294。
- 0x0303BB60 条件拆除时清零 UnitRoot+0x32F8，再调用 0x03039D9C 重建。
- 因此 root 当前 Group 的绑定修订版本和池对象 checkout 生命周期是不同身份。只对比同一指针或只在一个分支钩选 +0x32F8，都会漏掉部分真实状态变动；本轮没有证明覆盖全游戏的全部间接写者。

## 三、提供可验证的离线事件回放

新增 group_pool_binding_replay_20261017.py，只读取匿名 checkout、return、bind、clear、snapshot 的 JSONL；同地址归还后再取出会增加对象 checkout incarnation，存活对象的重新绑定仅更改 root binding revision。没有配套 checkout 的绑定返回 UNKNOWN；禁止原始裸指针。输出明确 full_event_coverage_proven=false、patch_authorized=false。合成回放绝非真实游戏日志。

## 四、下一步与约束

目前还需证明 Group 池事件完全覆盖、MOVE 和 member 的独立构造/回收代际、对象有效性、线程/重入安全以及群组快照时相。0x0301DC0C 中间是可能更换绑定的窗口，不得视为原子屏障。没有这些条件就不能向玩家交付实时采样 Hook，更不能宣布 Shift 挤压根因或制作会损坏 CA 队列、渐进转弯、避障、RMB 和 Shift ATTACK 的全局补丁。

文件：maintenance_tools/native_shift_re/group_pool_lifecycle_pins_20261017.txt、audit_group_pool_identity_20261017.py、group_pool_binding_replay_20261017.py、tests/test_native_shift_re_group_pool_identity_20261017.py。完整本地资源包 BSC_R30_GROUP_POOL_IDENTITY_AUDIT_20261017.zip 不含 EXE 或指针日志。只维护 research/n1-native-shift-behavior-patch-20261009，main 不修改。
