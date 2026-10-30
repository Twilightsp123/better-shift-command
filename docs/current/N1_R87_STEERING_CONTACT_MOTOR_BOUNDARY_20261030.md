# BSC R87 — Steering 邻兵接触与实际成员位移之间的数据流边界（2026-10-30）

**本轮目标：**研究 CA 原生 Shift 连续 MOVE 时单兵牌内士兵的空间穿插/挤压，而不是寻找名叫挤压的动作。用户已实测确认游戏缺陷，无需重复证明。没有安装游戏 Hook、修改 EXE 或开发可玩补丁。

**EXE 身份：**Warhammer3.exe 232531920 字节，SHA256 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496，PE ImageBase 0x140000000；地址均为 RVA。本地真实 EXE 静态核验 **128/128 完整原始机器码 + LLVM 指令起点、8/8 E8、15/15 Jcc、5/5 PE unwind；43/43 local tests PASS**（含真实 EXE）。公开 GitHub 维护 76 focus pins/6 E8/11 Jcc/5 函数及测试。

## 1. 积分器自身会修正 pending motion

函数 0x03146FF0 在 0x03147019 保存 RCX=member 到 RBX。在受数值与角度条件保护的路径中，依据自身当前朝向虚方法+0xC8、角度字段 +0x148 和局部运动分量 +0x14C/+0x150，于 0x03147189/91 读取已有 X/Z pending，0x03147199/A1 写回成员 +0x13C/+0x144。

在另一条状态/模式门槛下，0x031473A7 检查 member+0x108 bit0x04，0x031473B0/BC 检查动作模式；0x03147440/4D/55 对已有 pending Y/X/Z 累加运动分量，0x0314745D/65/6D 写回 member+0x140/+0x13C/+0x144。单独的允许分支 0x0314720B/23/3B 将 pending 用于实际物理 XYZ member+0x88/+0x8C/+0x90，并更新运动速度状态 +0xE0/+0xE8。

**正结论：**pending 的变化有成员自身朝向/运动积分的真实原生来源，不能自动将其归咎于邻兵事件。**限制：**分支有条件，不能说它们每帧连续发生，更不能宣称这些正常成员位移计算就是玩家 Shift 挤压的错误根因。

## 2. Steering 邻兵接触并非已证直接位移写入

0x03059BC8 进入时 RDI=当前 member。邻兵候选经过关联对象+0x80、优先级+0x74、位置+0x88/+0x90、速度+0xE0/+0xE8 等筛选；0x03059F47/4E 比较关联指针，0x03059F64/6A 选择 RSI 候选。**没有证据将这些候选一律类型化为同一兵牌/同一 UnitRoot**。0x0305A5D4..0x0305A623 中的虚调用还可能更换后续 RDI 所指对象，不应无条件认定接触回调中的 RCX 仍是入参 member。

Steering 在 0x0305A7C1 传 R8=RSI，0x0305A7C9 传当时的 RDI，0x0305A800 E8→0x03085114。接收器打包两个成员身份、优先级、坐标与条件标志；0x0308529D 取得某输入对象的 +0x1D8 子结构，0x030852A7 通过该结构的 vtable +0x10 **交付局部成对接触记录**。已定界的这个直接函数没有将 pending +0x13C/+0x140/+0x144 或实际 XYZ +0x88/+0x8C/+0x90 写回成员。

**否定边界：**该虚表接收者的内部副作用尚未闭合，不能从“这个函数无直接运动写入”跳到“接触响应绝不影响后续运动”。但把 0x03085114 当成已经证明的物理避障力写者，同样没有原码依据。

## 3. Steering 后续函数有独立条件，非通用积分阶段

member Tick 的条件性链 0x03087349→0x03059BC8、0x03087351→0x0308D830。后一个函数在 0x0308D839/857 检查成员 +0x30/+0x2E8 均非空，0x0308D865..871 要求 member+0x26C 为 0x78 或 0x79，后续还有附加虚方法检查、随机条件。通过才于 0x0308DA23 将 &member+0x1E0 传给 0x0308DA71→0x03065DB8。

这是一条条件性的成员目标相关辅助路径，并没有证明每个正常 Shift MOVE Tick 都走该路径，也不能仅凭传目标地址就断言必定修改了导航目的地。

## 4. 因果分叉、复验与下一步

R87 将此前容易混淆的过程拆为：**邻兵筛选/接触虚交付 → 成员自身 heading 或速度生成 pending → 受控物理 XYZ 累积**。目前只证明每层机制和限定原码，不证明同一次 Shift 中接触记录直接输入积分器或造成群体挤压。继续沿 R86 同时刻空间间距与世界目标诊断，不用路径静态交叉推测碰撞。

R88 限定沿 0x030852A7 的单个有类型 vtable 接收器核查是否存在同成员对象、同目标代际的直接 pending/XYZ 写入边；追不到则止损。禁止盲改所有 RMB 共用积分器、强制转向和替换 CA Shift 队列。

本地完整归档 BSC_R87_STEERING_CONTACT_TO_MOTOR_BOUNDARY_20261030.zip 含 128 原码 pin、五段原始反汇编、43 项测试及日志、SHA256 清单和 R86 完整历史 ZIP。没有分发游戏 EXE。

root_cause_proven=false; contact_direct_motor_link_proven=false; integrator_self_pending_sources_proven=true; game_hook_authorized=false; gameplay_patch_authorized=false; main_unchanged=true.
