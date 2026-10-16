# BSC N1 第28轮：direct-call 反证与首次差异离线分析（2026-10-16）

固定原始 Win64 Warhammer3.exe SHA256：518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a；所有函数地址均为 RVA。本轮仍未找到 Shift 折返时邻兵相互穿插的根因；禁止发布或声称已有 gameplay patch。

## 一、直接边界，而非凭同一虚表猜根因

在原始 EXE 上按 PE unwind 函数和 objdump 真正指令起点审计：成员 vtable 0x0390D4F8 的 +0x368=0x0306B9F0 为 B packet 接收器；+0x128/+0x130/+0x138 为动作标志写者；+0x538/+0x550 为状态4/16写者。

接收器完整函数共有13处 call，包括成员 virtual+0x100 与 virtual+0xE8，但没有直接 E8 调用上述五个状态写者。全可执行节真实 E8 调用者清单：0x0306B9F0 只有 0x02F4F900；0x0306A100 只有 0x03117226；0x03117214 以及另四个状态方法没有直接 E8 入口。**绝不能将“没有直接 E8”解释成不存在间接虚调用、回调或异步动作连接。**

本轮原始 EXE 审计通过17条指令起点与字节、6个同类型虚表槽、7个函数的真实直接调用入口清单。代码：maintenance_tools/native_shift_re/audit_packet_state_entry_gap_20261016.py。

## 二、修正旧归档的跨会话 skip 问题

第26轮离线 ZIP 把原始 EXE 路径写死在旧目录 /mnt/data/bsc_r25/private/Warhammer3.exe。当前环境直接重跑仅17 PASS/1 SKIP；随后已用重新解压并验证 SHA 的原始 EXE 单独重新核验第26轮 audit，142/142机器码、15/15 E8、14/14分支、5/5虚表槽 PASS。本轮新增测试改用可选环境变量 WH3_903_EXE，避免把 SKIP 误报为 PASS。

## 三、离线首次差异分析器

新增 maintenance_tools/native_shift_re/causal_first_difference_20261016.py。它**不接入游戏、不 Hook、不访问进程内存**；仅分析将来已验证代际且去除原始地址的 JSONL。只对同一 trace_id/unit_epoch/move_epoch/tick 的相邻两 member_index 配对，按 group_epoch、packet_route_epoch、frame_epoch、world_target_direction、tick_dispatch、motion_direction 的顺序报告最早**已记录**差异。

两个士兵的阵型目标、局部转向和速度可能合法地不同；输出恒定 root_cause_proven=false、patch_authorized=false。缺某阶段明确列 not_observed_stages；没有同 Tick 两邻兵时返回 INSUFFICIENT_ADJACENT_SAME_TICK_EVIDENCE；拒绝原始指针样式、无穷坐标、错误 schema、超量输入。合成测试不是玩家实机日志。

独立交付包 BSC_R28_FIRST_DIFFERENCE_REPLAY_20261016.zip 的两套本地脚本总计29/29 unittest PASS（包含1项固定原始 EXE 审计）。GitHub 中有同逻辑源码与17个测试定义；远端 CI 是否运行仍需单独核实。

## 四、下一步决定性缺口

静态函数与虚表不能证明真实 queued Shift 后继 MOVE 的同一兵牌、两邻兵、同一 Tick 命中了哪条分支。必须先离线审计有界只读采样的对象有效性、单调任务/Group 代际、防 ABA、采样时序和性能，然后才能把同一 MOVE 的 packet、goal、world-frame、member Tick 联系起来；真实速度输出写者尚未锁定，不能填造 output_velocity。尚不要求玩家进游戏重证已确认缺陷。

只维护 research/n1-native-shift-behavior-patch-20261009，不改 main；不上传游戏 EXE 或原始进程指针。原生队列、渐进转向、避障、普通 RMB MOVE 和 Shift ATTACK 必须保留。
