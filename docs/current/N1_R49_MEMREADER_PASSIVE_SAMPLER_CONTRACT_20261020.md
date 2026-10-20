# Better Shift Command — R49 / 本对话第16轮

**主题：核对用户提交的 memreader Plus 0.13.0 与 Derpy Third-Person Battles 的真实代码，并将 R47 无 Hook 采样器升级为带时间预算、全成员数组守卫的严格只读原型。**

> 截至 2026-10-20：只读静态核验 + Lua API 模拟测试 + Python 离线数据协议测试。**没有运行 memreader DLL、没有加载到 Warhammer III、没有安装 Hook、没有修改原生指令或修复挤压。** 研究限定为 Windows x64 对应原始 EXE，所有地址都是 RVA。

## 一、这一轮为什么必须先纠正 R47

R47 可以读取模型 XYZ、成员目标/增量、动作虚表，但发现四个需要修正的实际设计弱点：

1. **采样时间缺少真实耗时**：`time_ms` 来自调用者，旧实现没有检查处理一个兵牌所需的真实时间，不能把同一记录里各成员当作同时取得。
2. **成员清单验证范围不足**：R47 只在采样结束检查成员数量、数组指针和所抽成员。其他未抽中的成员可能重排而没有被发现。
3. **成员类型覆盖与可见性不足**：只接受单一普通成员虚表 `0x03912950`，会静默排除同一个兵牌中的其它派生类型；且跨采样同地址可能属于不同生命周期。
4. **错误路径有泄漏与误解风险**：`pcall` 原始异常可能含进程指针，若被原样写入日志不合适；只能对完整记录使用有效的数据协议，不能把所有已通过的快照视为原子数据。

## 二、从实际文件验证的 API 和对象模型

**实际输入**（均未复制进研究包）：

- `Warhammer3.exe` SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`；PE64 ImageBase `0x140000000`、PE 时间戳 `0x6ACEC6F4`。
- 用户提供的 `derpy_third_person.zip` 的 .pack SHA256 `a40d086d57f8d4857caff782680b62f490cf5e9d772723c9b50f69bee9e32176`。源码 `script/derpy_tp/platform.lua` 明确读取 `BattleUnit userdata+0x08`、原生 Unit object 的 `+0xA4` 数量与 `+0xA8` 成员数组，并读取成员 `+0x88/+0x90`。
- 用户提供的 `memreader_plus.zip` 的 .pack SHA256 `9e63d8feacb92c0b35ec327884bda558fe453dbdba945ee9d9c848deec1f7878`。`.pack` 发行标志为 `0_13_0`，包装器在 `_G.memreader_plus_release` 中记录版本，内嵌 DLL 字符串包含 `ticks` / `elapsed_us` / `read` / `read_original` / `hook_info` / `ud_topointer`。**没有执行 DLL，字符串存在不等于游戏运行验证。**
- 官方公开 API 定义：`ticks()` 返回 QueryPerformanceCounter 类型化 uint64；`elapsed_us(ticks)` 转成微秒。`read(p,offset,nbytes)` 返回原始字节字符串、`read_original` 返回 memreader Plus 追踪的原始指令、Hook 后 `read` 仍可看到当前跳板。参见 https://github.com/PKozdra/memreader_plus 。

本地对真实 EXE 的严格只读核验：成员 Tick RVA `0x03086F04` 开头 **7/7 字节**；Derpy 排队动作分支 RVA `0x03087378` **18/18 字节**；7 类动作 **14/14 虚表槽**；普通成员 **2/2 虚表槽（Tick `+0x18`、运动更新 `+0x20`）**。

## 三、R49 已实际实现

### 1. `bsc_r49_guarded_passive_sampler_research.lua`

- 仅允许手动调用 `M.sample(unit, opts)`，既不注册游戏事件也不定时调用，不调用 `mr.write`/`mr.call`/`mr.hook`/`mr.patcher`。
- 先检查 PE32+ 签名与时间戳、`SizeOfImage`，然后检查 Tick/Gate 当前和原始字节以及 `hook_info`，验证普通成员虚表两个方法槽。所有大型地址通过 0x10000 拆分，避免 CA Lua float32 大整数精度问题。
- 限额：最多一个单位、500 名成员、每次最多 32 行（默认16）、**同一次采集上限 5000 微秒**，日志时间戳和样本编号必须显式给定并单调递增。
- 在读取成员前后分别对完整 `member_array` 的 **n×8 原始字节**进行对照，并检查有无空指针及重复成员指针。额外复查数量、数组对象以及已选择成员的指针和虚表，普通成员还复查动作虚表与动作标志。
- 每行记录位置取得时的 `read_offset_us`；整组输出 `read_duration_us`，供离线拒绝过长的采样时差。
- 遇到非普通成员虚表但类指针仍位于游戏模块内时，只保留 **position-only** 信息，不读取未经该类型审计的动作/目标字段；这与 Derpy 的混编兵牌观察一致，但不表示未知成员已完整定型。
- 同单位清单改变、数组指针变化或采样间隔超过250 ms时，重建匿名 `roster_epoch`；原始指针/完整清单只在 Lua 局部状态中使用，日志不输出。
- 不输出 Native 异常原文，只返回脱敏状态码，避免日志携带可能的进程指针。

### 2. `r49_spatial_evidence_preflight.py`

- 复用 R47 纯离线空间分析，不伪造原生目标或动作数据。
- 检查完整清单守卫、真实采集耗时/逐成员偏移、匿名 ID 代际。
- **不连接不同 roster_epoch 的样本**；间隔超过250 ms或同次采样内最后一人与第一人的读时差大于2500 µs，则拒绝该间隔。
- 拒绝混入原始指针、非有限坐标与无法定型成员伪动作；只输出空间候选和刚体拟合。
- 明确输出 `SEQUENTIAL_NEAR_TIME_PASSIVE_SPATIAL_ONLY`：即使采样通过，仍不能证明原子快照、实际身体碰撞、旧新目标冲突或任何 Shift 原生错误条件。

## 四、验证证据与限制

1. **真实用户三份文件静态检查**：`audit_r49_sampler_contract.py` 通过 EXE 完整 SHA、两个机器码部位和 16 个虚表槽；检查用户 .pack 对应发行加载器与可识别的接口名字。
2. **真正运行 Lua 原型**：使用本地 Lua 5.3 `texlua` 加严格的 memreader 模拟器，测试 typed pointer 算术、完整 roster 变更、对象池 epoch、Derpy Code Cave、patch live bytes、时间预算、NaN、动作变化、缺少 API、错误回退等。**20/20 模拟用例 PASS**。Lua 5.3 不是游戏原生 Lua 5.1，实际接入仍缺少游戏内 smoke test。
3. **Python 研究回归**：R49 API+空间验证 20 个 unittest；R47 历史 19 项与 R48 历史 19 项也重新运行通过。
4. **仍不可证明**：`pcall` 无法消除另一个线程同时析构内存的风险；前后 roster 完全相同不能排除 ABA 地址复用；时间戳足够近不等于同时快照；该工具尚未安装／运行于 Windows 游戏中。

## 五、下一步怎么实质缩短查错链

- 不再大量 Hook `member Tick` 或在游戏中运行 Derpy。先将 sampler 视为 **实验性、手动调用、不随 MOD 自动加载** 的工具候选；只有验证加载时序/单人只读安全后才考虑制作可安装测试包。
- 最小对照应比较同一单位中空间最近的几名成员：`position_xyz`、`action`、`flags_108`、`flags_155`、`pending_delta_xyz`、`motion_xz`、局部目标与参考框架是否存在。发生约180°折返时优先找**非刚体接近 + 相同行动的近邻**，或**行动相异 + 不同增量处理**。
- 所有目标带参考框架时，需要额外的原生世界坐标解析，不能把 `stored_goal_xz` 当作真实 world goal；必须先核查 `member+0x1F0` 的生命周期。
- 本轮不需要用户重复证明挤压存在，不修改 `main`，不授权 Native gameplay patch。

**状态：`read_only_mock=PASS`, `new_build_static=PASS`, `memreader_in_game_tested=false`, `real_shift_trace_collected=false`, `root_cause_proven=false`, `gameplay_patch_authorized=false`.**
