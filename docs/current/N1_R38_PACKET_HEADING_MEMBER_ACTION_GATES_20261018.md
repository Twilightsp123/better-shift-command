# BSC Native R38（本对话第4轮）—— B2 packet 固定位、逐成员朝向修正与不同动作 Tick 的真实边界

日期 2026-10-18。研究 EXE 是用户当前上传的 `Warhammer3.exe`（Windows x64），**SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`**，大小 `232531920` bytes，ImageBase `0x140000000`。**所有地址均为 RVA。** 研究针对 CA 原生 Shift 连续 MOVE 折返时兵牌内部成员穿插挤压；不重复要求用户证明缺陷，不开发 Lua 替代。此轮仅静态、只读，未进行游戏实机 Hook/修复。旧 SHA 和旧 RVA 不适用于本轮。

## 本轮最重要的已证数据边

```
 B2 sender 0x0326A994
   ├─ 0x0326AAD9 -> 0x0326F210 -> 0x02F648E4
   │      packet+0x50 = 0x06 | (input_b0 & 1) | ((input_b4 & 1)<<4)
   │      optional: OR 0x08; sender 0x0326AB21..2F only replaces bit 0x40
   │      therefore verified B2 packet +0x50 bit0x20 always clear
   ├─ 0x0326AB19 -> 0x02F775AC
   │      OR packet+0x51 bit 0x02
   │      packet+0x50 bit 0x02 already set, so 0x02F775CE -> 0x030844C8
   │      member-specific heading compensation, if eligibility conditions permit
   └─ 0x0326ABAF -> member vtable+0x368 = 0x03070A48
          ├─ helper=0 and packet+0x50 bit0x20=0 -> member+0x4A8 inline task
          └─ helper !=0 -> packet+0x51 bit0x02 -> 0x03084618 member-relative target
                ├─ member+0x104 in {1,2} -> +0x100=0x030785AC -> 0x0316460C
                └─ other member+0x104 -> +0xE8=0x03078268 -> 0x03163DC4
                └─ packet kind+0x34 -> member+0x330 action task implementation
```

上面是已经在新版机器码中核验的**条件性**路径，不代表任何特定 Shift 实机实例全部命中。它证明 B2 packet 自身的 `+0x50 bit0x20` 不是每名士兵选择 inline / virtual 的差异源；**不能据此删除引擎模式判断**，也不能推断所有同 Group 成员 mode helper 必定相同（此处尚缺同实例所有者核对）。

## 真正的逐成员差异生成位置：0x030844C8

`0x02F648E4` 先由外部 16-bit heading 设置 `packet+0x40`。在同一 B2 sender 里，`0x02F775AC` 检查 `packet+0x50 bit0x02`（此构造器保证该 bit 为 1），然后调用 `0x030844C8`，**可能把该字段替换为成员独立调整的朝向**。

原码 `0x030844C8`：

- `member+0x2E8` 为 NULL → 原 heading 不变。
- 非 NULL、且 `[member+0x2E8]+0x36CC` 为非零 → 增量为 0，原 heading 不变。
- 上述指针存在、且该字段为零 → 读取 `member+0x984` 的单精度数；使用常数 `0.5f`、比例 `0x4000`，经 `0x004EDA50` 原生数值→朝向转换后，对输入 16-bit heading 执行 16-bit 加法。

形式上对应 `angle_in + NativeConvert(16384 * (member+0x984 - 0.5f))`。这是**有条件的局部角度调整**，不是“CA 发生错误转向”的因果证明。尤其不能把 16-bit encoded heading 直接等同无条件世界角度（单位/转换器仍需以 CA 真机为准）。

## member+0x984 的类型化写入来源：成员初始化，暂不是 Shift 路点计数

`0x03052BA8` 是成员构建函数，`0x03052D20/34` 安装真实成员 vtable `0x03912950`；该表的 `+0x368=0x03070A48`，`+0x100=0x030785AC`，`+0xE8=0x03078268` 均经用户新版 EXE `.rdata` 核验。

`0x030532BE` 写 `member+0x984`，值来自两种条件初始化：

- 若关联 Group 控制记录 `Group+0x8F0 != NULL`，从同 Group 的 `+0x90C` 取 32-bit float。
- 否则执行基于成员所属 context 的 `context+0x90` 线性随机数更新，生成标量并加原生常数（此处 `0x3922A80=0.15f`）。

一项保守的静态 0x984 显式指令扫描，在新版 EXE 可执行节中识别 23 个 `+0x984` 引用，其中这处是已类型化成员写点；另一个 `0x02E0DEAF` 对 `+0x984` 写 float 发生于另一数据对象函数，**不能因为偏移相同当成成员写者**。该扫描不覆盖别名、向量宽写入或间接 setter，所以**仍不能证明 Shift 运行中从未重写该字段**。当前没有证据支持“它是 Shift 路点 epoch”或“它在折返时发生错误更新”。

## 本轮下游动作分支核验

- 接收器 `0x03070A48` 的 immediate virtual 分支（helper!=0）在 `0x03070B2F` 读取各成员自身的 `member+0x104`。`1/2` 与其它状态通向不同位置更新实现；这本身不证明非法异步。
- Packet 的 kind 是 `packet+0x34`，接收器的 `0xD600` 位集合对应 `{9,10,12,14,15}`。命中时创建一类 `member+0x330` 内嵌 action，vtable `0x039199F8`，`+0x10=0x03263AF8`；其它 kind 创建 vtable `0x03919B28`，`+0x10=0x03261688`。**不同 action 实现是真实的，不是同一动作标签的两种叫法**。
- 成员主 Tick `0x03086F04` 下游 `0x030872CD/DA/DF`：`member+0x108 bit0x04=1` 且 `state+0x324∈{4,16}` 时，`0x0308731B → 0x03085F9C` 条件执行 `member+0x328` 内嵌动作，此次不调用邻近 steering；反之相关条件下 `0x03087349 → 0x03059BC8`。`0x03085F9C` 的 RCX 是 **&member+0x328**，其 `+0x154` 检测的是 **member+0x47C**，切勿错标成 member+0x154；它再通过 `&member+0x330` 动作对象 `virtual+0x08/+0x10` 更新。
- 因此**同一 B2 sender 调用完成 ≠ 同兵牌同一帧原子更新**。本轮仍缺真实相邻成员运动输出的同实例关联及速度/位移最终写者。

## 本轮排除与停止条件

**已降低优先级：** “B2 为不同士兵随机设置 packet+0x50 bit0x20 导致不同接收路径”；原生 packet 构造及本 sender 的有关写者不支持此说。**不可打这个 bit 的全局修复。**

**值得以后按需追踪：** 原生分组投影输入相同但逐兵 heading 补偿不同，是否会导致不合理的实际世界目标/运动分流。须先取得同一次真实 Shift 后继 MOVE 的 member 目标、行动分支、实际物理运动写者；该补偿本身可能是 CA 有意设置的散开/阵型行为，不能盲目删除。

**下一轮只有一个主要方向：** 不再拓展 B1/B2/B3 类型树、也不继续纯粹验证 `0x984` 是否有另一存取点；优先把已命中的 `0x03059BC8` 邻近 steering 调用链连到**真实类型化的成员运动输出写者**，形成「world goal 正常还是 motion response 错误」可否证边界。若静态找不到速度提交点，应如实停止相应假说，不用无意义的字节计数替代根因。

## 文件、验证与 GitHub 边界

- `maintenance_tools/native_shift_re/audit_r38_packet_heading_motion_20261018.py` 和精确固定 SHA 的 259 条机器码 `r38_packet_heading_motion_pins_20261018.txt`：用户新版 EXE 实际审计 **259/259 真正指令起点与字节、23/23 E8、9/9 跳转、7/7 类型化虚表槽**；13 个具有 PE unwind 的函数跨度、一个无 unwind 叶函数范围，以及以上类型/条件代码检查。
- `tests/test_native_shift_re_r38_packet_heading_motion_20261018.py`：17/17 本地回归（含真实新版 EXE）；不提供 EXE 的环境 16 PASS / 1 SKIP。
- `maintenance_tools/native_shift_re/evidence/20261018_r38_packet_heading_motion_static.json`：仅真实 EXE 的静态审计结果；测试和代码片段在完整 ZIP 中。
- 审计器只读 EXE；源数据绝不公开上传游戏 EXE / 运行时指针；`main` 不改；无 native gameplay patch。

`shift_crowding_root_cause_proven=false`, `native_gameplay_patch_authorized=false`。
