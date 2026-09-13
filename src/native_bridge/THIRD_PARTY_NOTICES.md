# 来源说明

`baseline/` 的两份 DLL 和 Lua/pack 均为用户提供的既有本机基线，按原字节保留用于核验与回退，不声称本轮编译生成它们。

`minhook.x64.dll` 是用户提供的 MinHook 后端；本工程仅动态调用其接口。原项目为 TsudaKageyu/MinHook。此交付用于用户当前私有 Mod 工程；若另行公开分发二进制，应同时保留对应版本原项目的完整许可及第三方声明。

`evidence/input_archives/` 是用户上传的局部证据归档，没有包含完整 Warhammer3.exe。里面的自然语言报告仅作为历史输入保留，当前工程不将其“100%”断言视为可执行证明。
