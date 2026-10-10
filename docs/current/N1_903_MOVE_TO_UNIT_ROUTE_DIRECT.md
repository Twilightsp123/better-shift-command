# N1 — Original WH3 MOVE worker directly configures the unit's native route descriptor (9.0.3)

**2026-10-10 | Exact-file machine-code dataflow. Not yet a fixed mod.**
Target is the user-provided 9.0.3-labelled `Warhammer3.exe`, SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` (image base `0x140000000`). Game VERSIONINFO label not independently verified; this EXE hash defines the research build.

## A positive, directly connected native MOVE path

Unlike earlier unlinked nearest-member distance searches, both branches of native MOVE work **RVA 0x03025D70** call original unit route configurator **RVA 0x0301287C**, at **0x03025E91** and **0x03026022**. These E8 destinations have been verified from the target EXE bytes, not guessed from proximity.

The configurator reads a root-associated group at `+0x32F8`, group subobject `+0xB30`, count `root+0x184`, and a scalar from `root+0x1D0`. Under the native branch conditions it invokes native descriptor constructor `0x030ECAB0` (callsite `0x03012945`), then route allocation helper `0x03008894` (callsite `0x03012982`) and writes the returned pointer into **`root+0x270`** at `0x03012987`.

An alternative branch writes destination XYZ into an inline root subobject `root+0x1E8` at `+0x20/+0x24/+0x28`, a scalar at `+0x40`, and sets **the same root `+0x270` field** to the inline object pointer (`0x030129E5`). These are two different original paths for establishing an associated unit route descriptor, NOT two BSC-issued commands or two separate soldier Shift queues.

```text
original MOVE work 0x03025D70
  ├── direct call 0x03025E91 ──┐
  └── direct call 0x03026022 ──┤
                                v
                     original 0x0301287C
                     group+0xB30 and member count
                        ├── descriptor 0x030ECAB0
                        │     └── native allocation 0x03008894
                        │            └── root+0x270 = route pointer
                        └── inline destination XYZ/scalar
                               └── root+0x270 = inline route
```

**Important:** `root+0x270` is at the *unit/root level*. There is still **no proof** that this function directly gives divergent high-level orders to each soldier model, or that soldier crowding is caused by this assignment.

## An adjacent original model/member dispatch candidate: not yet causally connected

Separately, native **0x03012A6C** accesses the same root route pointer at **0x03012BED** and, in a guarded branch, obtains a pointer from `root+0x188`, reads its position-like float fields `+0x88/+0x90`, and calls that object's virtual **`+0xC8`** at **0x03012C1E**. It then calls `0x0301287C` at **0x03012C42**. This suggests an original member-associated update may occur near unit route configuration; **the concrete object's class and virtual method meaning are not proven, nor is a caller edge from MOVE worker to 0x03012A6C**.

Another original routine **0x0304725C** reads `root+0x270` and loops through the `root+0x188` member list; for each selected element it constructs coordinates involving a pseudo-random scalar and calls **0x0307AA30** at **0x03047473**, which invokes multiple *member* virtual methods, including `+0xE8` and `+0x608`. But no direct E8 caller into **0x0304725C** was found and its dynamic task type/Shift relation remains unknown. **It may be a separate scattering/AI task, NOT normal queued Shift model target assignment.** Do not infer soldier-specific queued commands from it or patch the randomization.

## What has been verified offline, and what has not

- `audit_move_group_route.py`: **23/23 exact original opcode guards and 7/7 E8 call targets** on SHA-pinned user EXE.
- `audit_nearest_member.py`: **19/19 opcode guards and 5/5 E8 call targets**; zero raw direct E8 callers to unrelated selection function 0x031E11AC (virtual callers not ruled out).
- `test_audit.py` and `test_move_route.py`: **16/16 synthetic test cases PASS** for byte parser, target matching and safe failing.
- Runtime: **NO DLL, PACK, Win64 Hook or WH3 test**. Formation-slot target mapping and model per-turn synchronization are still not found, so patch authorization remains FALSE.
- Full source/test/JSON/LLVM instruction excerpts/SHA manifest: `BSC_903_MOVE_TO_UNIT_ROUTE_RE_COMPLETE.zip` (provided separately, game EXE excluded).

## Exact next causal boundary

Follow the verified *unit-route pointer* `root+0x270` through its original consumers with object identity proof; map the true **formation-slot / soldier-target writer** and which members receive different effective targets or change heading at different times. Compare normal RMB route against queued Shift using original call conditions. The first differing model-level decision, not an assumed unit-wide stop, is the only legitimate narrow Native Patch target.

**Do not** force writes to root+0x270, individual member fields, queue head or native task state. No second Lua/native scheduler. The conspicuous MOVE→ATTACK pause remains a legacy BSC Lua Controller regression and is separately scoped.
