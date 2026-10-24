# BSC R70 — same-member handler-to-projection gate; Shift reset hypothesis blocked (2026-10-24)

**Result: bounded negative causal decision, not a gameplay fix.** The exact licensed user WH3 executable is 232531920 bytes, SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`; image base `0x140000000`. All addresses below are RVAs.

## What is newly verified in original executable

Within the original PE UNWIND function `0x03072EB8..0x03073255`, `0x03072EBE` preserves `RCX=member` in RBX. Conditional on the preceding VTable `+0x88` return not being `0x81`, `0x03072EFD` reloads `RCX=RBX` and `0x03072F00` directly calls **`0x0307DB60`**. Later (on a branch that does not jump away due to `member+0x898`, and with `member+0xB11` branch flags permitting), `0x030731F8` *again explicitly* loads `RCX=RBX`, and `0x030731FB` directly calls **`0x0307E1A0`**, the native 0.01f comparison consumer of `member+0x23C`. This confirms a **conditional same-member handler→gate order**, not that both always run or that an actual queued Shift MOVE takes the path.

Original code has a separate, second direct E8 caller of the gate at `0x03072E74` in PE function `0x03072DFC..0x03072E7F`. Its prior call to `0x0307E7AC` is followed by *no new RCX load*, so the exact RCX alias requires an additional callee-preservation proof. A bounded full `.udata` E8 candidate scan returned exactly the two gate sites; both were independently checked as actual objdump instruction starts.

## Crucial rejection of the simplistic R68/R69 hypothesis

The local **mode setter** `0x0307D9C0` (via member VTable `+0xE0`) conditionally clears `member+0x23C/+0x1C8` when mode 1/2 becomes mode 0, and calls `0x0307DB60` at `0x0307D9F8`. But the new parent function calls **`0x0307DB60` directly**, *not* `0x0307D9C0`, and uses **different call flags**:

| Native caller | R9B | Stack fifth argument | EDX |
|---|---:|---:|---|
| mode setter `0x0307D9F8` | 0 | 1 | 0 |
| `0x03072F00` | 1 | 0 | prior virtual method return EAX |

Shared callee identity cannot establish the setter's clearing side effect. This is a concrete provenance and argument mismatch, not proof such a mode reset never happens through other paths. **`SHIFT_CAUSAL_LINK_BLOCKED`** for the proposed mode-reset→0.01f gate→crowding explanation. Do not NOP the reset, modify 0.01f, forcibly synchronize member modes, write member coordinates or introduce a Lua scheduler.

## Verification and provenance

Original EXE: **72/72** instruction bytes and decoded GNU objdump starts; **14/14** pinned E8 target relationships; **6/6** PE UNWIND ownership intervals. Local **22/22 unittest PASS**, including original EXE. The larger R70 ZIP delivered separately includes all 72 pin records, full original-code assembly excerpts, complete verifier and tests, execution evidence and R69 archive. **This GitHub change includes a smaller independently runnable 32-pin subset, not the whole ZIP or commercial executable.** Public Actions CI omits the EXE and must skip the private exact-EXE case.

## Stop rule / next research boundary

Stop unrestricted recursive xrefs of `member+0x23C/+0x1C8`. R71 can examine the already typed member Tick `0x03086F04` only to establish *whether* a bounded same-thread read-only observation can be made safely (ABI, lifetime, thread identity, nonblocking bounded publication, failure cleanup). No live Hook before safety proof, no new user game test, no gameplay patch, no change to `main`.

`root_cause_proven=false`, `mode_reset_to_gate_proven=false`, `same_shift_instance_proven=false`, `gameplay_patch_authorized=false`.
