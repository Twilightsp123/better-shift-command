# Better Shift Command R45（本对话第 11 轮）— B2 packet 与 state16 缓存向量任务的对象身份排除

日期 2026-10-19。针对 **CA 原生 Shift 连续 MOVE 折返时同一兵牌成员相互穿插、挤压** 的原生 Windows x64 研究。本轮只读检查提供的新版 `Warhammer3.exe`，不再证明缺陷存在，不用 Lua 替代 Shift，不发布猜测性 Native gameplay patch。

## 1. EXE 身份与审计范围

- 用户新 EXE：232,531,920 字节、PE32+ x64、ImageBase `0x140000000`、SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`。本报告全部地址都是 **RVA**，绝不能沿用旧版 RVA 直接 Hook。
- `audit_r45_b2_state16_provenance_20261019.py` 对新文件直接执行：**107/107 完整原码和 GNU objdump 指令起点、12 个 PE unwind 函数、1 个无 unwind 叶函数、22/22 E8、6/6 控制转移、8/8 类型化虚表槽**；另对整个可执行代码段枚举 `0324DBAC` 与 `0306F594` 的直接 E8 调用者，并检查确实位于指令起点。
- 独立 `unittest`：新版真实 EXE **18/18 PASS**；未提供 EXE 时 **17 PASS / 1 SKIP**。这些仅是静态与合成辅助测试，不是新版 Shift 玩家运行时因果或修复测试。

## 2. B2 实际到成员接收器的直接链

```text
B2 逐成员发送 0326A994
  0326AAD9  CALL 0326F210（构造 packet）
                  → 02F648E4 初始化 packet+0x50
  0326ABA9  R8D=0
  0326ABAF  member virtual+0x368
                  ↓（普通成员的 03912950+0x368）
           03070A48 packet 接收器
```

`02F648E4` 将 `packet+0x50` 设成 `0x06 | (bit0) | (bit4)`；B2 另一路可额外 OR `0x08`，所以已验证的 **B2 构造路径 bit0x20 恒为 0**。不代表 mode helper 恒为某个值或直接标识玩家 Shift。

普通成员接收器存在**互斥**路径：

| 条件 | 当前这一次接收器操作 | 能否作为 R44 state16 直接安装证据 |
|---|---|---|
| helper==0 且 packet+0x50 bit0x20==0 | `03070A8D...03070AB3` 建立 `member+0x4A8` 的 inline packet 任务，`03070AB8` 直接跳到退出 | **不能**：此分支没有创建 `member+0x330` state16 task |
| helper!=0 或 packet bit0x20!=0 | 根据 member+0x104 选择虚表 +0x100/+0xE8，然后根据 packet+0x34 类型，先调用 `02DB5A20` 清理 `member+0x328`，再在 `member+0x330` 安装 packet action | **不能直接证明**：使用的是另外两个具体构造器，不是 R44 向量任务 |

由于 B2 bit0x20 固定清零，第一种还是第二种由 mode helper 决定；同一次玩家 Shift 实机的 helper 值并未测得。特殊派生成员可能通过 `03070A24` 转发至关联对象，未在本轮将其冒充普通成员。

## 3. 两类 packet action 与 R44 state16 是不同数据类型

**packet action:**

- packet kind 命中 `{9,10,12,14,15}`：`03070BF8 → 0324E2C8`，安装 `0x039199F8` 虚表。`+0x08=0325E824`，`+0x10=03263AF8`。
- 其它 kind：`03070C2D → 0324D994`，安装 `0x03919B28` 虚表。`+0x08=0325D9FC`，`+0x10=03261688`。
- 两个构造器都从任务输入读取 **一个 8-byte 值**写入 `task+0x38`，随后显式 `task+0x40` 字节置零；不能把它当作三个 float 的缓存运动向量。

**R44 缓存向量 state16 task:**

- 真正的成员方法是普通成员虚表 `0x03912950 +0x550 = 0x0306F594`。
- `0306F712` 将 `member+0x324` 设置成 **16**；满足相关检查后 `0306F733 → 0324DBAC`，在同一内嵌任务槽安装 **`0x03AE22D0`**。
- 这个构造器分别复制三个 32-bit float 至 `task+0x38/+0x3C/+0x40`；其 `+0x08=0325E4B4` 才在 `0325E50F/513/530/544` 将**创建时缓存的向量**与**执行时 `member+0x1E0` 当前目标**传给 `03065DB8`。
- 新 EXE 直接 E8 全节检查：`0324DBAC` 的唯一有效直接 E8 调用点是 `0306F733`；`0306F594` 没有直接 E8 调用者，作为成员虚方法可被**间接**调用。因此只能排除所审计 **B2 packet 接收器本次直接创建** state16 向量任务，不能排除后续事件、间接虚方法或其它游戏阶段安装它。

**修正前一轮潜在误读：** 即便两类对象复用 `member+0x330` 槽，`task+0x38` 的类型也不相同。**不能**从 B2 packet+0x38 直接推导 R44 的 `task+0x38` 老向量配新世界目标问题。并且接收器在 packet action 分支会先清理旧动作，但具体动作状态标志是否同时改变仍需按其清理器分支说明，不能自行填补。

## 4. 已建立更直接的 B2 → 成员状态恢复 → 积分分支

在两个 **packet action `virtual+0x10`** 中找到了受条件门槛限制的原生直接调用：

```text
packet 通用 action   03261688
  03261A77 / 03261CAB CALL 03081D40
packet 特殊 action   03263AF8
  03263D9F           CALL 03081D40
                            ↓（还受内部条件控制）
                     03081ED6 CALL 03164710
                        → 清 member+0x108 bit0x02/0x08
                     03081EDB OR member+0x155 bit0x04
```

`03164710` 中 `03164776 AND byte [member+0x108],0xF5` 会清 `0x02/0x08`，`031647B2 OR member+0x155,0x03`；上层 `03081EDB` 另恢复 bit0x04。`03081D40` 对该函数传入 **`&member+0x88` 自身当前位置**（R42 已验证），所以这里不该被误称为使用外部坐标使士兵“瞬移”。R42 的原码证明，后续 `03146FF0` 的不同 bit 条件决定是否直接消费积累的运动增量；**本轮没有证明这些增量在任何 Shift 实例中实际陈旧或冲突**。

相较于此前缓存向量任务，这条条件性 packet action 状态恢复与成员积分的连接距离更近；**仍须检查实际 queued MOVE 的发包/执行相位及输入，不可全局清位或禁止动作**。

## 5. 旁路核对与止损

- R44 的另一名已类型化写者 `member virtual+0x470 = 03071DC8` 经 `030728C1 → 03065DB8` 使用当前 member+0x1E0 和它本函数生成的向量。唯一已知**直接 E8** 调用处是 `02F4F1BA`，**不是 B2 sender 或本次 packet 接收器中的直接调用**。不把它强行声称是 Shift 的 B2 数据来源。
- 在三个已查看的 B2 成员接收/后续 action 函数中，没有直接指令调用 `member virtual+0x550`；不声称“整个程序完全不可能间接调用”。
- **假说 H45：“B2 packet 本次接收直接安装 R44 state16 缓存向量任务”——在固定 SHA 及已检查的直接分支中排除。**
- **未排除：** B2 action 的后续状态恢复、世界目标刷新与成员积分增量消费之间，可能存在一个不同步的实例。没有玩家 Shift 的同实例相位证据、没有空间邻兵冲突的因果证明。

## 6. 下一轮唯一优先方向

在 B2 action `03261688/03263AF8 → 03081D40 → 03164710 → 03146FF0` 上，验证 `03164710` 调用的状态清理/重置是否会清理 `member+0x13C/+0x140/+0x144` 的待积分增量，及这些标志在**下一次**真实积分入口前如何被重新设置。若确认有原生配套清理，就降低这条候选优先级，优先看成员 steering 的实际生成输出/成员世界目标。不要重复查 Group 对象池、R44 state16 类身份或玩家已确认的缺陷存在性。

## 7. 文件、完整性与 GitHub

- `maintenance_tools/native_shift_re/audit_r45_b2_state16_provenance_20261019.py`
- `maintenance_tools/native_shift_re/r45_b2_state16_provenance_pins_20261019.txt`
- `tests/test_native_shift_re_r45_b2_state16_provenance_20261019.py`
- `maintenance_tools/native_shift_re/evidence/20261019_r45_b2_state16_provenance_static.json`
- 只读反汇编摘录和单测日志；ZIP 同时打包前一轮 R44 原始资源包，不含任何游戏 EXE。
- 只维护研究分支 `research/n1-native-shift-behavior-patch-20261009`；**`main` 不修改**，不能将离线审计报告成 CI PASS 或玩家游戏内修复。

`gameplay_patch_authorized=false`。
