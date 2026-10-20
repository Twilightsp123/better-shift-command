# BSC R46（本对话第13轮）— 对用户提供的 memreader Plus 与 Derpy .pack 的实际只读审计

> 2026-10-20。**本报告取代上一轮仅依据公开页面推断的 Derpy 未审读状态。** 本轮实际解析了两个用户上传的 PFH5 .pack 文件、memreader 0.13.0 Lua loader 与 Derpy `platform.lua` / `move.lua` / `main.lua`，并再次用用户新上传游戏 EXE 的完整 SHA 和真实机器码核验。**未运行 DLL/Hook、未修改 EXE、未作实机动态测试或 gameplay patch。**

## 1. 来源确切身份

| 来源 | .pack SHA256 | PFH5 文件数 |
|---|---|---:|
| `memreader_plus.pack` | `9e63d8feacb92c0b35ec327884bda558fe453dbdba945ee9d9c848deec1f7878` | 15 |
| `derpy_third_person.pack` | `a40d086d57f8d4857caff782680b62f490cf5e9d772723c9b50f69bee9e32176` | 27 |

memreader Plus 内的发行标记为 `0_13_0`（0.13.0）；其 `bin.lua` 嵌入 Windows AMD64 DLL 的 Lua 字节字符串，`loader.lua` 将字节保存为 `twwh3-memreader_plus.dll` 并 `require` 加载。本轮仅按 Lua 转义规则静态解码该载荷，验证 PE 为 AMD64、231936 字节、SHA256 `e26d0e2ff665f2611e94e13a7566653ea7e3791db6b945f1f191577bc83a491b`。**未执行或安全认证该二进制。**

## 2. Derpy 与 BSC 同版的实证

Derpy `script/derpy_tp/platform.lua` 存在 `BUILDS["6acec6f4"]`，其中 `update=0x03086F04`，`queued_gate=0x03087378`。用户新版游戏 EXE 的 SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496` 与前轮 BSC 一致，PE TimeDateStamp **`0x6ACEC6F4`（2026-10-14 00:04:04 UTC）**。直接从游戏 EXE 原码核对：

- `0x03086F04` 起始 **7/7 原始字节**与 Derpy `CAVE_SITE` 完全相同；
- `0x03087378` 原始分支 **18/18 字节**与 Derpy `GATE` 的预期值一致；
- 普通 member 虚表 `0x03912950+0x18` 的真实 QWORD 指向 `ImageBase+0x03086F04`，与 BSC R41 定型一致。

Gate 的短跳位移在 Derpy 控制期间由 `0x5C` 改为 `0x52`，分支目标从 `0x030873E6` 改为 `0x030873DC`。这是排队**单兵动画动作**在 member Tick 内的优先级调整，**不是 CA 原生 Shift MOVE 队列修复**。

Derpy 虽标注 Vanilla 9.X.X，但只对两种 PE 时间戳建立完整 steering 地址配置；未知 build 的模式扫描用于动画命令，不保证单兵 steering 可用。

## 3. 对 BSC 最有价值：已实现 BattleUnit→member 数组桥

Derpy `P.models(unit)`：
`mr.ud_topointer(unit) → [userdata+0x08] → native unit object`；`unit+0xA4` 是在场成员数量、`unit+0xA8` 是成员指针数组；member `+0x88/+0x8C/+0x90` 为 XYZ。其 `P.check_men` 再核对 CA Lua 的存活人数、member vtable 是否属于游戏镜像、坐标是否符合单位位置。

**注意 Derpy 的 native unit object 尚未证明与 BSC `UnitRoot` 指针类型相同**。不能从前者擅自读取 `+0x32F8` 当作 Group；成员数组下标不代表空间邻近，逐成员读取也非原子快照。BSC R41–R45 的 `member+0x108`、`+0x13C/+0x140/+0x144`、`+0x1E0/+0x1F0` 可以作为接下来有界只读观测的候选，但 `+0x1E0` 并不总是世界坐标。

## 4. 战斗工作线程的正确接入范例，以及重要冲突

Derpy 不依赖高频 Lua Hook 去控制工作线程。它在 `member Tick 0x03086F04` 安装 `mr.patcher('derpy_tp'):cave('mailbox', ...)`：Lua 仅把指定 member 与命令写入 mailbox，工作线程执行到其 member Tick 时按 RCX 身份筛选，对其他成员走原始 Tick，仅对选定成员执行 Native stop/walk/action。作者在源代码注释中说明，曾经直接在 Lua 线程修改 `member+0x330` 的活动动作，发生竞态崩溃；这是源作者记载，本轮没有重新实机验证。

**风险：** Derpy battle 自动加载入口的 `platform.build(mr)` 内即调用 `P.check_mailbox()`，这一调用早于 F2 开启控制，且早于脚本的多人/回放排除检查。虽然安装需通过版本/字节/API 门槛，不能断言必成功，但**仅加载 Derpy 就可能占用 BSC 想观察的普通成员 Tick Hook 点**。memreader Plus 的 `sites.lua` 标记 `cave/frame/relocate` 为 `STAYS`，这类改动会留到进程退出，不支持在同次游戏会话中完全卸载。**BSC vanilla 基线禁止同时启用 Derpy。**

## 5. 不可直接照搬的运动策略

Derpy 的 `P.steer` 会直接写 member `+0x1E0/+0x1E8` 和 `+0x194/+0x198` 目标副本，`P.face` 写 `+0xB0` 朝向，并由工作线程的 mailbox 构造/停止单兵动作。其目的就是脱离 CA 整队指令，**正与 BSC 必须保留原生 queued Shift MOVE、渐进转向及阵型协同的设计约束相反**。只能复用其**成员识别、版本验证、跨线程通信与原字节安全防护思路**，不能直接复用单兵方向控制算法。

## 6. 交付及止损标准

已离线制作只读 PFH5/PE/嵌入 DLL 元数据审计器、来源 SHA 清单、静态 JSON 证据与 **非自动加载、未实机验证**的 BSC 单位成员只读采样原型。用用户两份 .zip 和固定游戏 EXE，**11/11 unittest PASS**；无私有素材 **7 PASS / 4 SKIP**。这只验证离线审计，不代表补丁或采样实机可靠。

完整离线工作文件：`BSC_R46_DERPY_MEMREADER_ACTUAL_PACK_AUDIT_20261020.zip`（聊天附件，不包含第三方 MOD、原生 DLL 或游戏 EXE；GitHub 只维护原创总结和研究资料）。

下一步先证明 `BattleUnit→member` 的身份及生存期和实际战斗线程边界，再设计最小只读采样；必要时参照 Derpy 使用有版本门槛的 Native mailbox，但**不引入可改变 gameplay 的动作控制**。没有同实例错误条件就不发布 Native patch。

**结论：`derpy_pack_reviewed=true`，`same_exe_opcode_verified=true`，`memreader_runtime_executed=false`，`new_gameplay_test=false`，`root_cause_proven=false`，`gameplay_patch_authorized=false`。**
