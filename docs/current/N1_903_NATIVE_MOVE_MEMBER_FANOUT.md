# N1 9.0.3 — Original MOVE actually fans out native commands to each group member

**2026-10-10 — exact-binary STATIC result. NOT a working BSC patch.**

Target user-supplied WH3 EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, PE64 image base `0x140000000`. Version 9.0.3 remains user label rather than an independently validated VERSIONINFO.

## Direct closed chain (machine-call destinations verified)

```
native MOVE issuer 0x030323C8
  0x03032965 E8 -> 0x0302DB44 unit route update
     0x0302DB8E E8 -> 0x0301B8E4 build group from UnitRoot members
       root+0x184 count / +0x188 pointer array
       0x0301B946 E8 -> 0x030E0460 append member into group
       root+0x32F8 <- native group
     0x0302DBC4 E8 -> 0x0301287C native unit route descriptor config (+0x270)
     0x0302DBDB E8 -> 0x030D5490 native member fan-out
       group VTable+0x48 generates member-indexed records
       group+0x24 count / group+0x28 element pointer array
       loop uses output[i*0x30], calls 0x02F5F868 at 0x030D54FC
       calls each element's VTable+0x368 at 0x030D550F
       group VTable+0x20 invoked after loop
```

**Important discovery:** the original game is capable of **one unit MOVE giving rise to separately prepared native member-level task payloads**. These are **not shown to be different high-level Shift orders**. The individual members' virtual dispatch may allow later divergence, but this does NOT prove that per-model waypoint arrival is independent.

### Object provenance and semantics

The original `0x0301B8E4` enumerates A members from one UnitRoot, invokes `0x030E0460` for each, and stores resulting group at `root+0x32F8`. The insertion routine invokes member VTable+0x3F8 and finally calls a group insertion routine `0x030C7420`; filtering/dedup/lifetime effects of virtual implementation are unverified. The unit-route updater `0x0302DB44` uses this native group and updates the original route `root+0x270`, then calls `0x030D5490` with a route-associated input.

The group function `0x030D5490` calls VTable+0x48 ONCE with group count, producing a per-member `0x30`-stride output array. Each iteration loads a group member pointer and its generated output record, creates a native payload via `0x02F5F868` (which sets native code byte `0x26` at payload+0x50), and calls that member's virtual `+0x368`. The *actual concrete method implementation*, type of member and meaning of native code `0x26` must still be resolved.

### Negative evidence correcting a tempting false arrival gate

Function `0x03022A4C` contains a read of native queue count `root+0x2F88`, **but this read is inside the DL=0 branch**. Its sole direct-E8 caller currently located, `0x03043289`, sets DL=1 at `0x03043284`. Thus the visible queued-count check is **bypassed on that observed call path** and must not be treated as a proven group-arrival condition.

## 2026-10-10 successor finding: actual virtual receiver functions identified

[N1_903_MEMBER_VIRTUAL_RECEIVER_RESOLVED.md](N1_903_MEMBER_VIRTUAL_RECEIVER_RESOLVED.md) resolves the formerly unknown member VTable `+0x368`: 38 original constructor-backed native vtables share group getter `+0x3F8 -> 0x008F37B0` (`member+0x300`). Of them 36 dispatch `+0x368` to common `0x0306B9F0`, one to forwarding wrapper `0x0306B9CC` and one to specialized `0x03117CE0`. The common handler chooses member action `+0x100` or `+0xE8`; the former reaches `0x0315F4E0`, an instruction-verified member coordinate/angle writer (`+0x88/+0x90/+0xB0`), while another downstream method updates member-local route cache (`+0x910/+0x930`). Still no proven independent per-model waypoint-arrival decision or patch safety.

## What is still open / exact next proof

1. Identify concrete implementations and original completion logic behind member VTable `+0x368`; establish whether this submits an independent motor task, an individual route phase or another animation/action.
2. Prove that group member elements correspond to actual model steering agents, including their destination/facing writer and lifetimes.
3. Compare TWO members receiving payloads from the SAME native queued MOVE: does each independently advance to leg k+1, or do they share a group leg with different steering and collision?
4. Only then consider adjusting WH3's **original** coordination/promotion rule; no Lua reissue, second queue, forcing all soldiers to arrive exactly, or speculative bit/threshold mutations.

## Offline proof

Local downloadable `BSC_N1_903_NATIVE_MEMBER_FANOUT_20261010.zip` includes the SHA-pinned read-only `verify_fanout.py`, **38/38 original instruction byte guards, 9/9 decoded original E8 call edges**, 10/10 synthetic/offline tests, bounded LLVM disassembly and SHA256 manifest. These checks demonstrate code structure only, **not** smooth in-game formations or a safe Hook. No EXE redistributed, DLL, PACK, Windows or WH3 test.
