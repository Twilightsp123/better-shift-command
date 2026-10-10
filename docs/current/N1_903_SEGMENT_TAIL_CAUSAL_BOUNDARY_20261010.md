# N1 native segment target generation: exact-build executable evidence (2026-10-10)

**Status:** STATIC PASS (original EXE) / OFFLINE PASS / WINDOWS NOT BUILT / WH3 NOT RUN. Product bug existence is already accepted. Do not ask user for further game trials until an evidence-backed repair and Windows test exist.

Target EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, image base `0x140000000`. RVA notation throughout.

## Confirmed original producer/consumer

- Conditional real MOVE task calls `0x03279E40 → 0x030D554C → 0x030D5490`. In the latter, a group-specific virtual `+0x48` creates one 48-byte record for each member. `0x02F5F868` copies a record into a member task **before** virtual `+0x368` dispatch. Original V3 did not capture this handler: conditional reachability does NOT establish taken branch.
- Mode 0 strategy `0x0390F558+0x48 → 0x030C9A64` enters `0x030DBFD4`, which invokes per-segment generators `0x030DC0A0 / 0x030DC304`. These contain measured segment direction, distance projections and model spacing; they are not just blind grid rotations.
- At `0x030DC075–0x030DC085`, if member-output quota remains after all path segments, native loops `sink.vtable+0x20`. One instantiated sink at `0x03ACFD48+0x20` resolves to `0x030D1F60`, which duplicates the last 48-byte record through `0x030BE544`. Different members may receive identical *target records* if quota is underfilled. This is a code-level possibility, **not** proven to have fired in the user's V3 compressed turn.
- The vtable +0x20 slot in **six** distinct emitters resolves to `0x030D1F60`; global detouring the clone primitive cannot be isolated to the one observed formation strategy.
- Separate constructor-grounded UnitRoot virtual `0x03908718+0x248 → 0x030135E0` invokes the same Mode 0 target generator at `0x0301385E / 0x03013B5C`, and sends through `0x02E0AFDC / 0x02DED114` without passing `0x030D5490`. Historical zero-hit instrumentation therefore does not globally exclude Mode 0 target generation; activation in V3 is still unproved.

**Negative controls / rejected fixes:** no global hook on `0x030D1F60`; no blind removal of cloned records (downstream `member[i]`/48-byte indexing needs cardinality); pure Hungarian permutation preserves the count of duplicate target destinations; `member+0x104` actor mode 0 does not establish the separate formation strategy mode 0; `member+0x2E0` attachment/follower relation is not a proven universal soldier motor.

## Current limited repair policy

The concrete local boundary worth testing **offline first** is the *segment emission quota and destination cardinality policy before native per-member task copy*. A valid delta must preserve the exact output member count while preventing unsafe duplicate or crossing goals, maintain original guide-bends and original order lifecycle, and avoid changes to six unrelated emitter types. Do **not** ship a patch on this hypothesis alone. If original input geometry shows the quota can be fully satisfied without cloned destinations but V3 still compresses, reject the clone hypothesis and follow the actual local steering/avoidance producer rather than tweaking a magic distance constant.

**Remaining causal blocker:** which formation generator and branch the unit followed during the real V3 Shift turn, and whether target duplication versus follower steering produced its measured crowding. The evidence in the originally provided V3 trace does not identify a generated 48-byte target array. It is not acceptable to claim an experimental native fix is safe on static linkage alone.

## Actual code, reproducibility and test grade

- `maintenance_tools/native_shift_re/audit_903_segment_tail_multi_path.py`: read-only exact-SHA 13 native E8, 10 instruction and five vtable guard checks; six-shared-emitter negative control.
- `tests/test_native_shift_re_segment_tail_multi_path.py`: six synthetic PE/API regression tests; existing N1 GitHub Actions success.
- Downloadable original-EXE investigation archive, independently unpacked/smoke-tested: `BSC_N1_903_NATIVE_SEGMENT_TARGET_AUDIT_20261010.zip` (supplied in conversation): two more strict exact-EXE auditors, original disassembly, source, offline model, 22/22 tests including two pinned-EXE runs, SHA256 manifest. **No EXE copy, no DLL, no PACK.**

This is a concrete static producer/consumer and negative-fix result, **not completed gameplay repair**.
