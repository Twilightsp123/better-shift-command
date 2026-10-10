# N1 9.0.3 — CLOSED negative finding: formation layout count is not waypoint arrival

**2026-10-10 | Original executable SHA256:** `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` (image base `0x140000000`). User labels it 9.0.3; VERSIONINFO remains unauthenticated. **STATIC/OFFLINE only. Gameplay patch NOT implemented.**

## Decisive distinction: two DIFFERENT virtual +0x20 methods

The original native fanout function `0x030D5490` first obtains **group+0xB30**, a formation-strategy object. `0x030D54CA` invokes that object's **virtual +0x48 ONCE** outside the per-member loop, producing 0x30-byte indexed output records. `0x030D54D0..0x030D551A` then iterates group members and calls their **virtual +0x368**, each receiving a separately constructed payload. After the loop, `0x030D5522` invokes virtual **+0x20 on the group object**, a *different type*, not the strategy.

For the original constructor-backed group object VTable `0x0390F5F0`, that group +0x20 is **`0x030E0AA8`**. Do not conflate it with one of the eight strategy +0x20 methods.

## Original task +0xB8 is a cached layout-number, NOT a proven arrival phase

Native callback `0x0302BC30` reads **the strategy object +0x20** from `group+0xB30`, passes the unit member count `root+0x184` and scalar `[root+0x270]+0x40`, then compares the returned **integer** against `task+0xB8` (`0x0302BCA2`), later updating the cache (`0x0302BDC4`).

The precise code of eight genuine constructor-referenced strategies strongly identifies layout cardinality/size calculations, NOT the number of models that have reached a Shift waypoint:

| Strategy method at +0x20 | Observed computation |
|---|---|
| `0x008F7750` | truncate(sqrt(member_count)) |
| `0x030D1A08` | min(13, member_count) |
| `0x008F7770` | member_count-indexed table lookup +1 |
| `0x030D19A4` | bounded integer from member count, route scalar and strategy floats |
| `0x008F7700` | sqrt(member_count) with alternate integer rounding |
| `0x0305FFDC`, `0x008F7780`, `0x030D1A18` | other mode/size-dependent integer mappings |

The exact game term (ranks, columns, or another formation cardinality) remains unknown. **The proposed N1 “group strategy +0x20 / task+0xB8 is the unified soldier-arrival/waypoint-phase predicate” must be rejected.** Treat these as formation-layout caching, not an approved patch site. The original refresh path subsequently bulk-clears member bit0 but that bit is also **not** proven waypoint arrival.

## Next-level native member action divergence exists; its meaning remains open

The already verified shared member receiver `0x0306B9F0` reads **member+0x104** at `0x0306BAD7`. It branches on `value-1 <= 1`:

- member **virtual +0x100** at `0x0306BB0E`, whose original implementation can enter `0x0315F4E0`, directly writing member position-like `+0x88/+0x90` and orientation-like `+0xB0`, clearing/resetting local state;
- otherwise member **virtual +0xE8** at `0x0306BB44`, whose original implementation can enter deeper native move/action logic `0x0315EC98`;
- both branches can finish with a local route/cache refresh through `0x03056ED4`, reading/writing `member+0x930`.

This proves that **the original common unit MOVE can fan out to members which may take different internal action paths**, without different HIGH-LEVEL Shift commands. The meaning and producers of `member+0x104`, the actual model arrival/phase transition, and whether action differences cause reported jostling are **NOT** proven. The `+0x100` routine directly writes current pose-like fields, so don't mistake those writes for each soldier's next destination.

## Exact next causal fork (no unlimited speculative Hook search)

**If** there is a model-local next-leg completion event downstream of virtual +0xE8 or the path cache, locate its real write/read path, then evaluate reuse of an original group phase rule. **If not**, identify the physical steering/formation-slot target discontinuity between common group output and individual agent response. Explicitly distinguish these using decoded native dataflow. No forced group snap, first model triggers all, wait-for-everyone deadlock, Lua issuing, raw OrderHead/cached-size edits, or blanket vtable patch.

## Verification and GO/NO-GO

Against the pinned original user EXE: **26 exact instruction byte guards PASS**, **8 strategy VTables including their 16 method pointers PASS**, original distinct group-object +0x20 pointer PASS; **8 local synthetic tests PASS**. The complete reproducible package additionally includes bounded LLVM disassembly, generated JSON and a SHA manifest; **no game EXE distributed**.

**Status:** STATIC mechanism PASS, OFFLINE tooling PASS, WINDOWS not run, WH3 not run, **working Native patch NOT created**. This round *falsifies the prior proposed shortcut*; it does not establish gameplay fix or ABI safety.
