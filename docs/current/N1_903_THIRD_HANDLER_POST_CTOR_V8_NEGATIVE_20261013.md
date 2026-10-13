# N1 9.0.3 — 第三处理器构造后 virtual+8 空操作的原生负证据（2026-10-13）

## 这次实际排除了什么

在 SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` 的原始 `Warhammer3.exe` 上，逐一核对前轮找到的 **16 条 `0x0326581C` 直接构造调用**：

- 构造对象真实虚表为 `0x03ADE428`；该表 `+0x08` 指针为 `0x008D3280`。
- `0x008D3280` 的原始指令为 `c2 00 00`（`ret 0`），不是另一套 MOVE 成员目标分配器。
- 16 条创建路径的构造调用之后，均存在同一函数内通过返回对象虚表 `+0x08` 的分发：**12 条尾跳 `jmp`，4 条 `call`**。
- 每条路径的构造器返回到 `virtual+0x08` 之间，经原始 PE unwind 和 GNU objdump 指令边界核验，没有直接 `[register+0x88]` 操作数。
- 同一真实对象类型的析构器 `0x03266FC0` 重装 `0x03ADE428 / 0x03ADE520` 虚表，释放/清理 `+0x98` 与 `+0x80` 相关资源；其函数体没有直接 `+0x88` 操作数。

已在用户原始 EXE 实际执行独立只读审计，**16/16 完整构造→virtual+8 有界路径、4/4 析构器指令守卫 PASS**。同时本地合成/真实 EXE 回归通过；原始 EXE 不提交公开仓库。

## 必须保留的限制

上述**不是全局 `object+0x88` 非空写入不可能的证明**。它只排除了已检查的 16 条创建调用返回后到 `virtual+8` 的直接字段写入，以及所检查析构函数里的直接访问。仍有间接函数、类型转换、内存复制、其他时序回调可能改变 `+0x88`。构造器本身还调用了其他原生函数，不能凭此推导任意时刻均为空。

不能据此宣称 `object+0x88` 就是或不是 `MOVE slot+0xA0`，也不能宣称第三类型属于 RMB/Shift 的某个键位。**后续不必再次从这 16 条构造器尾部寻找直接 setter**；应该查真正的 type-aware lifecycle / attach API 以及和 MOVE 大任务的具体引用传递。

## 施工产物与使用

- `maintenance_tools/native_shift_re/audit_third_handler_post_ctor_v8.py`：固定 EXE SHA、真实反汇编指令起点、16 条 E8、16 个 virtual+8、析构器真实指令守卫。
- `tests/test_native_shift_re_third_handler_post_ctor_v8.py`：合成 fail-closed 测试及私有原始 EXE 可选测试。
- `maintenance_tools/native_shift_re/evidence/20261013_third_handler_post_ctor_v8_static.json`：脱敏证据。

命令：`python maintenance_tools/native_shift_re/audit_third_handler_post_ctor_v8.py --exe PATH_TO_ORIGINAL_EXE --out PRIVATE_REPORT.json`

未修改游戏 EXE、Native gameplay、Shift 队列、motor goal 或 main；未上传原始游戏文件及用户带指针日志。