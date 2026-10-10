# N1 9.0.3 — One-pass group phase / per-model arrival causal audit

**2026-10-10. Current status: STATIC VERIFIED SUBGRAPH; MOVEMENT ROOT CAUSE UNKNOWN; NATIVE PATCH NO-GO.**

Primary user-observed problem: the original queued unit Shift MOVE can yield inconsistent turns/crowding among constituent soldier models. This does **not** require each soldier to receive a distinct Shift command. Legacy Lua MOVE→ATTACK stop/rollback is a separate BSC regression. The goal is original-engine behavior correction, not a new Lua/Native scheduler.

**Research build (exact file):** user EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, image base `0x140000000`, WH3 9.0.3 user-supplied label.

## This round: complete inbound native member fanout plus repeat-task routes

Verified original unit MOVE issuer `0x030323C8` → `0x0302DB44` → build group `0x0301B8E4` from `root+0x184/+0x188`, configure common route `0x0301287C` (`root+0x270`), then native group dispatch `0x030D5490`.

At `0x030D54CA` original group VTable+0x48 is invoked **once before the per-member loop**, producing group-indexed 0x30-byte payload records. Inside that loop, `0x030D54FC` constructs a native payload and `0x030D550F` invokes each recipient's virtual+0x368; only after the loop is the group's virtual+0x20 invoked. The concrete member receiver family was previously resolved to `0x0306B9F0` (36/38 constructor-referenced VTables), then vfunc+0xE8/+0x100 leading to member coordinate/angle writers and cache updates. This is **one native group target generator producing multiple member payloads**, not evidence of multiple high-level Shift orders or independent member *arrival*.

**New complete static crossreference sweep** of both executable PE sections found the group dispatch also directly reached from original task callback sites `0x0301C05F`, `0x0301C0DD` and `0x0301C185`, in addition to initial MOVE `0x0302DBDB`. Specifically task callback `0x0301C0B0` re-invokes group fanout then calls `0x0302BC30` at `0x0301C0EE`. The latter compares a group virtual+0x20 result to cached task+0xB8 under native conditions, can refresh the original route, and **bulk-clears bit0** in each root-A member's+0x6C/+0x70. The group virtual result and bits **cannot be labeled waypoint arrival or next-leg index** without their writers/consumers. The vtable task callback's identity as normal Shift progression is also unproven.

**New concrete strategy resolution:** original group constructor `0x030C2C3C` calls strategy selector `0x030C7D18`, which constructs `group+0xB30` strategy objects. Eight distinct constructor-anchored virtual tables are confirmed on the pinned EXE. For each original table, the `+0x20` group-state method and **`+0x48` member-target generator** are decoded and reside in executable sections:

| Strategy VTable | Original vfunc +0x20 | Original vfunc +0x48 |
|---|---|---|
| `0x0390F4B8` | `0x030D19A4` | **`0x030C9B3C`** |
| `0x0390F0C8` | `0x030D1A18` | **`0x030CAD9C`** |
| `0x0390F180` | `0x008F7750` | **`0x030CA218`** |
| `0x0390F388` | `0x008F7700` | **`0x030C9C44`** |
| `0x0390F558` | `0x0305FFDC` | **`0x030C9A64`** |
| `0x0390F030` | `0x008F7780` | **`0x030CAFCC`** |
| `0x0390F218` | `0x030D1A08` | **`0x030CA140`** |
| `0x0390EF98` | `0x008F7770` | **`0x030CAF04`** |

At least some actual `+0x48` implementations process original coordinate/heading/group-mode inputs and invoke route/target-generation helpers (e.g. `0x030DBFD4`), **not one universal per-soldier arrival function**. Mode-specific selection means patching only a convenient virtual receiver could silently miss other unit types. Exact link from individual model's later arrival to a next waypoint phase still unproven.

Read-only local one-pass audit checked **14/14 direct E8 targets**, **18/18 opcode guards**, **8/8 constructor-referenced group-strategy VTables** with **16 verified method pointers**, and assembled raw-E8 crossreference candidates of 11 functions plus **nine** bounded native disassembly excerpts. Tool tests **6/6 PASS**. Full pipeline and JSON evidence delivered as `BSC_903_ONE_PASS_CAUSAL_AUDIT_20261010.zip` in the conversation. The full tool, generated JSON, bounded disassembly, detailed Chinese report and SHA manifest were supplied as conversation archive **BSC_903_ONE_PASS_CAUSAL_AUDIT_20261010.zip** (not the game executable). This is STATIC/OFFLINE integrity, not a WH3 motion test.

## Single closed causal decision, not endless small reports

A. Resolve the concrete `group+B30` object VTable+0x48 (member-specific target generation) **and** VTable+0x20 (group status), and the original task callbacks' vtable/constructor/queued-context. Determine exactly who generates/advances a route leg.

B. Trace an actual model/slot target writer and **reader**; prove or reject a per-model native `leg=k→k+1` transition. If two models share a group leg but still have different headings, the cause is formation-slot target geometry/steering rather than different completion phases.

C. Compare **normal RMB, queued intermediate MOVE, final MOVE and legacy Lua-off native ATTACK** in the *same* original native dataflow. Do not promote guessy offsets or route geometry thresholds as a workaround.

D. Only if one narrowly defined original-engine condition is proven causal and safe to change: create a group-scoped route-phase/target-sync delta, never hard wait for every model, never early transition from one outlier, never reissue MOVE/ATTACK or mutate OrderHead. Complete evidence-derived 90/135/180-degree, short zigzag, blocked/casualty, cancellation and attack negative cases, then guarded Win64 ABI/install/disable tests, then **one consolidated WH3 acceptance** focused on within-card crowding and relative headings.

**No-go verdict now:** Neither independent per-soldier waypoint arrival nor globally shared leg with asymmetric steering has yet been proven. No safe native predicate/ABI is established. Do NOT install a speculative DLL or claim BSC gameplay repaired. The next actionable task is the concrete group VTable+0x48/+0x20 and task callback-vtable producer/consumer analysis, *as one finite investigation batch*.
