# BSC R95 — S2 两类原生目标记录的参考框架与世界坐标转换（2026-11-17）

**判据：S2_STATIC_FRAME_MATH=PROVEN；S2_RECORD_LAYOUTS=PROVEN_FOR_TWO_TYPES；S1_SAFE_LIVE_SNAPSHOT=NOT_PROVEN；SHIFT_INSTANCE_TIMELINE=NOT_PROVEN；SEARCH_CANDIDATE=false；ROOT_CAUSE_PROVEN=false；GAMEPLAY_FIX_PROVEN=false。**

## EXE 身份、研究边界

用户原版 Win64 `Warhammer3.exe` 232531920 字节，SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`，PE AMD64，ImageBase `0x140000000`。本文地址均为 RVA。仅在原始 EXE 上做只读静态分析；没有 Hook、没有游戏内测试、没有 gameplay 补丁。不再重复证明用户确认的 Shift 折返挤压。

## 两个不同类型的目标记录，不可混用参考字段

- **持久导航目标**：R79 已证明常规 setter `0x0311E6CA` 写 `member+0x1E0` 的前 16 字节，`0x0311E6E8` 写入 `member+0x1F0` 的 8 字节引用。R95 核查解析器 `0x03121F54` 在 `0x03121F5B` 读取 `record+0x10` reference；空指针分支 `0x03121F6F..7F` 复制前三个 float XYZ；非空分支 `0x03121F64/68` 用 `reference+0x18` E8 调 `0x02F3D668`。
- **阵型 Packet 空间记录**：`0x03070B54` 与 `0x03070B6F` 的受条件双分支均 E8→`0x0312214C`，它在 `0x03122153` 读取 **`record+0x18`** reference，而不是导航目标的 +0x10；空指针复制 XYZ，非空在 `0x0312215C/60` 同样调用 `0x02F3D668`。之后可分别调用 member vtable +0x100 或 +0xE8；并未证明 Packet = 正在追踪的持久目标。
- **实际 Steering 消费者**：`0x0305A061` 从当前 member+0x1E0 取导航记录，`0x0305A06D` E8→`0x03121F54`，之后从解析的世界 XYZ 减去成员实际 XYZ。入口受 `0x0305A05B` 条件保护，不能推断每个 Tick 必然命中。

## 真实仿射变换，字段布局由原生机器码证明

`0x02F3D668` 收到 `RCX=reference+0x18`、`R8=local_xyz`、`RDX=out_xyz` 后，取如下 float32：

```
translation T = ref + {0x18, 0x1C, 0x20}
basis row 0   = ref + {0x38, 0x3C, 0x40}
basis row 1   = ref + {0x44, 0x48, 0x4C}
basis row 2   = ref + {0x50, 0x54, 0x58}
world         = T + basis(3x3) * local_xyz
```

原生代码按 scalar SSE 顺序运算，未预设矩阵必然正交或单位尺度。浮点 FTZ/DAZ 模式、实际多线程引用变化没有被证明。两个解析器共同使用此变换器，但**不是同一个记录格式**。

## 负对照与实际根因关系

合成例证明：相同 local(2,0,4)，若参考平移分别是 (10,0,0) 与 (50,0,0)，世界目标分别为 (12,0,4) 与 (52,0,4)；不同 local(1,0,0)/(6,0,0) 与不同平移(10,0,0)/(5,0,0) 可以得到相同 world(11,0,0)。**只比较局部目标会产生漏报或误报**。即使参考指针不变，其矩阵数据也可能随时间变化；静态代码不能证明实际游戏发生该现象。

离线工具接收已取得的记录与完整 reference 矩阵，强制核对 Root/Group/route/tick/reference epoch 字段一致性，拒绝重复 member ID、缺失矩阵、非法或非有限 float。其结果始终标记 `STRUCTURAL_ONLY`，**用户声明的 epoch 并不能证明原生线程所有权或对象存活**。

## 验证与禁止越界

本地对匹配的真实 EXE：**120/120 完整指令字节与 LLVM 真实起点、5/5 E8、4/4 Jcc、18/18 语义锚点、6/6 PE unwind 归属**。本地 **27/27 unittest PASS**（1 项真实 EXE 验证，1 项错 EXE 拒绝）；公开无 EXE 模式 **25 PASS/2 SKIP**。记录见本地完整 R95 ZIP 的 `evidence/`（包含 6 段 ASM、原码 manifest、输出和合成反例），绝不上传商业 EXE。

R94 已证明 Group 池回收存在 ABA 风险，未取得安全的 engine-owned 同步观察窗口/route generation；不允许以双重指针读取或 Derpy Tick Hook 拼装未经证实的 live 观测器。

**R96 的唯一验收目标：**在引擎自身持有合法对象生命周期的调用阶段，将一个确切的 queued Shift route generation 关联到 Root→Group→member，并证明参考矩阵与目标/位置能够在同一可信时间窗口读取。做不到则继续离线静态分析，不要求用户再做实机测试。

完整报告参照本轮 ZIP；R94 历史 ZIP 在本会话容器中无法取得 backing bytes，不能虚称已在 R95 包中嵌套。
