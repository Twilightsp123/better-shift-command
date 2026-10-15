# WH3 9.0.3 — Native Shift RE offline tooling

**Research-only. No executable patch and no proven 9.0.3 queue writer.**

## Scripts

- **scout_pe.py** (Python 3.8+, standard library). Read-only AMD64 PE header, SHA256 and executable-section scanner. Uses historical 9.0.2 byte guards exclusively as discovery leads, including relocation masks. Even an exact byte match is NOT a verified RVA/ABI/Hook.
- **ghidra_order_xrefs.py** (Ghidra Jython). Searches decoded executable instructions for operands matching the *historical* 9.0.2 offsets +0x2F88/+0x2F8C. Includes opcode bytes, function context and read/write hints; neither current Unit-root provenance nor actual field-access semantics are established.
- **../../tests/test_native_shift_re.py** contains synthetic fixture tests (not game physics or WH3 proof).

## Read-only PE fingerprint and byte-similarity scan

From the repository root, with the installed original 9.0.3 EXE:

    python maintenance_tools/native_shift_re/scout_pe.py --exe "C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\Warhammer3.exe" --report "N1_outputs\pe_scout.json"

The first pass records SHA256 but reports UNVERIFIED_BUILD_SHA_DISCOVERY_ONLY, because a matching digest for 9.0.3 is not pre-established. Independently confirm the EXE build before asserting its game version. Optional pinned rerun:

    python maintenance_tools/native_shift_re/scout_pe.py --exe "C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\Warhammer3.exe" --expected-sha256 "<recorded verified 9.0.3 SHA256>" --report "N1_outputs\pe_scout_pinned.json"

SHA_VERIFIED_BINARY_RESEARCH_ONLY means **hash matched user-supplied expectation**, not that byte pattern implies a valid engine hook. EXE and legacy JSON are never written. Invalid input returns code 2; explicit old-build rejection/expected SHA mismatch returns code 3.

## Ghidra decoded instruction candidate search

1. Import and fully analyze the *same* SHA-verified 9.0.3 executable in Ghidra; retain the original EXE on disk.
2. Add maintenance_tools/native_shift_re to the script search path.
3. Run ghidra_order_xrefs.py with script arguments:

    --exe=C:/WH3/Warhammer3.exe
    --expected-sha256=<same exact hash>
    --output=C:/WH3/N1_outputs/ghidra_order_xrefs.json

The script confirms the EXE SHA256, compares its MD5 to the Ghidra imported-program MD5, and refuses to overwrite the EXE. Ghidra was NOT run in the development container: treat the script as a tested Python syntax/contract draft awaiting Ghidra runtime compatibility and 9.0.3 binary verification.

**Output limitations:** the Ghidra script detects operands with scalar values matching historical fields. It cannot discover optimized aliases/changed offsets reliably; an operand read/write hint is not proof the memory belongs to a WH3 order queue. It never promotes a site or authorizes patching.

## Native proof steps after candidate export

Find an actual engine root provenance, confirm original head/count **writers**, and follow control/dataflow to MOVE completion, old order retirement and next activation. In parallel, trace original per-frame MOVE braking and motion state. Separately identify original ATTACK activation/target lifetime. Maintain exact SHA, instruction bytes, RVA, ABI, xrefs, alternatives and negative normal-RMB controls.

## Exact user-provided 9.0.3-labelled EXE state-origin proof

`verify_903_move_state_origin.py` is a **read-only, exact-SHA evidence verifier**, *not* an address relocator. It matches 25 selected machine-instruction guards and two original float constants and records that no patch is authorized. It rejects other EXE hashes, including other builds of WH3.

    python maintenance_tools/native_shift_re/verify_903_move_state_origin.py --exe "C:\\path\\to\\Warhammer3.exe" --report "N1_outputs\\state_origin_evidence.json"

Original result for SHA `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`: **25/25 instruction guards match**, 8/8 isolated byte/metadata tests passed against original EXE; six additional synthetic CI tests were added without the EXE. No gameplay, Ghidra, or Win64 loader behavior is verified.

See [native state origin report](../../docs/current/N1_903_MOVE_STATE_ORIGIN.md).

## Offline synthetic test

    python -m unittest discover -s tests -p "test_native_shift_re.py" -v

Initial isolated Python result: **9/9 PASS** on synthetic PE files. This is NOT Ghidra integration success, Windows runtime testing or WH3 acceptance.

No DLL, PACK, native injection, executable modification, shadow queue, Lua controller or Steam release results from these tools.

See docs/current/WH3_9_0_3_NATIVE_PATCH_DESIGN.md for the current N1–N6 plan.

## N1 route-gate evidence (9.0.3-labelled exact SHA)

`verify_903_route_gate.py` checks 46 frozen machine-instruction byte guards and 6 verified E8 call edges on the exact user-supplied EXE SHA only; always emits `runtime_patch_authorized: false`. The derived `state+0x24` truth table is **specific to the traced callback**, not a general WH3 mode or movement-speed rule. Run with:

    python maintenance_tools/native_shift_re/verify_903_route_gate.py --exe "C:\\path\\Warhammer3.exe" --out "N1_outputs\\route_gate.json"

Six synthetic CI cases reside in `tests/test_native_shift_re_route_gate.py`. The complete separately supplied local proof archive additionally contains bounded LLVM disassembly, byte evidence, tests and SHA manifest without the EXE. Actual WH3 physics/braking and Windows Hook compatibility have not been tested.

## N1 formation member/group coordinate entry (user-reported real defect)

The read-only `audit_903_formation_entry.py` accepts `--exe` and `--report` and refuses all EXE SHA mismatch. It compares **23 pinned exact instruction guards** and **6 decoded direct-call targets** for UnitRoot member-position aggregation and group coordinate updating before native order processing. This is NOT a proven soldier-array mapping, arrival condition or Hook location. Synthetic regression tests: `tests/test_native_shift_re_formation.py` (8 cases).

    python maintenance_tools/native_shift_re/audit_903_formation_entry.py --exe "C:\\path\\to\\Warhammer3.exe" --report "N1_outputs\\formation_entry.json"

See [N1 formation entry report](../../docs/current/N1_903_FORMATION_ENTRY_CALLGRAPH.md). The user-visible issue is within-unit soldier model desynchronization and crowding, **not a proven vanilla Move stop**.

## Distinct member layers (2026-10-10)

`audit_903_member_layers.py` verifies 23 exact user-EXE instruction byte guards and four E8 call targets. It preserves an important **negative inference**: two independent UnitRoot count/pointer vectors and one deeper child collection do **not** automatically identify individual soldier movement objects. It neither writes the EXE nor authorizes runtime changes.

    python maintenance_tools/native_shift_re/audit_903_member_layers.py --exe "C:\\path\\Warhammer3.exe" --report "N1_outputs\\member_layers.json"

See [N1 member layer report](../../docs/current/N1_903_MEMBER_LAYER_TYPE_GAP.md). Synthetic checks: tests/test_native_shift_re_member_layers.py. A separately provided full offline package also contains bounded LLVM instructions, 8 independent local tests and SHA manifest; no executable copy.

## Native MOVE → unit route proof (exact 9.0.3 user binary)

Run `audit_903_move_unit_route.py --exe PATH --report OUTPUT` to check the 23 exact byte guards and seven original E8 target calls linking both MOVE worker branches to `0x0301287C` and native route descriptor storage at root `+0x270`. Research only, not a Hook map. See [N1 report](../../docs/current/N1_903_MOVE_TO_UNIT_ROUTE_DIRECT.md).

Run `audit_903_member_route_virtual.py --exe PATH --report OUTPUT` to verify nine original bytes and two E8 targets near native unit-route/member virtual `+0xC8` dispatch. The vtable implementation and soldier identity are **not** proven. Old unrelated nearest-member selector `0x031E11AC` has no direct E8 caller identified; no patch proposed.

## N1 proven original MOVE fanout to group members

Read [N1_903_NATIVE_MOVE_MEMBER_FANOUT.md](../../docs/current/N1_903_NATIVE_MOVE_MEMBER_FANOUT.md). SHA-gated `audit_903_move_member_fanout.py` verifies **38 exact original machine instruction guards and nine E8 call destinations**: original MOVE issuer calls route update, constructs a unit-root-derived native group, creates group-specific 0x30-stride target records, and calls each member object's virtual +0x368 with a separately constructed native payload. The concrete VTable receiver/motor-completion logic is not yet identified. Synthetic CI gates: `tests/test_native_shift_re_move_member_fanout.py`.

    python maintenance_tools/native_shift_re/audit_903_move_member_fanout.py --exe "C:\\path\\Warhammer3.exe" --report "N1_outputs\\move_member_fanout.json"

This tool does not write to the executable, install hooks, or prove actual game animation/arrival behavior.

## N1 original member virtual receivers solved (9.0.3 labelled EXE)

`audit_903_member_virtual_receivers.py` verifies original SHA and **16 machine instruction byte guards**, scans native VTable slots +0x3F8 and +0x368, then independently confirms constructor RIP-relative LEA references. Exact-binary result: **38 VTables, 36 common member handler `0x0306B9F0`, 1 delegator `0x0306B9CC`, 1 special `0x03117CE0`**; group getter `0x008F37B0` reads `member+0x300`. Downstream member methods `+0xE8/+0x100` connect to native coordinate/heading writes and local route cache. No proven waypoint completion or runtime Hook. Synthetic CI tests: `tests/test_native_shift_re_member_virtual_receivers.py`. Full EXE-backed 7-case test bundle delivered separately.

    python maintenance_tools/native_shift_re/audit_903_member_virtual_receivers.py --exe "C:\\path\\Warhammer3.exe" --out "N1_outputs\\member_vtables.json"

See [research report](../../docs/current/N1_903_MEMBER_VIRTUAL_RECEIVER_RESOLVED.md).

## Exact 9.0.3 layout-count vs waypoint-arrival negative proof

`audit_903_layout_vs_arrival.py` statically verifies 26 code guards, eight constructor-backed strategy vtables (+0x20/+0x48), and distinct original group object virtual +0x20 (native RVA 0x030E0AA8). The strategy+0x20 values are formation layout cardinalities (sqrt(n), min(13,n), member-count lookup, etc.), not a demonstrated Shift waypoint arrival flag. Task+0xB8 caches these computed integers. The member receiver chooses +0x100/+0xE8 actions by member+0x104; no proven original leg-phase controller or Hook site. Offline tests `tests/test_native_shift_re_layout_vs_arrival.py` (8 cases).

    python maintenance_tools/native_shift_re/audit_903_layout_vs_arrival.py --exe "C:\\path\\Warhammer3.exe" --out "N1_outputs\\layout_vs_arrival.json"

See [finding](../../docs/current/N1_903_LAYOUT_COUNT_NOT_ARRIVAL_DISCONFIRMATION.md). No EXE writes.

## V3 active MOVE / mode0 / local pose / group-cohesion bounded call audit (2026-10-10)

`audit_903_active_cohesion_links.py` verifies the 9 documented E8 anchors and enumerates decoded direct and indirect callsites in 16 bounded windows on the pinned target EXE. It requires GNU `objdump` and the original 9.0.3-labelled SHA. It never alters game memory or asserts virtual/dataflow links from missing direct calls. Run `python maintenance_tools/native_shift_re/audit_903_active_cohesion_links.py --exe /path/to/Warhammer3.exe --report active_cohesion_links.json --objdump objdump`; offline tests: `python -m unittest discover -s tests -p test_native_shift_re_active_cohesion.py -v`. See `docs/current/N1_903_ACTIVE_COHESION_LINK_AUDIT.md`. This is not a Native Patch.


N1 9.0.3 registration reverse references: `audit_factory_registry_xrefs.py --exe PATH --out PATH` (exact SHA required); synthetic tests `test_native_shift_re_factory_registry_xrefs.py`. Static only, no native gameplay patch. See `docs/current/N1_903_FACTORY_REGISTRY_REVERSE_XREF_AUDIT_20261013.md`.


Third typed handler post-constructor negative: `audit_third_handler_post_ctor_v8.py` checks 16 original exact-SHA constructor → virtual+8 bounded paths and destructor; not a setter proof or patch. See `docs/current/N1_903_THIRD_HANDLER_POST_CTOR_V8_NEGATIVE_20261013.md`.


WH3 9.0.3 MOVE queue/member geometry type-gate: `audit_move_queue_member_gate.py --exe EXE --out PRIVATE.json` strictly verifies exact original SHA and 94 native instruction starts, conditional +0xB8 MOVE slot gate, stack coordinate provenance and two packet subtypes. Synthetic regression: `tests/test_native_shift_re_move_queue_member_gate.py`. Static research only; no Native gameplay patch. See `docs/current/N1_903_MOVE_QUEUE_MEMBER_GATE_20261013.md`.


## 2026-10-14 — 原生 MOVE UnitRoot / Group 的共同来源与双发包入口（精确 EXE）

最新只读审计 `audit_move_group_common_context.py` 在 SHA256 固定的原始 EXE 上实测 **98/98 opcode 与 objdump 指令起点、15/15 E8、2/2 typed vtable 槽、3/3 RIP 虚表安装** PASS；本地 **10/10 测试通过**。细节及负证据见 `docs/current/N1_903_MOVE_GROUP_COMMON_CONTEXT_20261014.md`。真实 group 构造器 `0x030C2D40` 接收 `UnitRoot+0x30`，将 `[UnitRoot+0x38]` 赋值给 `group+0x10`；上级构造器另外保存 `group+0xA10=UnitRoot`，`0x0301B8E4` 再保存 `UnitRoot+0x32F8=group`。发令入口 `0x0302DB44` 配置 `root+0x270` 后走 `0x030D5490`；MOVE 工作短期任务 `0x02F2C734` 保存 `shortTask+0x8=UnitRoot`，其 `0x02F561E8` 状态回调可沿 `UnitRoot+0x32F8 → 0x03279E40 → 0x030D554C → 0x030D5490` 进行另一次**条件性**成员发包。`0x03008894` 与 `0x030D554C` 静态访问同一表达式 `[[[UnitRoot+0x38]+0x440]+0x160]`，但通过不同转换函数准备成员记录；不保证运行时输出相同，不代表 Shift 实例必定双发包。此 `routeContext+0x160` 也**不是已证明**队列复用 `bigTask+0x160` 的别名。下一条要证明的是同一 queued MOVE state=1 的两路发包输入和逐成员目标代际，未授权任何 gameplay patch，禁止重复玩家折返测试。


## 2026-10-14 原生短期 MOVE Group 当前指针晚绑定与对象池重用（最新严格负/正证据）

新增 `audit_move_group_generation_latebind.py` 和同名前缀回归，固定 SHA 原始 EXE 通过 **91/91 opcode/unwind/objdump、19/19 E8、3/3 类型虚表**，13/13 本地测试 PASS。`0x0301B8E4` 每次路线重建先通过 `0x030197A8 → 0x0302C2D4` 把旧 group 送回 `context+0x150+0x58` 对象池，虚表 `0x0390F5F0+0x10=0x030C61D4` 的回收析构以 edx=0 跳过释放对象本体，再由 `0x0301B834 → 0x030C2C3C` 重新使用并写 `root+0x32F8`。短期任务 `0x02F2C734` 保存 `task+0x08=UnitRoot`，状态回调 `0x02F561E8` 到分发点才在 `0x02F563F4/FD` 读取**当前** `root+0x32F8`，把与短任务关联的临时参数交给 `0x03279E40`。后续清理检查 `0x02F5652D/7B` 在调用之后且受状态门槛限制。**指针相等并不保证 group 同代，可能发生对象池 ABA**，离线已给出有/无回收、任务已清退的对照反例。仍未证明真实 Shift 存在“旧 shortTask 在新 group 重建后继续进入回调”的时序，不能认定 Shift 挤压根因，不得改 EXE / Native gameplay。详见 `docs/current/N1_903_MOVE_GROUP_GENERATION_LATEBIND_20261014.md`。


Native WH3 9.0.3 shortTask scheduler typed stack: `audit_move_shorttask_resume_gate.py --exe PATH --out PRIVATE.json` validates exact SHA, 69 opcode instruction starts, 13 E8 calls, 5 branches and 4 vtable slots. Tests: `tests/test_native_shift_re_move_shorttask_resume_gate.py`. Shows non-top shortTasks have no-op +0x18 and +0x74 selects descriptor branches; NOT a gameplay patch. See `docs/current/N1_903_SHORT_TASK_STACK_RESUME_GATE_20261014.md`.


## 2026-10-14 — 大任务推进、路线描述符与成员发包共用原生几何管理器（新类型化审计）

新脚本 `maintenance_tools/native_shift_re/audit_shared_move_geometry_manager.py` 直接在固定 SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` 原始 EXE 上通过 **81/81 机器码+unwind/objdump指令起点、12/12 E8 直接调用、2/2 typed vtable**；本地 **13/13 单元测试 PASS（含真正 EXE 校验）**。中文独立报告：`docs/current/N1_903_SHARED_MOVE_GEOMETRY_MANAGER_20261014.md`。

经原始 ctx+0x440→routeContext+0x160 字段来源确认的 **manager** 同时支持三路调用 `0x030FDA9C(manager+0x18)`：路线描述符构造 `0x03121A99`，管理器路线节点生成 `0x03129092`，group目标适配/成员发包 `0x030D55F5`。关联上游 `0x02DD5A2C→0x02DD579C→0x03128E80` 读取该 manager，遍历 manager+0x1F0 的 bigTask 并通过 `0x0311DE74` 推进任务；此前证明的继承式 state=1 投影仍只在原生门槛成功时执行。转换器的某些分支写 `converter+0x1D0 = manager+0x1E8` 计数/状态字段，**未证明它是 generation ID**。这属于强于“函数复用”的静态管理器身份链，但 **manager+0x160 与 bigTask+0x160 不是已证实的指针同一性**；输出分别落在不同路线对象，不能宣称发生了目标代际错配或 Shift 物理挤压。正常成功 MOVE→MOVE 交接清退旧 shortTask 的反证继续有效。未授权 native gameplay patch，不修改 main/原始 EXE/含指针日志，不要求用户重复实机折返。


## 2026-10-14 第13轮 · B 家族大任务引用→旧子任务几何→路线节点的类型化静态链（最新）

**重要纠错：** `0x03AE00E8`、`0x03AE0108`、`0x03AE0128` 是由三个不同构造器实际安装的相邻虚表；`0x03281408` 真实属于**第三张** `0x03AE0128+0x10`，尽管该槽地址数值上也等于第一张表+0x50。绝不能跨对象类型拼接。短期 MOVE task `+0x74` 影响辅助对象是否沿 `0x03263E7C→0x03263D68` 将关联大任务指针写入 `aux+0x20`（并对非空任务引用增加 `+0x18` refcount）。B 型任务构造器 `0x03263AB0` 把该辅助对象放到自身 `+0x58`；类型化 `+0x10→0x03281408→0x03281444` 依当前节点、`aux+0x20` 及 `task+0x158` 条件，分叉到普通 `0x031219B0` 或大任务特化 `0x03121ABC` 路线节点构造。特化构造器 `0x030ECB10` 以**独立第六个 ABI 参数**读取大任务 `+0x80/+0x84/+0x88/+0x90/+0x98/+0x158`，`0x030FE1E4` 沿旧子任务 `+0x08` 链将各自 `+0x18` 几何输入关联为原生路线，结果存 `node+0x70`，同时将 `node+0x08` 初始标记有效，因而随后一般重算并非无条件立刻覆盖它。原始 SHA `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` EXE 实际完成 **168/168 opcode/objdump，22/22 E8，5/5 JCC，3/3 RIP vtable install，3/3 typed slots**；本地 **18/18 回归 PASS**。详见 `docs/current/N1_903_TYPED_BIGTASK_B_ROUTE_NODE_BRIDGE_20261014.md`、新只读审计与测试。**未证明某个玩家 Shift MOVE 实例命中 B 类型，也未证明 node+0x70→record[i]→motor goal 的错误因果；禁止 Native gameplay patch，禁止清空旧 subtask 以破坏原生渐进转弯。**

N1/9.0.3 typed B route reference lifecycle (2026-10-14): `audit_b_node_route_identity_gate.py --exe ORIGINAL_EXE --out private.json` validates 140 exact opcode/instruction starts, 17 E8, eight JCC, three typed sibling vtables and bounded RDX retention through native validation to `node+0x70`. It distinguishes the route+0x78 producer/consumer, conditional aux big-task release and generic-node fallback. Synthetic/optional private EXE regressions: `tests/test_native_shift_re_b_node_route_identity_gate.py`. See `docs/current/N1_903_B_NODE_REFERENCE_LIFECYCLE_20261014.md`. NO GAME PATCH.

## 2026-10-15 — Typed B member-packet receiver flag audit

Read-only SHA-pinned standard-library check: `audit_b_member_packet_receiver_flags.py`. It validates ten exact original-EXE byte guards for the conditional `aux+0x78 -> node+0x70 -> 0x03265B24 -> member+0x368` path, both packet constructor variations and the receiver's `0x20` gate. One constructor ORs `0x06`; the dynamic flags must not be mislabeled as a constant. Run:

    python maintenance_tools/native_shift_re/audit_b_member_packet_receiver_flags.py /private/path/Warhammer3.exe
    python -m unittest discover -s tests -p test_native_shift_re_b_member_packet_receiver_flags.py -v

With `WH3_903_EXE` pointed to the private original EXE, the fourth test additionally revalidates the actual bytes. Strict SHA and byte mismatches fail closed even under `python -O`. Local evidence: 10/10 byte guards, 4/4 tests. CI skips the real EXE; static proof is not gameplay success. Details: [packet receiver flags](../../docs/current/N1_903_B_MEMBER_PACKET_RECEIVER_FLAGS_20261015.md).

## 第 3 轮（2026-10-15）普通 B packet 和成员内联任务

`audit_b_member_packet_task_lifecycle.py` 使用标准 Python 库和 GNU objdump 对固定 SHA 的原始 EXE 只读验证 **84/84 指令起点/机器码、23/23 E8、8/8 类型化虚表**。本地 `test_native_shift_re_b_member_packet_task_lifecycle.py` 11/11 PASS（私有 EXE 存在时，其中一项审计原始代码；GitHub CI 会跳过此项）。

```
python maintenance_tools/native_shift_re/audit_b_member_packet_task_lifecycle.py --exe PRIVATE/Warhammer3.exe --out PRIVATE/b_member_task.json
python -m unittest discover -s tests -p "test_native_shift_re_b_member_packet_task_lifecycle.py" -v
```

重点：`0x0326A3A0` 的普通 B 调用可构造 `0x07/0x0E` flags；`0x0306B9F0` 在 mode/flag 条件通过时将成员内联任务构造到 `member+0x4A8`，holder `+0x490`，有效标记 `+0x5C0`；具体类型虚表 `0x03905E18+0x10=0x02F83B24` 条件性进入成员 `+0x328` 子动作处理。没有证明 motor goal 或玩家 Shift 实际分叉。见 [本轮中文报告](../../docs/current/N1_903_B_MEMBER_PACKET_TASK_LIFECYCLE_20261015.md)。不含 EXE、不含 runtime 指针、不含补丁。

**本轮追加精确 bit 查询：** 类型化虚表 `0x03905E18+0x80=0x008F4DD0` 读取 `task+0x90` 的 bit 0x10，bit 复制函数 `0x02D99F74` 与成员 Tick `0x0308234D` 已核实；`0x07/0x0E` 在内联任务刚安装时这个 bit 都为 0。总计 84/84 opcode、23/23 E8、8/8 vtable，11/11 本地测试。仍不代表实际 Shift 时序或最终 motor goal。

## 2026-10-15 第 10 轮：MOVE shortTask 与成员运动目标的有类型证明

- 新证据：MOVE `0x02F561E8` 只在特定条件进入 `0x02F4F514`，再经当前 `UnitRoot+0x32F8` group 到 `0x03279EE8`。mode helper = 0 时构造 `0x03AE00E8` 普通 B 对象，独立于带旧大任务的 `0x03AE0128`。
- 新代码 `audit_move_to_motor_goal_bridge.py` 加上 `move_to_motor_goal_manifest.txt` 严格 SHA/PE/真实 objdump 指令起点，核验 **218/218 唯一指令、28/28 E8、10/10 类型化虚表**。附加构造器 RIP/vtable、E9 早退、无 unwind 叶函数检查。
- 命令：`python maintenance_tools/native_shift_re/audit_move_to_motor_goal_bridge.py --exe PRIVATE/Warhammer3.exe --out PRIVATE/typed_goal.json`。回归：`python -m unittest discover -s tests -p test_native_shift_re_move_to_motor_goal_bridge.py -v`。
- 在没有私有原始 EXE 的公开 CI 中为 7 PASS + 1 SKIP；本地额外完整分段审计和测试合计 **30/30 PASS**。这是条件性静态控制/数据流，不证明真实 queued Shift、物理挤压根因和补丁。详见 [中文研究报告](../../docs/current/N1_903_MOVE_SHORTTASK_B_MOTOR_CHAIN_20261015.md)。不得提交 EXE 或运行时指针。

## 2026-10-15 第 12 轮：RMB/queued MOVE 指令入口和状态生命周期

**只读**审计入口：`audit_rmb_shift_lifecycle.py`；固定 EXE SHA 为 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`。输入：
- `rmb_shift_exact_pins.txt` — 72 个经过固定 EXE 及 objdump 核验的队列/参数指令。
- `state_lifecycle_exact_pins.txt` — 69 个真实状态机和 shortTask 回调指令。
- `tests/test_native_shift_re_rmb_shift_lifecycle.py` — 8 个回归（不包含 EXE 的 CI 跳过真实文件测试）。
- `evidence/20261015_rmb_shift_queue_state_diff_static.json` — 原始 EXE 结果，脱敏、不含内存指针。

运行：`python maintenance_tools/native_shift_re/audit_rmb_shift_lifecycle.py --exe PRIVATE/Warhammer3.exe --out PRIVATE/rmb_diff.json`；`python -m unittest discover -s tests -p test_native_shift_re_rmb_shift_lifecycle.py -v`。

原始 EXE 只读审计：**72/72** 队列机器码起点、**64/64** 类型化直接 E8 MOVE 调用、**4/4** MOVE 虚表、**69/69** 状态代码起点、**8/8** E8、**6/6** JCC。更详细的独立审计与整合审计在本地联合 **32/32 PASS**（含 3 项私有 EXE 测试）。工具依赖 GNU objdump 和同目录已有的 `audit_b_member_packet_task_lifecycle.py` 提供的 OriginalEXE 类，公有 CI 不需要也不得上传原始 EXE。

**类型与因果边界：** R9B=0/!=0 表示替换/追加队列请求，不能视为 RMB/Shift 键位的绝对动态身份；新槽位初始 NULL，只有队列后续推进资格通过才有条件复用 bigTask。state1 可条件性走 state2→state3→state4 并满足普通 B 回调 tuple (4,0,3)；仍未验证同一个 shortTask 与特定玩家 Shift 的完整生命周期、成员目标代际错误或游戏修复。中文报告在 [RMB/Shift 原生差异](../../docs/current/N1_903_RMB_SHIFT_QUEUE_STATE_LIFECYCLE_20261015.md)，`native_patch_authorized=false`。

**第12轮新增类型化对象身份桥：** `audit_move_slot_shorttask_binding.py` 在原始 EXE 验证 36/36 原码与 decoded instruction starts、6/6 E8 和 Win64 栈帧别名，证明 `shortTask+0x80=&MOVE slot+0xA0`，通过 `0x02F4EFE0` 晚绑定读取该 slot bigTask；新创建路径经 `0x02F41644` 可反写 `slot+0xA0`。测试 `tests/test_native_shift_re_move_slot_shorttask_binding.py` 8项，带私有原始 EXE 时本轮四套测试整体 **40/40 PASS**，公有 CI 应跳过 4 项真实 EXE 测试。不能混淆合法的新 shortTask 与已经清退的旧 shortTask，尚无 gameplay patch。

## 2026-10-15 第13轮：队列与即时群组重建的 CFG 排除证据

新增 `audit_move_dispatch_branch_split.py` + `move_dispatch_branch_split_manifest.txt` + `tests/test_native_shift_re_move_dispatch_branch_split.py`：对用户固定 SHA Win64 原始 EXE 检验 **37/37 机器码/objdump 指令起点、17/17 E8、5/5 JCC/E9**，在同一 unwind 函数 `0x030323C8` 做保守 CFG 可达性检验。**常规队列分支**有 `0x030326BE CALL 0x02F50410`，经 `0x030326E9 JMP 0x0303296A` 直接跳过即时 `0x03032965 CALL 0x0302DB44`；**另一组模式/命令分支**才有条件 `group rebuild → route configure → member fanout`。槽位激活 `0x03025D70` 无直接调用同一 group 构造器，但读当前 `UnitRoot+0x32F8` 的空间记录（转换源 `group+0xBF0`）计算新朝向并调用路线配置，然后创建短期任务。短期任务回调晚绑定当前 group。严格控制流证明不代表用户 Shift 实机分支、root cause 或游戏补丁。

运行 `python maintenance_tools/native_shift_re/audit_move_dispatch_branch_split.py --exe PRIVATE/Warhammer3.exe --out PRIVATE/branch_split.json`，`python -m unittest discover -s tests -p test_native_shift_re_move_dispatch_branch_split.py -v`。本地详细审计 **11/11** PASS（含私有 EXE）；上传的 GitHub 合同测试另包括一个独立子用例，CI 无 EXE 应当跳过原始二进制测试。完整见 [中文报告](../../docs/current/N1_903_QUEUED_VS_IMMEDIATE_GROUP_BRANCH_20261015.md)。

**第13轮 bit2 上游字段来源新增：** `audit_move_slot_bit2_provenance.py` 静态验证 `0x030323FF RDI=command descriptor`，`0x030326DB R9=RDI`，`0x030090BC → 0x03009100` 原生 bitwise copier 从 `descriptor+0x5A` 搬运低7位到 `MOVEslot+0x9A`；`0x03032679 OR [descriptor+0x5A],0x06` 在部分预处理支设置 bit2，`0x03025E69 JE` 只允许 bit2=0 的后继激活选择 group+0xBF0 采样分支。新增源审计 **19/19 指令、2/2 E8、3/3 JCC**，本地联合两个模块 22/22 测试 PASS（2 个私有原始 EXE 测试）；不含 EXE 的 CI 跳过私有检查。运行 `python maintenance_tools/native_shift_re/audit_move_slot_bit2_provenance.py --exe PRIVATE/Warhammer3.exe --out PRIVATE/bit2.json`，`python -m unittest discover -s tests -p test_native_shift_re_move_slot_bit2_provenance.py -v`。原分支审计扩展后共 **39/39 指令、17/17 E8、6/6 JCC/E9**。不要把 bit2 当 Shift 键码，禁止更改游戏 EXE。

**第13轮最后新增已证参数分叉：** `0x03025E76 MOVZX R8D,[MOVE slot+0x98] → 0x03025E91 CALL 0x0301287C` 与 `0x03026015 MOVZX R8D,AX`（由当前 Group 空间参考计算）`→0x03026022 CALL 0x0301287C` 是队列后继 MOVE 的不同 R8 朝向来源。真实 EXE 第一审计提升为 `41/41 machine code/starts, 17/17 E8, 6/6 branches`；联合两套本地 `23/23 PASS`，共2项真实原始 EXE。此参数差异不能解释为玩家 Shift/RMB 的固有键位差异，也不授权 patch。

## 2026-10-15 第14轮：从两种后继朝向到路线节点与 A 类成员发包

`audit_route_heading_to_member.py` 针对固定原始 SHA `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`，只读检查 **83/83 opcode/objdump starts、15/15 E8、5/5 JCC、1/1 具体成员 vtable**，含两处无 unwind 叶函数的定界检查；本地完整 17/17 回归通过（含真实原始 EXE），公开 CI 缺 EXE 时必须跳过真实二进制测试。

已证数据边：`0x0301287C R8W → 0x030ECAB0 record+0x38 → 0x030EC9EC node+0x58`，在原生 gate 下由 `0x030FDA9C` 生成 node+0x70；同一源还写入 `routeDescriptor+0x44`，并挂在 `UnitRoot+0x270`。即时路径使用 descriptor+0x18→node+0x70，shortTask 的 A 路径仅当临时参数没提供朝向时读取 descriptor+0x44；B 分支不可归并。见 [中文报告](../../docs/current/N1_903_R8_HEADING_TO_MEMBER_A_FANOUT_20261015.md)。严格禁用 gameplay patch，不上传原始 EXE/内存指针。命令：`python maintenance_tools/native_shift_re/audit_route_heading_to_member.py --exe PRIVATE/Warhammer3.exe --out PRIVATE/r14.json`；测试：`python -m unittest discover -s tests -p test_native_shift_re_route_heading_to_member.py -v`。
