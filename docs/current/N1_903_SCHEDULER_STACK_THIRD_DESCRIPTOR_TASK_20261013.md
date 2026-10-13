# N1 9.0.3 — 处理器调度栈与独立任务描述符边界（2026-10-13）

## 原始 EXE 新静态验证

原始 SHA256 \`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a\`。
这次重新解压用户提供的 \`Warhammer3.zip\`，独立检查 ELF 工具 GNU objdump 与
x64 PE 原始 unwind 指令归属：**46/46 opcode 及指令起点、5/5 E8、
5/5 typed callback pointer PASS**；本地 **7/7 回归 PASS**（含
实际原始 EXE）。这仅是原始机器码静态证明，并非游戏现场分支取证。

### 1. A/B 同一种调度器槽位布局，而不是 Shift 专用路点队列

- A 的回调 \`0x0326FFF4\`、B 的 \`0x0326FF60\`：
  \`parent+0x10\` 取调度器；\`dispatcher+0x898\` 读计数、
  \`dispatcher+0x818+(count-1)*16\` 比较当前 parent 的指针。
  因此二者确实依赖“当前处理对象是不是栈顶槽位”。
- \`0x0327C6B0\` 检查调度器 \`+0x8A8\` 门槛和 \`+0x8AC\`
  索引，再 \`CALL 0x030DBF3C\`。
- \`0x030DBF3C\` 从 \`+0x818\` 起处理每个 16 字节记录：
  前八字节为对象指针，后面 \`+8\` 是移除时计入
  \`+0x89C\` 减法、\`+0x8A0\` 加法的数值，并令
  \`+0x898 -= 1\`。
- \`0x030C47A4\` 析构时传 \`owner+0x30\` 给相同清退函数，
  随后读取 \`owner+0x8C8\`；\`0x30+0x898=0x8C8\`。
  这是**同一嵌入式调度栈的结构归属关系**，并非与
  MOVE queue \`+0x2D10\` 的 pointer alias 证明。

### 2. 靠近原生任务的真实调用，但属于第三种描述符

\`\`\`text
descriptor slot 0x039407A8 = 0x032701C4
   ├─ E8 0x032701F2 -> 0x0327C648
   │     └─ read [object+0x88] -> test pointed +0x20==4 / +0x24
   └─ 0x0327020D read [object+0x88]
         -> E8 0x03270229 -> 0x0311C5E0
               └─ checks +0x20/+0x24/+0x25
                  and passes task+0x168 to 0x0311C674
\`\`\`

\`0x030EE850\` MOVE 大任务构造器同样初始化 \`+0x20/+0x24/+0x168\`；
**只证明字段与生命周期形态高度一致**，不证明被读取的
\`object+0x88\` 指针就是 \`MOVE slot+0xA0\` 指针。

第三描述符 \`0x039407A8\` 不是 A 的 \`0x03940EE0\`、
也不是 B 的 \`0x03941408\`。因此不能将这条链直接归到两套
工厂，更不能当作 RMB/Shift 输入身份。这是本次主要防误判结论。

## 工程交付

- 新增 \`maintenance_tools/native_shift_re/audit_scheduler_task_boundary.py\`
  严格只读 SHA / PE / unwind / objdump / E8 / typed-pointer 守卫。
- 新增 \`tests/test_native_shift_re_scheduler_task_boundary.py\`；
  7 项本地 PASS，公开 CI 的真 EXE 一项按预期跳过。
- 新增脱敏静态证据 JSON；没有向 GitHub 上传原始 EXE、运行时指针，
  或修改 Native 游戏行为。
- **没有找到确证的 MOVE slot→Factory A/B parent 同一实例引用；
  不能制作根因未定型的 Native 补丁。**

下一步应继续沿第三描述符 \`object+0x88\` 的构造器/赋值点，
通过真实 pointer provenance 比较 MOVE slot+0xA0，验证是否存在
共用任务类型，再进一步检查工厂 A/B 的 parent 各自引用。
