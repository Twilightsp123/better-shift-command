# BSC R73：shortTask → B2 → 成员 roster 的条件性身份链（2026-10-24）

**只读 EXE 静态研究 + 离线合成反例，不是 Shift 根因确认、不是安全 Hook、不是 gameplay patch。**

## 输入/验证
当前玩家提供的 Win64 `Warhammer3.exe`：完整 SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`，大小 232531920，PE ImageBase `0x140000000`；下面地址都是 RVA。本地按 GNU objdump 真正指令起点复核 **40/40 指令、7/7 E8**，完整本地校验器与 17/17 unittest（含真实 EXE 一项）PASS；公开 CI 无 EXE 会 SKIP。完整局部反汇编、报告、SHA Manifest、R72 历史另存独立 ZIP，不在 GitHub 上传播商业 EXE。

## 新增的有限数据链
- `0x02F31791` 将 `UnitRoot` 记在 `shortTask+0x08`；`0x02F5B3F0/3F9` 在某回调分支从 Root 重新取得此时的 Group，`0x02F5B400` 可以分派 A。**A 与以下 B 路径不是同一调用栈上的必然连续两次发送。**
- 另一分支 `0x02F5B475 → 0x02F54510`；`0x02F545DA` 条件构造路线 node，`0x02F545FF` 读取 node+0x70，`0x02F54621` 再从 Root 取得**执行时** Group，并在 `0x02F54628` 调 `0x0327ED4C` B 分派。
- 在满足分派门槛时，`0x0327EDD5` 构造 B2 `0x03268D34` 并通过 `0x03268D80` 保存路线至 B2+0x60。后来两个**条件性且不是必同时**的直接发包入口 `0x032769F2` 与 `0x03286445` 均调用 `0x0326A994`。不能说 B2 创建就意味着已发送。
- `0x0326A994` 内 `0x0326A9C4` 把本次 Group（RDX）保存到 RSI。**函数并不逐成员重查 UnitRoot+0x32F8**，但其循环**没有冻结 Group roster**：`0x0326AA38` 读取 Group+0x24 数量，`0x0326AA44` 在循环头再次读取 Group+0x28 数组指针，`0x0326AA4B` 读索引成员，`0x0326ABAF` 经成员 vtable+0x368 发包，`0x0326ABBD` 在循环尾再次读取 Group+0x24 数量。旧研究 R35 的“Group 指针不逐成员重取”与本轮“Group 内数组与计数逐次读取”均成立，不能混淆。

这是一个应当明确记录的**数据一致性条件**，但不是证明存在并发写入或实际错代。合成反例 `(11,22)→(11,99)` 可产生混合成员流，仅演示这段代码如果在相关时点发生 roster 改变的可能效果，不是玩家游戏实测。

## 遗留阻断
`same_shift_instance_proven=false`；`roster_mutated_during_sender_proven=false`；`group_generation_proven=false`；`root_cause_proven=false`；`live_hook_authorized=false`；`gameplay_patch_authorized=false`。

下一轮 R74 只审计**当前 EXE 的 Group+0x24/+0x28 同对象写入与线程/生命周期**，确定是否存在 B2 sender 可能同时观察的变动；无法证明就下调假说优先级，回到 Steering 与物理运动差异，不再继续凭新 RVA 维持进度。
