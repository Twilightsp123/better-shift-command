# BSC 第25轮 / R59 — Derpy walk_b、CA walk_a 与 B2 action：缓存字段归属纠错

日期：2026-10-20。任务仍是改善 CA 原生 Shift MOVE 连续折返时兵牌内部运动的流畅性和协调性；**不得使用 Lua 替代 Shift**。本轮只使用用户的实际 `Warhammer3.exe`（SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`）、Derpy 已提取的原生代码/技术档案进行静态复核；不注入，不改游戏文件。

## 1. 纠正 R58 的核心原码归属错误（这是真正新发现）

R58 正确认定 Derpy 的工作线程代码洞会在其选定的 `walk_b` 动作输入变化时条件性地清零 `member+0x3C0`（以 `member+0x328` 为 action 基址，就是 `action+0x98`）。**但 R58 错误地把 `0x0325B05A/108/114/1EF/1F6/395` 的 action+0x98 读写归属于 walk_b 调用的 `0x0325AE78`。**

本轮使用 **PE x64 unwind 原生函数表 + GNU objdump 全函数指令起点 + 整段可执行代码 E8 真实调用者反向扫描**，确认两个函数完全不同：

| CA action | 虚表 `+0x10` | 下一层 E8 | 对应函数真实 PE 范围 |
|---|---|---|---|
| `walk_a`，虚表 `0x03919350` | `0x03264B70` | `0x03264BF7 → 0x0325B008` | **`0x0325B008..0x0325B3D2`** |
| `walk_b`，虚表 `0x03AE2400` | `0x03262850` | `0x032628D9 → 0x0325AE78` | **`0x0325AE78..0x0325B005`** |

`0x0325AE78` 在 `0x0325B004` 明确 `RET`，其后 `0x0325B008` 才是新函数入口；前者本体没有以自身 action 对象访问 `+0x98`。后者在 `0x0325B035` 把传入 `RCX` 保存到 `RBX`，其六处确认读/写 `action+0x98` 的指令属于**由 walk_a 直接调用的 handler**，而不是 walk_b 这条直接调用。

整个原生 `.udata` 扫描：按完整 E8 rel32 算出目标，且要求 PE unwind 范围内 GNU objdump 真正的 `call` 指令，**`0x0325B008` 唯一直接调用者为 `0x03264BF7`；`0x0325AE78` 唯一直接调用者为 `0x032628D9`**。

另纠正一个很易误读的 `+0x98`：在 `walk_b+0x10` 的 `0x0326296E`，读取的是 `[RDX+0x98]`，但上游 `0x0326295D` 从 `action+0x28` 取得上级对象，`0x03262967` 再取其 `+0x440`；此处 RDX **不是 action 指针**，而是上级上下文对象。不要据此称 walk_b 消费 `action+0x98`。

**可证范围**：R58 所指的 direct walk_b→handler+0x98 链被否定；没有证明这个字段在全程序所有间接路径中都无作用，也没有证明 Derpy 的清零操作在其游戏场景中完全无效。Derpy 代码洞确实写该偏移的事实保持不变。R58 的静态测试仍能通过原字节守卫，却无法替代**对象与函数身份验证**；本轮明确修正文档语义。

## 2. B2 packet action 不能套用 walk_a 的缓存字段

B2 实际普通成员接收器 `0x03070A48` 的两个已检查 packet-action 分支：

- 特殊 kind 分支：`0x03070BCB` 先清旧 action → `0x03070BF8` 调 `0x0324E2C8` 构造特殊 action，安装 `0x039199F8` 虚表，构造时 `0x0324E2E8` 写 `action+0x40=0`。
- 普通 kind 分支：`0x03070BFF` 先清旧 action → `0x03070C2D` 调 `0x0324D994` 构造普通 action，安装 `0x03919B28` 虚表，构造时 `0x0324D9B4` 写 `action+0x40=0`。
- 这两个构造器都把输入的 **8 字节**写入 `action+0x38`，不是 R44 state16 的三个 float；和 `walk_a` 的 `action+0x98` 更不是同一个对象字段。

之后 B2 普通 `virtual+0x10=0x03261688` 根据状态在 `0x0326188E/8A9/8E4/8F4/0x03261BA4` 等处操作**自身 `+0x40`**；B2 特殊 `virtual+0x10=0x03263AF8` 在 `0x03263BA1/BBC/BFB/C0F/C85/CA0` 等处操作相应状态字节。这里存在自有状态机制，但没有足够证据将其命名为“路线缓存失效标志”。

**针对直接构造 B2 action 的这两条分支**，新建时先清旧 action 并将自身 `+0x40` 初始化为0，所以没有证据说它们从旧 B2 实例继承一个未清的 `+0x40` 字节。其它异步/内嵌 packet 路线、间接分发和后续 Tick 尚未排除。

## 3. 对“转弯更流畅”的实际影响

先前设想的“参照 Derpy，只要 Shift 换段就全局清 `member+0x3C0`”现在必须**撤销为未证假说**，因为真正的 `action+0x98` 处理器属于 walk_a 的已验证直接链，而 B2 两种 packet action 使用自己的结构与条件。

现在更应该做的验证是：

1. 对实际 queued Shift MOVE 的某个已定型 member action，弄清其**真实具体虚表类型**，而非仅有 `member+0x330` 指针；分辨 walk_a、walk_b、B2 ordinary/special 和其它 action。
2. 将新后继 MOVE 的**预存/实时 Group 朝向 → packet 目标 → action 实际消费 → member+0x1E0 世界目标 → 积分器**按同一实例关联。
3. 优先找到：**哪种 action 能在目标更新之后仍保留不相容的真实路径状态**；如果新建已自动清理/初始化，就停止这个分支，不做猜测性全局清零。
4. 对“更流畅”保持 CA 原生队列、渐进转向、避障和 Shift ATTACK，不发布会导致一步一停的替代队列。

只凭字段偏移绝对不能打补丁；这次 R58 的原码归属错误就是明确的反例。

## 4. 审计与回归等级

新完整 SHA 新版 EXE：**59/59 指令原码与 objdump 起点，8/8 直接调用边，5/5 类型化虚表槽，6 个重要 unwind 函数范围**。两条 handler 的唯一直接 E8 调用者还经过整个可执行 `.udata` 的真实指令验证。

R59 本地标准库回归：**15/15 PASS**（其中 1 项使用原始 EXE）。无私有 EXE：**14 PASS / 1 SKIP**。纯静态测试不是新游戏内命中，更不是修复效果测试。

- `audit_r59_action_cache_provenance.py`：只读 PE/unwind/objdump/E8/typed-field 审计器，严格 SHA。
- `r59_pe_trace.py`：PE 读取、unwind 归属及真实反汇编帮助函数。
- `r59_exact_pins.txt`：59 条原始指令与语义摘录。
- `test_r59.py`：15 条类型/控制流/真实EXE回归。
- `static_evidence.json`：脱敏的静态验证结果。
- `native_action_boundary_excerpt.txt`：关键原码连续区段与对象来源。

**root_cause_proven=false；native_patch_authorized=false；in_game_tested=false。** 不修改主分支，也不分发游戏 EXE 或 Derpy 完整第三方源代码。
