# N1 — Mode-selected group layout versus cross-motion handling (9.0.3)

**2026-10-10; exact user EXE static audit; no playable native repair.** SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, image base `0x140000000`. WH3 9.0.3 is the user-supplied version label.

## The user's removal-vs-death correction

`0x030DD3F4` mode-dependent swap-last (`0x030DD469`) is **old-group member removal/container maintenance**, not proof that original Shift turning remaps actor-to-target slots. It can be used for death/leave, but is **not death-only**: original native MOVE group rebuilding `0x0302DB44→0x0301B8E4→0x030E0460` transfers a member out of its former group, invoking old-group virtual +0x08 (`0x030E04A6`) if the former group exists. The NEW group is rebuilt in `UnitRoot+0x188` enumeration order, so old-group swap-last does not automatically provide corner-turn identity rematching when the source order remains stable.

## Does normal Shift always select the mode3 grid strategy?

**No such statement is established.** `0x0302DB81` loads `[UnitRoot+0x3D48]`, `0x0302DB88` reads that object's `+0x248` integer and passes it to group constructor. There is also a native formation/configuration update path `0x030C666D→0x030DDE78` with multiple writes to the recipient object's `+0x248`: 2/10/11/12 and a general computed value. The caller's concrete pointer identity with `[UnitRoot+0x3D48]` is **not completely proven**. A normal battle's actual mode requires game-state evidence; a static EXE does not reveal the unit's current field contents. The mode3 3×3/180° geometric crossing counterexample is **conditional**, not a proven default.

## Which strategies did CA actually implement?

1. **Mode3** `+0x48→0x030CA218` generates indexed grid targets, appends 48-byte records, and maps grid neighborhood indices; the original `0x030D5490` fanout pairs `group_member[i]` to `record[i]`. No globally optimized prior-member-position/nearest-target assignment has been identified within those audited boundaries. This is a *local negative finding*, not a claim about every engine path.
2. **Mode5** `+0x48→0x030CAD9C` calls `0x030E04F4` at `0x030CAE7D`; this reads 24-byte-stride template records, performs geometric rotation/translation and writes transformed position/facing outputs (`0x030E05F6`, `0x030E0601`). `0x030CAED9` then appends records in order. No member-to-nearest-new-slot solver appears in this examined template-transform/append path either.
3. **Mode0** `+0x48→0x030C9A64` delegates to `0x030DBFD4` (`0x030C9B18`). That function traverses strategy child objects and calls per-item virtual +0x30/+0x38; their complete implementations have not been resolved. Thus one cannot assert *all* CA formation strategies are naive fixed-slot loops.
4. **Post-fanout original group processing** `0x030D5522→0x030E0AA8` can call `0x030E07C0`, which uses record geometry and can set record+0x2C=1 at `0x030E08EB`. This happens after member tasks are dispatched; no proven immediate old-target-to-new-target remapping, though later task effects are unverified.

## Strong counterevidence to “CA never considers movement direction”

An *independent* original actor-interaction subgraph **does** consider spatial position together with a member's displacement rate: `0x03086910` computes flat difference in member+0x88/+0x90 (`0x03086A50..0x03086A68`), multiplies by member+0xE0/+0xE8 motion-rate components (`0x03086A70/78`), sums a **dot product** (`0x03086A80`), and branches on its sign (`0x03086A84/88`). Another guarded branch calls member pair geometry `0x03058E0C` at `0x03086AD5`. Verified upward E8 edges `0x030827E0→0x030880E4` and `0x030885CD→0x03086910`; some upstream objects access `UnitRoot+0x3D48`, but there is **no proven direct native Shift MOVE→this-check call chain**. It may be actor interaction, combat or target screening rather than actual locomotion avoidance.

**Correct result:** WH3's native code contains direction-sensitive member geometry and extra formation strategies. We have *not* identified a guaranteed collision-free reallocation in the tested mode3/mode5 member-target issuance path. Therefore both blanket claims (“CA never considered directional collision” and “CA already prevents Shift corner crowding”) are unsupported.

## Verification and next decision boundary

Pinned original EXE check: **45 exact instruction byte guards; 9 original E8 direct-call targets; 3 strategy VTable +0x48 targets; 12/12 offline tests** (includes SHA match and wrong-binary rejection). Complete independently runnable Chinese forensic bundle: `BSC_N1_903_MODE_AVOIDANCE_AUDIT_20261010.zip`, available as conversation download; contains `verify.py`, `test_verify.py`, original bounded disassembly, `evidence.json`, report and SHA manifest. Game EXE not redistributed.

To decide a BSC Native change rather than make another conjecture: establish actual queued-Shift mode for the target unit, identify/contrast slot mapping across two consecutive native MOVE legs with stable model identity, and determine whether the original per-model locomotion/collision consumer corrects crossing trajectories. No version-guarded ABI, safe patch delta or WH3 physical acceptance yet, so **NO HOOK / NO DLL / NO CLAIMED FIX**.
