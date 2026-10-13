# N1 9.0.3 — 双工厂注册表反向引用审计（2026-10-13）

## 本次落地的源码和证据等级

新增 `maintenance_tools/native_shift_re/audit_factory_registry_xrefs.py` 与
`tests/test_native_shift_re_factory_registry_xrefs.py`。目的是找两类工厂
注册指针的实际代码消费者，而不是重复数 `+0x100` 函数槽。

**可独立由已有受守卫的机器码计算的四个 RIP 目标：**

| LEA 指令 RVA | 目标注册地址 RVA |
| --- | --- |
| `0x0327711C` | `0x03D19C08` |
| `0x03277129` | `0x03D19C10` |
| `0x03277168` | `0x03D19A88` |
| `0x03277224` | `0x03D19A88` |

这些是已有 `audit_two_handler_factory_origins.py` 精确字节的**独立
RIP-relative 反解**；不是新游戏实机事件。尤其 `0x03D19C08` 与
`0x03D19C10` 在这一步仍不可合并为同一工厂身份。

## 具体施工

1. 原始游戏 EXE 经 `StrictPE` 完整 SHA256
   `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`
   及 x64 PE、ImageBase 检查；先重跑已有工厂校验。
2. 使用有限 x64 RIP-relative 指令模式扫描可执行节；对每一个匹配，
   要求属于真实 unwind 函数，并且是 objdump 的**真实指令起点**。
3. 对非可执行节枚举八字节对齐的静态注册引用，单独报告，绝不将
   数据引用视为调用边或实际类型分发。
4. 输出代码引用的 RVA、函数归属、反汇编行与目标注册 RVA。输出不含
   游戏运行时指针，也不触碰原 EXE 和游戏进程。

运行方式：

```powershell
python maintenance_tools/native_shift_re/audit_factory_registry_xrefs.py --exe "C:\Path\Warhammer3.exe" --out "N1_outputs\factory_registry_xrefs.json"
```

## 本会话实际完成与未完成

- 已实际执行**5/5 离线合成单元测试 PASS**，覆盖 signed RIP displacement、
  四个目标、嵌套字节假阳性、独立数据指针、不同注册身份。
- 本会话运行环境没有固定 SHA 的原始 EXE，因此**尚未执行这一新增
  全文件反向引用扫描**，没有宣称发现新的 caller RVA 或完整 parent 来源。
- 该模式扫描并非全面 x64 反汇编：不覆盖其他寻址指令、跨无 unwind
  叶函数等情形；结果为经过指令边界核对的**静态引用候选**。
- 不确定 `parent+0x50/+0x60/+0x68` 到 `MOVE slot+0xA0`
  是否有别名关系，也不确定类型谓词与用户 Shift 实例的联系。

下一条真正可关闭的边：由反向引用所得函数定位注册表**消费者和
parent 实际构造器**，证实它获取的对象地址是否来自
`MOVE slot (vtable 0x0390B4F0) +0xA0`，而后再区分
inherited state=1 与 fresh state=0 的成员目标分配。
没有此边，不发布 Native Patch，也不让玩家重复验证挤压。


## 2026-10-13 原始 EXE 实跑复核和修正（本次对话）

本次用户重新提供 `Warhammer3.zip`，内含 `Warhammer3.exe`，本地独立
SHA256 实测 **完全匹配**固定 9.0.3。实测 **39/39 固定机器码和指令边界、
9/9 E8、12/12 类型化指针、4/4 RIP 目标 PASS**。此前的
`audit_two_handler_factory_origins.py` 把合法无 unwind 叶函数
`0x0327711C..0x0327713C`、`0x0327714C..0x03277186`、
`0x03277214..0x0327724E` 漏在区间识别之外；
因此旧工具在真的拿到 EXE 时会 fail closed。本次修复为受固定地址和
机器码双重保护的显式 leaf span，**不放开任何未知指令地址**。
`audit_factory_registry_xrefs.py` 也修复这个上游依赖与叶函数过滤问题。

新增可复核的区别：
- `0x03D19A88` 指向 `0x03940ED8`，其中回调 `+8` 为 A 工厂 `0x0326F0DC`；
- `0x03D19C10` 指向 `0x03941400`，其中回调 `+8` 为 B 工厂 `0x0326F07C`；
- **`0x03D19C08` 指向的是另一张 `0x03941388` 描述符**，其 `+8` 是
  `0x0326EF10`，不能把整个 B-family 的谓词直接归为 B 工厂实例。

此外直接检查 `0x0326FFF4` 和 `0x0326FF60` 两条工厂调度回调：
二者都从 `parent+0x10` 取上游调度器，以 `+0x898` 的值计算索引，
读 `+0x818 + index*16` 并与当前 parent 地址比较。这是真实共享的
上游 **dispatcher 结构布局**。它不同于已确认的 MOVE 槽位队列
`+0x2D10`，不能因同样叫 queue 就将其强行当成 MOVE task。

当前尚未完成 `MOVE slot+0xA0` 至工厂 parent 的指针同一性连接。
原始 EXE 验证仍属于 **静态逆向**，不是 Shift 现场分支记录，也不是 Native
游戏修复。此次不上传 EXE、原始用户 JSONL 或发布 gameplay patch。
