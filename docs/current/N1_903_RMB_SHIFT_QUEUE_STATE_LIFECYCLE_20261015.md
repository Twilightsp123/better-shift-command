# BSC N1 — RMB REPLACE vs 队列 MOVE 差异与 bigTask 状态链（2026-10-15）

## 静态研究输入与验证

用户提供的 Windows x64 原始 `Warhammer3.exe`，SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`；PE ImageBase `0x140000000`。本文地址全部为 RVA。版本数字 9.0.3 仍只是用户提供的标签，不是独立核验结论。

在原始 EXE 上：**72/72 队列机器码和 decoded 指令起点、64/64 真实 E8 MOVE 入口、4/4 类型化 MOVE 虚表；69/69 状态机机器码和真实起点、8/8 直接 E8、6/6 JCC**，还核对两个无 unwind 叶函数。附带完整本地离线 **32/32 PASS（3项私有原始 EXE 校验）**，包含错误版本 fail-closed 和 `python -O` 负例。以上均是 **EXACT_ORIGINAL_EXE_STATIC/SYNTHETIC_CONTRACT**，没有实机玩家 Shift/RMB 输入身份命中，也无 gameplay patch。

## 一、MOVE 入口存在明确的 replace / append 开关

`0x030323C8` 原生 MOVE 接口由 `0x030323FC` 读取 R9B，转交给 `0x030326BB` 的 DL，`0x02F50410` 使用该位决定队列行为。**DL=0** 清理原槽后添加新命令；**DL!=0** 保留旧槽位并追加（常规容量门槛为 40）。

新 MOVE 的 `slot+0xA0` 在两者的初始构造阶段都是 **NULL**；不是追加后立即强制继承旧大任务。下一阶段队列推进时，旧槽的 `vtable+0x40=0x03039FB0` 必须验证 old bigTask 的 state4、flag、旧 subtask 和 group 合法性，然后后继槽 `vtable+0x48=0x03040864` 才有条件将同一 bigTask 赋给新槽位并将大任务重置为 state1，更新三块新路线几何。普通 fresh state0 与 inherited state1 依然共用 CA 原生生成器 `0x0311E80C`，后者 state1 的旧方向投影仍有门槛，不能粗暴清空旧引用。

## 二、64 个入口不代表 64 次玩家操作

对固定 EXE 的 `.00cfg` 扫描得到 64 条真正的 `CALL 0x030323C8`，逐条通过 PE unwind 所属函数和 objdump 指令边界验证。按照调用点之前最近的局部 R9 写入：**54 局部设置0、3 局部设置1、7 动态转发**。此分类仅是局部指令语义，**不是路径敏感运行时常数证明**。

另外，`0x0304433C` 在 `0x030444C1`、`0x03044531` 有两次内部 MOVE 重发。原生叶函数 `0x02D25674` 只复制数据，不修改承载追加位的 R8B，所以两条 `R9B=R8B` 的调用进一步可确认为内部追加请求。细化为 **54 设0、5 已知1、5 动态**。另三处固定1源为 `0x031F1DA6`、`0x0320444E`、`0x03224794`。

上游还可从 `0x01B9E7EC` 的内部序列化布尔解码经 `0x02ECBFA0→0x02F45EC0` 的第五参数送到 MOVE；另有 `0x02ECD088→0x02F482D0→0x02F4B20C` 第五到第七栈参数的转发。**无法据此认定这个参数直接来自玩家的 Shift 键事件**。内部自发追加也会使用同一个入口。

## 三、新突破：同一大任务的 state1 → state2 → state3 → state4

`0x0311DE74` 的初始入参 RDX 为 bigTask；`0x0311DEB2 MOV RDI,RDX` 保存该对象指针。state1 调用生成器 `0x0311E80C` 时，生成器 `0x0311E84F MOV RSI,RDX` 继续操作同一个 bigTask。这一身份关系不是把不同对象的相同偏移拼起来。

**长生命周期（全部为条件性，不代表每帧必执行）：**

1. state1 先清 bigTask `+0x24`，共享生成器重新计算。返回的 flag=1 时，`0x0311EBC2` 写 bigTask `+0x20=2`；原 state1 分支随后才按 `+0x24==1` 旧方向投影，把旧 `+0x158` 子任务引用交给下一 subtask。
2. 下次 state2 处理在 `0x0311E540` 检查节点 `+0x6E`，特定结果由 `0x0311E546` 写 bigTask `+0x20=3`；存在其它状态分支，并非无条件推进。
3. state3 调 `0x03125A1C`；当其 EAX=0 的条件分支成立，`0x0311E41B` 写 bigTask `+0x24=0`、`0x0311E41F` 写 `+0x28=3`，传同一 RDI 指针给 `0x0311EC28`。该函数 `0x0311EC49 MOV RSI,RDX`，于 `0x0311ED63` 写 `bigTask+0x20=4`。
4. 因而**存在**同一 bigTask 的可达状态组合 `(+0x20,+0x24,+0x28)=(4,0,3)`，满足第10轮 `0x02F561E8` 的特定 shortTask 分发门槛，随后能有条件进入 `0x02F4F514→0x03279EE8` 普通 B 成员任务链。

**另一条早退分支：** 如果 state1 公共生成器重算 flag=0，可直接写 state4，但 `+0x28` 在已确认分支为 **1 或 2**，并非 B shortTask 要求的 stage3，state1 调用者也跳过本轮旧方向投影。因此不能把每个 state1→4 都当作普通 B 发包。

短期任务关联读取器 `0x02F4EFE0` 是无 unwind 叶函数，读取 `shortTask+0x80` 指向的间接任务地址或后备 `shortTask+0x98`。**未证明**这个 shortTask 在 state1→2→3→4 的整个跨时序周期均存活并持续绑定同一 bigTask；此前成功 MOVE→MOVE 继承会清退旧 shortTask 的负面证据仍有效。

## 四、修复前仍缺的真实实例数据边

目前找到了输入队列语义差异、条件性任务身份继承、state1 状态分流和到普通 B 发包的候选生命周期联系。**还没有**把某次玩家 Shift 键的明确 order、继承状态 bigTask、后续 shortTask、当前 group generation 以及同组两名相邻成员的目标安装代际连成动态实例。也未证明哪一段引起 Shift 折返的队内挤压，Native gameplay 修复尚未授权。

应继续追 shortTask 关联指针与 queued handoff 后对象生命周期，以及路线的成员目标代际，保留 CA 原生队列、渐进转弯、避障、普通 RMB 与 Shift ATTACK。禁止全局更改 packet 标记、强制清旧 subtask 或拦截所有 R9B=1。

## 五、仓库审计工具

- `maintenance_tools/native_shift_re/audit_rmb_shift_lifecycle.py`：原始 EXE 严格 SHA、typed vtable、真实反汇编边界、64 个 E8、条件分支与无 unwind 叶函数。
- `maintenance_tools/native_shift_re/rmb_shift_exact_pins.txt`：72 个原码指令位置。
- `maintenance_tools/native_shift_re/state_lifecycle_exact_pins.txt`：69 个状态机原码位置。
- `tests/test_native_shift_re_rmb_shift_lifecycle.py`：8 项测试。公开 CI 没 EXE 应为 7 PASS / 1 SKIP。独立的完整 Round12 资源包还包含另外两份详细审计源码、24 项详细回归和脱敏 JSON 证据。

**native_patch_authorized=false；没有修改 main、游戏 EXE、包含指针的用户日志。**

## 六、第12轮续查：新 shortTask 的关联 bigTask 身份终于闭合

新增固定 SHA 原始 EXE 的**36/36 机器码/解码指令起点、6/6 直接 E8**，两个无 unwind 叶函数与 Win64 栈参数别名核验（`audit_move_slot_shorttask_binding.py`）；联合审计回归提高为 **40/40 PASS**，其中 **4项使用私有原始 EXE**。该结果属于静态原码，不是新实机折返。

精确指针传递：

1. 新 MOVE 槽位激活 `0x03025DD7 LEA R14,[MOVEslot+0xA0]` 获取的**是大任务指针字段的地址**；`0x03025E39` 说明激活时另有兼容性检查可清空该槽位所持有的旧 bigTask。
2. `0x0302608D MOV [RBP-0x70],R14` 将该地址放进短任务描述符。由三个原生 PUSH、`RBP=entryRSP-0xB8`、`RSP=entryRSP-0x1B8` 严格可得 `[RBP-0x70]=[RSP+0x40+0x50]`，并在 `0x0302609F/AF` 把描述符送进 `0x02F2C734`。
3. 构造器 `0x02F2C758` 将复制目标设成 `&shortTask+0x30`，`0x02F2C770` 把源设成描述符，`0x02F2C784` 调用无 unwind 的 `0x02F2C834`：`0x02F2C8A7` 读描述符 `+0x50`，`0x02F2C8AB` 写目的 `+0x50`。因此**`shortTask+0x80 = &MOVEslot+0xA0`**。
4. 关联任务 getter `0x02F4EFE0` 确实先读 `shortTask+0x80`，若该**地址非空**，则再解引用得到 `MOVEslot+0xA0` 当前存储的 bigTask；仅地址为空时使用 `shortTask+0x98` 备份。
5. 当该槽位任务当前为 NULL，`0x02F2C7BF/0x02F2C7C7` 合格分支经 `0x02F2C81B→0x02F41644` 创建新 bigTask，`0x02F41675` 通过 `*[shortTask+0x80]` 将它写回同一个 MOVE slot+0xA0。成功交接的后继槽可先存同一旧 bigTask；这条机制不要求**旧 shortTask**复活。

至此，**成功继承后，新 MOVE 槽位创建的短期任务与该槽位保留的同一个 bigTask 具有确切地址连接**。这比“同一大任务可能在某个短任务里出现”更强，而且不会与此前正常成功 MOVE→MOVE 交接清退旧 shortTask 的负证据冲突。

仍未证明玩家某次 Shift 继承的具体状态历程、group generation、两个相邻成员最后 motor goal 的错误代际和挤压因果。不要用“短期任务复活”解释新 shortTask 的合法晚绑定，也不授权修改原生 gameplay。新增 [严格源码](../../maintenance_tools/native_shift_re/audit_move_slot_shorttask_binding.py) · [回归](../../tests/test_native_shift_re_move_slot_shorttask_binding.py)。
