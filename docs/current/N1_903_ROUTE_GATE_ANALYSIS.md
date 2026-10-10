# N1 — WH3 9.0.3 native route-processing gate and state+0x24 eligibility

**2026-10-10; exact-binary STATIC/OFFLINE only. No Hook or playable patch.** User-provided EXE SHA256: `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, PE image base `0x140000000`. Version label 9.0.3 comes from user, not independently verified VERSIONINFO.

## Found: 0x0310F560 is a stateful route processor, not a pure boolean

Callback `0x0311E80C` calls it at `0x0311EAC7`, then uses its AL result. This is NOT a safe detour candidate for "always return true": real instructions update route-working memory and invoke multiple geometry/planning helpers.

| Exact 9.0.3 RVA | Code-level observation |
|---|---|
| `0x0310F58C`, `0x0310F596` | zero working fields `+0x170/+0x184` |
| `0x0310F5B6`, `0x0310F5C0` | early check; a guarded branch returns AL=0 |
| `0x0310F6DB` | SIMD store of derived coordinates to `+0x1B4` |
| `0x0310F728`, `0x0310F880`, `0x0310F8DC` | call route clone/update helper `0x030EA7D0` |
| `0x0310F7CF` | calls alternative route helper `0x030EA6F4` |
| `0x0310FB02`, `0x0310FB09` | clear working pointer fields `+0x198/+0x1A0` |
| `0x0310FB48` | return selected processing result in AL |
| `0x030EA919` | route helper `0x030EA7D0` calls further native route processor `0x030E88C8` |

`0x030E88C8` contains a proven XY-distance calculation (`subss`/`mulss`/`addss`/`sqrtss` at `0x030E8A31–0x030E8A47`) and compares/stores derived route values at `0x030E8A67–0x030E8A80`. Physical significance of the other scalars is **unknown**: this is NOT a proven unit-speed, arrival radius or terminal-braking calculation.

## Narrowed: state+0x24 flag truth table for this callback path

Earlier findings identified writer `0x0311EB10` but left the exact condition open. The immediately preceding original opcodes now show:

- `0x0311E891`: DIL=0 on the identified callback path; x64 callees preserve RDI.
- `0x0311EAC7`: call `0x0310F560`; `0x0311EACC` saves AL; `0x0311EAD4` tests AL.
- `0x0311EAD8`: compare controller field `[rbx+0x4E4]` with constant **2**; the branch for AL!=0 and field<2 sets DL=1.
- `0x0311EB04–0x0311EB0D`: set DIL=1 only if saved AL!=0 and DL==0.
- `0x0311EB10`: `mov byte ptr [rsi+0x24],dil`.

Conditional on reaching this block with DIL=0, the written flag is exactly:

| Route-processing AL | controller `+0x4E4` | state `+0x24` |
|---|---|---|
| 0 | any | 0 |
| nonzero | 0 or 1 | 0 |
| nonzero | >=2 | **1** |

This is **not** a global predicate for all native state writers. It does NOT prove what the mode field or AL means in gameplay (route acceptance is a plausible label, not validated). The successful branch writes linked object/coordinate data (`0x0311EB1D–0x0311EB38`), may enter state 2 (`0x0311EBC2`), and calls `0x03105B4C`. Other paths set state 4 (`0x0311EC0E`), so reachability of **state=4 AND flag=1** for ordinary Shift MOVE remains open.

## Consequences and next N1 proof

1. Forcing `0x0310F560` to return 1 would skip native route setup and teardown. **Rejected.**
2. Forcing `state+0x24=1`, `state=4`, task count=0 or raw OrderHead bypasses original ownership/eligibility logic. **Rejected.**
3. Follow `0x030E88C8` outputs into original path/motor consumer, distinguishing *spatial route checks* from *desired speed / terminal braking*. Then trace state2→state4 and flag retention with native object lifetime.
4. Compare original queued intermediate MOVE vs terminal MOVE and normal RMB; ATTACK remains separate via ordinary activation.
5. **Still unknown:** the instruction causing visible stop-and-go, native locomotion reset, patch-safe ABI/threading, WH3 runtime behavior. No Native patch authorized.

## Reproducibility

Read-only local `verify_903_route_gate.py` checked **46/46 exact executable instruction guards** and **6/6 E8 direct-call edges**, no address promotion. **8/8 unit tests PASS**, including 7 synthetic/metadata cases and one optional exact-EXE read-only check (skipped if no EXE). The accompanying downloadable research bundle includes source, tests, bounded LLVM disassembly, JSON evidence and SHA256 manifest; **does not redistribute EXE**. No Ghidra, Windows hook or WH3 behavior test has been performed this iteration.
