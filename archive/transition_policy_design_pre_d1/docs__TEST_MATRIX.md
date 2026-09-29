# Test Matrix — CorePath RC8 PREBUILD

This matrix records **current candidate gates only**. Historical PASS results do not automatically carry forward to RC8 unless listed here. Research fixture PASS does not promote a semantic assumption into production.

| Gate | Current result | Meaning |
|---|---:|---|
| CorePath controller jobs | 19/19 PASS | offline Lua/Python regression suite |
| Mutation suite | 40/40 CAUGHT | deliberately broken core invariants detected |
| Portable Native CTest | 13/13 PASS | Linux portable fixtures |
| ASan/UBSan CTest | 13/13 PASS | no sanitizer finding in portable fixtures |
| Source prebuild contract | PASS | 16 mandatory + 2 optional static sites, quarantine markers, provenance |
| 2026-09-29 top-level Move/Attack outcome dataflow audit | PASS (with report-control-flow caveat retained) | allocator ABI + exact top-level constructors + Full Move VTable `0x03910AA8` + Attack VTable `0x03910228` verified; queue-full/`ACCEPTED_NO_SLOT` remains intentionally supported because the supplied report contains a branch/return inconsistency |
| Windows VS2019 v142 + MASM | PENDING | must be performed by BuildOnly agent |
| Windows CTest + mid-hook smoke | PENDING | must pass before candidate pack |
| Current EXE inspect | PENDING ON WINDOWS | must show SHA match and 16/16 core |
| Deterministic candidate pack | PENDING WINDOWS DLL | embedded DLL/MinHook must exact-match |
| WH3 CorePath runtime smoke | PENDING | final go/no-go for install candidate |

Physical component-layout fixture tests remain in Native CTest for research-code safety. Passing them does **not** prove WH3 physical layout semantics and is not listed as a release proof.
