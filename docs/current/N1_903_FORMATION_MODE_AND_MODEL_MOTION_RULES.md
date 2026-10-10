# N1 9.0.3 — Find the rules governing each model's motion

**2026-10-10 | exact EXE static machine-code result.** Target SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`; image base `0x140000000`. User labels game as 9.0.3. **No physical velocity, per-model player-Shift waypoint advance, or safe Hook is proved.**

## New direct provenance: the original MOVE selects formation strategy by native mode

At original MOVE route helper **`0x0302DB44`**:

```asm
0x0302DB81 mov rax,[rcx+0x3D48]  ; rcx is UnitRoot
0x0302DB88 mov edx,[rax+0x248]   ; native strategy mode integer
0x0302DB8E call 0x0301B8E4      ; group construction, receives that mode
```

Original `0x0301B8E4` passes that EDX into `0x0301B834` via R9, which stores it at ctor-input `+0x10`. Group constructor `0x030C2C3C` reads input `+0x10` at `0x030C2D1A` and invokes strategy wrapper `0x030C7CD4`; it reaches **`0x030C7D18`**, a switch across modes **0..12**. The original group then calls chosen strategy VTable `+0x48` ONCE per fanout to produce `0x30`-stride member-specific position/facing records, distributing through native member VTable `+0x368`. **It is not 13 different player Shift queues.**

### Confirmed direct strategy modes (other modes use wrappers and need separate checking)

| Input mode | VTable RVA | Group target generator (+0x48) |
|---|---|---|
| 0 | `0x0390F558` | `0x030C9A64` |
| 2 | `0x0390F388` | `0x030C9C44` |
| **3** | **`0x0390F180`** | **`0x030CA218`** |
| 5 | `0x0390F0C8` | `0x030CAD9C` |
| 10 | `0x0390EF98` | `0x030CAF04` |
| 11 | `0x0390F218` | `0x030CA140` |
| 12 | `0x0390F030` | `0x030CAFCC` |

**Important new discriminator:** previously shown mode-3 3×3 differing member facing codes apply to **mode 3**, and are **not evidence that a specific ordinary queued Shift unit currently uses mode 3**. Establish actual mode selection before trying to fix its generation.

## What must be investigated together to explain actual soldier movement

1. **Formation mode / slot target:** `[[UnitRoot+0x3D48]+0x248]`; group strategy `+0x48`; original per-member `record[i]` positions `+0/+4/+8`, heading code `+0x22`. Determine if targets swap or cross after a group turn.
2. **Per-member pose vs *actual velocity*:** original member fields `+0x88/+0x90` contribute to group position aggregates and are written through native pose-like setters; `+0xB0` receives facing-like codes. A different facing code is **not** an actual movement vector. Find per-tick final position writer and `Δpos/Δt` (or native desired-velocity writer).
3. **Member action mode:** `member+0x104` is written by `0x0307897C` and selects original virtual `+0x100` versus `+0xE8` in `0x0306B9F0`. Its changing value is **not proved** to be a high-level route-leg index or arrival Boolean.
4. **Member-local trajectory:** `member+0x930` path cache and a separate `member+0x2E0` controller; `0x0315BF14` advances controller `+0x18` local spline segment, `+0x1C` interpolation fraction. Those are not automatically player Shift waypoints. Trace their output to the actual per-tick position/velocity writer.
5. **Common route-phase transition:** prove when original `root+0x270` route/order advances and whether all model targets change at once. Separate asynchronous high-level phase changes from one common group phase with divergent slot/steering.
6. **Collision/avoidance:** candidate member spacing `0x03057B68`/`0x03058E0C` must first be shown reachable from ordinary MOVE. Compare target velocity and actual motion to distinguish avoidance from a target assignment failure.

## Deterministic causal interpretations

| Same MOVE, two models A/B | What it would support |
|---|---|
| Different **high-level** route leg/target refresh times under one group | Soldier-local leg promotion; evaluate original group phase coordination |
| Same group refresh time, new slots/heading assignments conflict/cross | Original formation slot/turn geometry |
| Same phase and coherent target slots, different approaching velocity vectors/collision | Local path/steering/avoidance; don't change original Shift queue |
| Stop before native ATTACK only when old Lua Controller is present | Legacy BSC reissue/rollback regression; separate issue |

## Exact-file reproducibility

The read-only local program `audit_formation_mode_path.py` in downloadable package `BSC_903_MOTION_RULES_TRACE_20261010.zip` validates **22 exact opcode guards, 5 original E8 call targets, mode-3 strategy constructor LEA and two genuine VTable pointers** against this pinned EXE; **8/8 local tests PASS**, plus JSON evidence, complete Chinese report, SHA manifest. The EXE is not redistributed. **STATIC/OFFLINE only; no DLL/PACK or gameplay acceptance.**

**Next executable investigation must resolve the actual *per-frame model velocity/target* and normal queued Shift strategy selection, not more OrderHead speculation or guessed arrival thresholds.**