# BSC N1 — 普通 B 节点成员发包与 packet 0x20 分流（2026-10-15）

## 输入、证据等级和范围

固定用户提供原始 `Warhammer3.exe` SHA256：
`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`。原始 PE32+ x64，ImageBase `0x140000000`；本文件全部函数地址为 RVA。

本轮独立只读验证在真实原始 EXE 上 **10/10 机器码签名通过**，新增单元测试 **4/4 PASS**（其中 1 项使用私有 EXE）。机器码签名是选定字节的直接匹配，**不是**完整控制流/对象类型/指令起点重审，也不是运行时实机命中。CI 没有原始 EXE 时只能运行无需原始文件的测试，EXE 现场校验应跳过。`native_patch_authorized=false`。

## 1. 普通 B 节点的条件性下游

* `0x03281520`: `0x0328153D` 读取 `aux+0x78`，`0x03281554` 读取 `node+0x70`，`0x032815C5` 直接调用 `0x03265B24`。
* 入口同时检测 `aux+0x80`、`node+0x08` 等条件，**不能**把这条边说成无条件。
* `0x03265B24`: `0x03265BBE` 调用阵型策略 `virtual+0x48`，然后逐成员生成目标记录；`0x03265D3F` 发往 `member virtual+0x368`。
* `record[i]+0x2C` 与 `member+0x318` 的分支在此路径被访问，但原始 `record[i]` 不等于最终 motor goal。后续空间、朝向修正必须保留。

**禁止类型混淆：** 本轮普通 B 持有者是 `vtable 0x03AE00E8 / aux+0x78`；旧大任务引用 B 持有者是另一个类型 `vtable 0x03AE0128 / aux+0x58`。不能因二者皆有 `node+0x70` 便断定在同一个 queued Shift MOVE 实例执行。

## 2. Packet 构造函数不是固定的 0x06/0x26 二元分类

* `0x02F5F868` 在 `0x02F5F8BD` 明确写入 `packet+0x50=0x26`。
* `0x02F5F8DC` 在 `0x02F5F940` 执行 **OR 0x06**，后在 `0x02F5F95E` 保存组合标志至 `packet+0x50`；另有布尔参数参与 bit `0x10` 组合。**不能**声称这个构造器在全部调用中始终写出精确的 `0x06`；输入及其它标志来源应继续验证。

## 3. 成员接收器的两重条件

`0x0306B9F0` 调用原生 mode helper `0x02DC2E04`，在已发现的门槛路径里：

1. mode helper 返回 **0**；
2. `packet+0x50 & 0x20 == 0`；
3. 才于 `0x0306BA5B` 调用 `0x02F5F7C8`。

所以 `0x20` 位**不是唯一条件**。不得将“无 0x20 = 延迟运动”、“有 0x20 = 即时运动”当作已经证明的物理事实。`0x02F5F7C8` 初始化与成员／时间相关的任务对象（已识别虚表 `0x03905E18`），**尚未追清其更新/失效时机及是否写入 `member+0x1E0` motor goal**。

## 4. 后续直接研究的缺口（不是已证 root cause）

1. 查 `0x02F5F7C8` 任务的构造、拥有者、更新虚函数与释放条件；对比接收器另一分支的真实 motor goal 写入。
2. 查 `0x03279EE8 → 0x03AE00E8` 的普通 B 成员发包是否与 queued inherited MOVE `state=1` 为同一真实实例。
3. 若需验证同组两名成员不同 packet 标志与目标激活阶段，应先完成只读静态断点设计，严格锁定原始 EXE，不让玩家重复证明已知挤压问题。

**未授权 gameplay patch，没有修改游戏原始 EXE，没有真实 Shift 修复效果声明。**

## 5. 对应源码、回归和提交纪律

* `maintenance_tools/native_shift_re/audit_b_member_packet_receiver_flags.py`：完整 EXE SHA 守卫，选定 10 个字节签名，标准库即可运行，**只读**。
* `tests/test_native_shift_re_b_member_packet_receiver_flags.py`：错误 SHA fail-closed、标志位反例、可选的本地真实 EXE 测试；公开 CI **不得**上传原始 EXE。
* 本地验证：`python maintenance_tools/native_shift_re/audit_b_member_packet_receiver_flags.py /path/to/Warhammer3.exe`；`WH3_903_EXE=/path/to/Warhammer3.exe python -m unittest discover -s tests -p 'test_native_shift_re_b_member_packet_receiver_flags.py' -v`。
* 本文件只属于研究分支 `research/n1-native-shift-behavior-patch-20261009`；禁止修改 `main`，禁止上传原始游戏 EXE 或含运行时指针的原始 JSONL。
