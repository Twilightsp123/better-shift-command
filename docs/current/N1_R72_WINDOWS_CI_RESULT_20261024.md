# R72 Windows MSVC / MASM CI verification (2026-10-24)

Two separate GitHub Actions runs, neither loaded or modified Total War WARHAMMER III.

| GitHub Actions run | Commit | Linux | Windows | Result |
|---|---|---|---|---|
| [40062212819](https://github.com/Twilightsp123/better-shift-command/actions/runs/40062212819) | 3ed42800c2be | 2/2 CTest PASS | Compile FAILED | Build flags mistakenly applied to MASM, and MSVC C4324 intentional padding treated as error |
| [40062382966](https://github.com/Twilightsp123/better-shift-command/actions/runs/40062382966) | cdea5efcc793 | 2/2 CTest PASS | **3/3 CTest PASS** | Fixed target language compiler flags |

Windows-2022 x64 build succeeded in compiling both a synthetic 64-bit C++ lock-free ring and an owned MASM PROC FRAME with unwind metadata. The three executed CTest suites were r72_ring_mpsc, r72_win64_fixture, and r72_protocol. The Win64 fixture tests controlled callback-window flags, some nonvolatile register/XMM preservation, RtlLookupFunctionEntry, and synthetic SEH RaiseException from inside a call crossing an owned MASM function.

This is **NOT a live or simulated in-process game Hook**. It does not prove stolen prologue relocation, full volatile state preservation at WH3's Tick 0x03086F04, arbitrary worker thread lifetime, object generation tracking, live thread suspension, or roll-backability against memreader Plus/Derpy. Do not promote from Windows test fixture to a gameplay probe. LIVE_HOOK_NOT_AUTHORIZED, ROOT_CAUSE_NOT_PROVEN, MAIN_UNCHANGED.
