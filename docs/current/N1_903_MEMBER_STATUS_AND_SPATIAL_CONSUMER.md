# N1 — 9.0.3 verified native unit-route member flags and spatial member comparison

**Exact build static RE:** user-provided AMD64 WH3 binary, SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` (image base `0x140000000`). Game 9.0.3 label user-supplied. **No working BSC Native patch**.

## Positive original native call chain: common route + bulk member status

Original native task callback **RVA 0x0301C0B0** reads the root's **shared route `root+0x270`** at `0x0301C0CE`, then calls **`0x0302BC30`** at exact E8 site `0x0301C0EE`. The callee obtains the same root, the A-member count `root+0x184`, native route `root+0x270`, and optionally calls original route configuration **`0x0301287C`** at `0x0302BD41` after checking a native helper at `0x0302BD09`. Finally it iterates **all** A member pointers at `root+0x188` and clears **bit 0** in **each** member's `+0x6C` and `+0x70` at `0x0302BDF1/0x0302BDF5`.

Separate engine functions **`0x03033A54`** and **`0x03033BEC`** also walk the same root A-member count/array and broadcast `OR 1` and `OR 3`, respectively, into `member+0x6C` (`0x03033A83`, `0x03033C0A`). This is proof of *unit-wide batch status changes*, not proof that bit0 is Shift waypoint arrival. Context-specific `0x03018F7C` also loops a **different** vector at context+0x24/+0x28; do not assume alias. Elsewhere `0x03023060` uses AND `0xFFFFFFFC`, clearing **both** bits 0 and 1, not only bit1.

**Do not infer separate soldier-level Shift command queues.** Shared native route context and bulk member state changes coexist with individual model movement.

## Spatial member subsystem: exact machine evidence, but no proven Shift relation

Member-like object function **`0x03057B68`** calls vfunc `+0x58`, gets child group **count `+0xB64`/array `+0xB68`**, filters each member's status **bit1 (`0x2`) of `+0x6C`** at `0x03057BA3`, computes 2D Euclidean distance using `+0x88/+0x90` at `0x03057BD5`, adds a size-like `+0xA0` float at `0x03057BD9`, and selects the maximum at `0x03057BE1`.

Original two-member comparison **`0x03058E0C`** calls that envelope function four times at `0x03058F40/78/92/A6`, reads relative positions and virtual +0xC8 heading-like values, and compares spatial bounds to return a Boolean. Original higher functions `0x03086910` and `0x030880E4` reach this logic through verified E8 edges: `0x03086AD5`, `0x03086B7E` -> `0x03058E0C`; `0x030885BF` -> `0x030865B8` and `0x030885CD` -> `0x03086910`. This is native **member spatial/overlap/relative-position processing**, not yet a proven soldier waypoint turn predicate. It may be a separate collision/encounter/targeting system.

**Original code does NOT establish a causal edge from normal Shift MOVE work `0x03025D70` to this spatial subsystem.** The flags `+0x6C` bit0/bit1 are also not confirmed to mean arrival/next-leg. Changing them or any geometry threshold now would be speculative and unsafe.

## Proof and next causal blocker

Local SHA-pinned read-only evidence (`BSC_N1_903_member_status_and_spacing_20261010.zip`) checks **38 original x64 instruction guards + 13 original E8 direct calls** and passes **9/9 synthetic/negative tool tests**. Package includes full decoded disassembly, JSON guard ledger, reproducer, JSON result and SHA256 manifest, excluding game EXE.

The actual issue is the user's reported **different arrival/turn behavior among soldier models sharing one unit-card Shift order**, causing crowding. To patch WH3 directly, we still must connect the native shared route to an actual *per-model next-destination/facing writer or arrival/leg promotion condition*, and prove whether phase differs by model versus shared target with differential steering. **No Hook/DLL/PACK, no Windows or WH3 proof; N1 causal blocker remains open.**
