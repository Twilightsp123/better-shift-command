# BSC R85 — 候选控制器 0x738 的异对象间接写入审计与止损（2026-10-27）

目标是修复同一兵牌 Shift 连续折返的成员轨迹拥挤；这是群体空间现象，不是引擎里的某个挤压动作。

## 实际原始 EXE 证据
用户匹配的 Win64 Warhammer3.exe：SHA256 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496；232531920 bytes，ImageBase 0x140000000；地址均为 RVA。只读离线逆向，没有游戏进程 Hook。

- 已确认普通成员类型：构造器 0x03052F82 清 QWORD member+0x738；普通成员 vtable 0x03912950+0x4A0 → 0x030751E4；其 0x03075202 读取同一成员的候选引用，非空时 0x0307520E → 0x03126964 处理引用对象。候选函数 0x0311F34C 以 inline controller+0x20（即 member+0x738）消费该指针；其完整函数体七处直接读取、没有识别到直接写入。
- 新确认的异对象假写者：0x02F9C9C4 构造路径安装 vtable 0x03AD01F0，0x02F9C9FE 保存 R14=该对象。0x02F9D16C 确实把 QWORD 写到该对象+0x738，但它不是普通成员构造器。
- 同一个十六进制偏移在另一输入对象上更像间接 setter：0x02FA6054 在 0x02FA6088 保存 R14=RDX，0x02FA66F8 把 RCX 设置为 R14+0x738 字段地址，0x02FA6705 提供 RBP+0x140 临时记录，0x02FA6734 E8→0x02F93ABC。已完整解码的接收函数以 [RCX] 为容量、[RCX+4] 为计数、[RCX+8] 为数组指针，以 24B 为步长追加记录（必要时扩容）。这是**另一对象的 24 字节记录向量**，并非普通成员的导航候选引用 setter。
- 0x0329B276/31F 写 RBP 所属局部工作记录+0x738；0x0300BB6A 和 0x0303A16A 写入其他对象的 DWORD+0x738。不能按相同字段位移错误合并对象所有者。

## 精确验证范围
原始 SHA 匹配的 EXE 上已验证 49/49 原始机器码及 llvm-objdump 真实指令起点、4/4 E8 调用目标、10/10 PE unwind 函数边界、普通成员虚表+0x4A0；26/26 Python 本地测试通过。公开仓库提供 49 pin、10 函数范围、4 E8 和 SHA fail-closed 的校验器与模拟测试；公开 CI 的商业 EXE 项应跳过。完整离线 ZIP BSC_R85_TYPED_CANDIDATE_WRITER_STOP_20261027.zip 包括十段反汇编、日志、全部本轮源码及 R84 历史包，不包含游戏 EXE。

这只是受限的位移编码/类型化调用审计，并非全引擎指针别名穷举。**没有发现可靠的普通成员运行期 setter，不等于证明游戏绝不会赋值。** 未证明其等于 Shift 路点编号或造成成员挤压，未授权游戏修复。

## 决策与 R86
正式停止 R80–R85 中无新类型证据的同偏移扩张。 MEMBER_CANDIDATE_738_RUNTIME_WRITER=UNKNOWN，OFFSET_SCAN_DEPRIORITIZED=true。R86 转向可证伪的同一兵牌多成员**同时刻**几何连续性：世界目标、最近邻距离、内外侧转向半径、成员相位差及实际积分。不能把合成直线插值冒充 CA 的轨迹，不能直接强制同步成员或修改原生移动队列、RMB、Shift ATTACK、避障/速度。

crowding_root_cause_proven=false; gameplay_patch_authorized=false; main_unchanged=true.
