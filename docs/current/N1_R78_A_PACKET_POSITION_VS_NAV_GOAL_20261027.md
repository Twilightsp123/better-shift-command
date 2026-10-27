# R78 — 当前 EXE A 类阵型 Packet 不等同于已证的最终导航路点

日期：2026-10-27。玩家要修复的是同兵牌内成员群体运动挤压，不是寻找名为挤压的原生动作。原始 WH3 Win64 EXE SHA256 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496，大小 232531920，ImageBase 0x140000000，以下均 RVA。仅原始 EXE 静态审计与合成反例，没有实机游戏内观测或补丁。

## 关键正证据：A 阵型数据经过个体修正，最终可更新成员物理位置

1. A fanout 0x030DA51C 的 member[i]→record[i] 等索引配对仍成立（R77）。0x030DA577 把 Win64 栈上的第五实参置 1；0x030DA588 调 0x02F64870 构造 Packet，0x030DA59B 向具体 member 虚表 +0x368 发包。记录坐标及参考对象被复制，但这本身没有证明导航曲线路径。
2. Packet 构造器 0x02F648C5 将 Packet+0x50 设为 0x26（含 bit0x20），0x02F648A5 先清 Packet+0x51 bit0x02；其自身 push RBX、sub RSP,0x20 后以 [RSP+0x50] 读取上述第五实参 1，0x02F648D5 因而调用 0x02F775AC。0x02F775B2 将 Packet+0x51 bit0x02 重新设置，并在另一位允许时经 0x02F775CE→0x030844C8 条件性执行 member+0x2E8/+0x984 朝向修正。禁止因中途清位就误判 A 没有个体修正。
3. 成员接收器 0x03070A48 根据 Packet+0x50 bit0x20 及 +0x51 bit0x02 决定流程。对上述 A Packet，它进入虚方法路径且在 0x03070ACD→0x03084618 产生个体位置/参考修正，随后 0x03070B54 或 0x03070B6F→0x0312214C 对带参考框架的数据求世界坐标；其引用非空时进一步 0x03122160→0x02F3D668 变换。
4. 当前普通成员虚表 0x03912950 的 +0x368=0x03070A48、+0x100=0x030785AC、+0xE8=0x03078268。接收器依据该 member 的 +0x104 模式 1/2 或其它选择后两者。+0x100→0x0316460C 在 0x03164658/6A **直接写 member+0x88/+0x90 物理 XYZ**；+0xE8→0x03163DC4 在满足进一步分支时，于 0x0316443D/53 和 0x0316446B 写该成员实际 XYZ、更新位置状态/朝向。

## 明确纠正旧假说

R77 的等索引下发是原生事实，但不能升级为 A record[i] 是普通 Shift 中成员的最终持久导航目标。真正的持久导航记录由另一个已类型化函数 0x0311E5DC 写 member+0x1E0/+0x1F0；当前 A bounded direct chain 证明了物理位置同步写入，但没有证明它与那套导航目标同一对象或同一 MOVE 任务代际。也不排除未穷尽的虚调用副作用。不能据此设计固定 slot remapping、速度/转弯阈值补丁。

## 实际分支与限制

原生 0x0327ECA4 在 0x0327ECC6 调 0x02DC7E30 作环境模式判断；结果区分 0x0327ED17 A 分发与 0x0327ED3C B 分发。这不是对玩家原生 Shift 是否实际命中 A 的动态证明。R37/R38 的 B2 位置包也不能反过来作为普通 Shift 的逐帧导航目标。

## 离线验证与交接

在匹配原始 EXE 本地验证 118/118 条真实原码与 LLVM objdump 指令起点，16/16 E8，11/11 PE unwind 范围，3/3 普通成员虚表槽；36/36 Python 测试通过（其中2项真实 EXE/反汇编）。公开 GitHub 上附 SHA fail-closed 精简焦点 39 pin、12 E8、10 个 PE 边界、3 虚表及对应测试，私有 EXE 用例须 SKIP。完整离线包 BSC_R78_A_PACKET_POSITION_VS_NAVIGATION_GOAL_20261027.zip（含前轮 R77），不含商业游戏 EXE。

R79 唯一主线：审计 0x0311E5DC 导航 goal setter 的真实原生调用者与源数据，优先将其和 original queued Shift MOVE 同一任务身份连接，而不是继续在 A 的物理位置 Packet 上猜 waypoint。若仍没有同实例归属，就明确 UNKNOWN，不能要求玩家再证明挤压。

root_cause_proven=false; actual_shift_A_hit=false; A_record_is_persistent_goal_proven=false; live_hook_authorized=false; gameplay_patch_authorized=false; main_unchanged=true.