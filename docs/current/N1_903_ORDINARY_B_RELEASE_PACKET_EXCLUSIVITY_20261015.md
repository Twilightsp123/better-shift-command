# BSC N1 — 第16轮：bigTask 清理后的普通 B 两条成员发包路径（2026-10-15）

## 版本与精确证据

固定用户原始 WH3 Win64 EXE SHA256：`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，ImageBase `0x140000000`，地址均为 RVA。本轮在真正原始 EXE 上严格校验 **72/72 字节/objdump 指令起点、11/11 直接 E8、4/4 JCC、2/2 具体普通 B 虚表槽**，并检查构造器 RIP vtable 和两个无 unwind 叶函数结尾。**10/10 本地回归通过**，包含真实 EXE 与错误 SHA/Python -O fail-closed。只读静态验证，**不是游戏实际 Shift 命中，也不是修复效果**。

## 真正的有类型数据关系

1. `0x02F4F514 → 0x02F4F52B CALL 0x02F50FE4`：在旧关联对象仍存在时减少 bigTask 引用计数，并把 `*[shortTask+0x80]`（之前已证与 MOVE slot+0xA0 对应）置零；这是**释放引用**，不能认定对象已释放内存。
2. 后续 `0x02F4F5DE CALL 0x031219B0` 生成普通路线节点；`0x02F4F603` 读取 `node+0x70`，`0x02F4F617 CALL 0x03263F64`。该叶函数 `0x03263FB0` 写 `descriptor+0x28=node+0x70`。
3. `0x02F4F62C CALL 0x03279EE8` 按 mode helper 区分 A/B。仅 mode helper=0 时 `0x03279F71 CALL 0x03263EC4` 创建**普通 B**；构造器安装 vtable `0x03AE00E8`，将 `descriptor+0x28` 写到 `aux+0x60`，并设置 `aux+0x78=NULL, aux+0x80=0`。
4. 普通 B 基类 `0x030C35A0` 还持有 group/context 身份，因此“无直接旧 slot 读取”**不等于**证明所有间接 oldTask/route 关联不存在。

## 新的负证据：普通 B 两个虚表方法不必重复发包

普通 B 虚表 `0x03AE00E8`：

| 原生方法 | 已证条件性作用 |
|---|---|
| `+0x08 = 0x03271B0C` | `aux+0x60` 非空时直接取已有路线、调用 `0x03265B24` 生成逐成员包，并写 `aux+0x80=1`；为空时创建普通节点，保存到 `aux+0x78` |
| `+0x10 = 0x03281520` | 先检查 `aux+0x80`；已为 1 则跳过再发。未处理时要求 `aux+0x78` 节点非空、`node+0x08` 有效，才经 `node+0x70→0x03265B24` 发包 |

**因此可排除一个默认假说**：普通 B 正常 fast-route 执行 `virtual+0x08` 后，`virtual+0x10` 必然再对同一批成员重复发令。真实 flag0x80 明确阻挡了这条重复路径。原先的 `aux+0x78→node+0x70` 调查只覆盖了普通 B 的后续节点路径，不能冒充所有 B 发包。

**另一项排除：** 本次 ordinary-B 构造已经从新创建的 node 把几何复制至局部描述符及 `aux+0x60`，因此不能再要求 `MOVE slot+0xA0` 必须一直持有旧 bigTask 才能解释 fast-route 发包。仍需确认 group 间接身份与路线几何代际是否正确。

## 接下来只追一个真正的差异

P1：证明 **`aux+0x60!=NULL` 的 fast-route 与 `aux+0x60==NULL` 的 node fallback** 在同一 queued MOVE 条件下何时发生、各自的成员 `record[i]`/packet kind/子动作和 motor goal 安装时间。具体调查 node+0x70 的有效性生产条件与 group/node 对象的生存期；如果实例不能由静态代码唯一确定，再设计**一次性只读**（在 `0x02F4F52B` 之前绑定 task 身份）的必要诊断，不让玩家重做已确认挤压测试。

不得修改原生 EXE、取消旧方向投影、改所有 packet flag、影响 RMB/Shift ATTACK。`native_patch_authorized=false`。

## 代码与回归

- `maintenance_tools/native_shift_re/b_ordinary_identity_pins_20261015.txt` — 72 个原始指令的精确字节；
- `maintenance_tools/native_shift_re/audit_b_release_packet_paths_20261015.py` — 固定 SHA/PE/unwind/真实指令/E8/JCC/typed vtable/叶函数检测；
- `tests/test_native_shift_re_b_release_packet_paths_20261015.py` — 10 个测试（公开 CI 缺原始 EXE 时预期 9 PASS、1 SKIP）；
- 独立完整离线资源包含本轮中文记录和全部本地测试结果，不上传原始游戏 EXE、进程内存指针或未经验证 gameplay patch。
