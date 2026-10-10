# WH3 9.0.3 — Original member-level displacement-rate writer and local path tick

**2026-10-10; read-only exact-binary STATIC proof, not a working BSC patch.**
Target EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`. User describes game build as 9.0.3; version resource not independently checked. Original virtual/route context: [MOVE fanout](N1_903_NATIVE_MOVE_MEMBER_FANOUT.md), [receiver](N1_903_MEMBER_VIRTUAL_RECEIVER_RESOLVED.md), [mode selector](N1_903_FORMATION_MODE_AND_MODEL_MOTION_RULES.md).

## New result: actual per-member XYZ displacement differential is computed, not just facing

Exact original function **`0x0315C1E4`** receives member in RCX, new XYZ in RDX and 16-bit new-facing code in R8W. It:
1. Subtracts each member's prior `+0x88/+0x8C/+0x90` pose from new XYZ at `0x0315C237`, `0x0315C244`, `0x0315C25A`.
2. Loads float 1000.0 from `0x0391CF08` and a global integer (original file value 100) from `0x03D0727C`, forms **scale=1000/global_int** at `0x0315C251`. The global may change at runtime.
3. Multiplies all three positional deltas by scale, writes them to **member `+0xE0/+0xE4/+0xE8`** at `0x0315C27E/0x0315C286`.
4. Computes 16-bit angular difference (special handling for `0x8000`), multiplies by original float `0x0391D3E0≈2π/65536` and same scale, writes **member+0xEC** at `0x0315C2B4`.
5. Then writes the supplied new XYZ to **`+0x88/+0x8C/+0x90`** and new 16-bit facing to **`+0xB0`** at `0x0315C2C0/CB/D1`.

**This is direct original member-by-member displacement/change-rate dataflow.** It is closer to motion than a static facing target; it still **does not prove** that `+0xE0` is the ultimate physics solver velocity or what the avoidance system does after it.

## Verified per-member update feeds this function using an agent's own local controller

Original member update **`0x03060700`** reads its own member XYZ `+0x88/+0x90` (`0x0306086D/7D`) and **member+0x2E0 local controller** (`0x030608AF`). It adds controller-local XYZ `+0x13C/+0x140/+0x144` to its newly computed coordinate, then calls the pose/rate writer **`0x0315C1E4`** at original direct E8 site **`0x0306091D`**. **After** that call on this path, the same member controller's virtual `+0x628` runs at `0x0306099B`. A documented compatible virtual implementation `0x0306F438` calls **`0x0315BF14`**, which can independently increment local path segment **`+0x18`** and update fractional progress **`+0x1C`**. These segment indices are not proven to be the user's *clicked Shift waypoints*.

This answers the narrow motion possibility: **one common unit MOVE can issue different member target records, and the original per-member updater is capable of writing different or opposing XYZ displacement-rate vectors based on each member's own pose and trajectory.** It does **not** imply individual high-level Shift queues.

## Explicit offline risk example; DO NOT mistake it for game recording

At original EXE's loaded step value 100, pose old/new `(-1,0,0)→(1,0,0)` yields native-field X change-rate `+20`. Another member `(1,0,0)→(-1,0,0)` yields `-20`; their rate-vector dot product is negative. Conditional mode-3-like **3×3** grid with unchanged slot indices, an abrupt 180° orientation reversal, linear same-progress trajectories and **no avoidance** gives a midpoint conflict for opposite indexed corners. The same conditional fixture with 90° turn keeps the pair 2 units apart. The latter example assumes index retention, linearity and mode3 activation: it **does not prove actual WH3 collision or unmodded Shift choosing mode3**. Real game may reassign slots/avoid dynamically.

## New negative result: mode-3 target-record writer is just a 48-byte vector append

Original mode-3 generator `0x030CA218` directly calls `0x030BE544` at **`0x030CA5B5`**. Machine instructions in `0x030BE544` compare size/capacity, allocate when needed, compute record stride **3×16 = 48 bytes** (`0x030BE57A/7E`), copy member position/facing record including `+0x22` (`0x030BE5BD/C3`), and increment the vector length at **`0x030BE69E`**. This is a target **container push-back**, **not** per-agent collision avoidance or a per-model waypoint-completion test. Any member-to-slot remapping must be resolved elsewhere in the generator (including subsequent `0x030CA5CF–0x030CA5E9` mapping writes) or downstream native steering. Do not mistake this appender for a collision-safe assignment algorithm.

**New complete read-only evidence:** 52/52 original byte guards, 5/5 call edges, three binary scalar checks and 18/18 offline test cases, including the exact supplied EXE and conditional 3×3 90° versus 180° test cases.

## Causal fork still required for a safe Native patch

- If original formation target assignments actually cross under relevant Shift modes, identify group strategy's member-to-slot matching/permutation (including `0x030BE544` inside `0x030CA218`) and how avoidance responds. Prefer original slot-mapping fix, not waypoint pop.
- If targets don't cross but each local controller moves differently, trace native model collision/steering consumer of `+0xE0` and controller state; avoid forcing all members to share velocity/path index.
- Distinguish a shared unit route phase from agent-local spline segment index. Neither is a demonstrated soldier-specific clicked-waypoint arrival flag.
- Native Hook ABI, model lifetime, 9.0.3 runtime motion and safe patch predicate are still unverified. **No DLL/PACK or release.**

**Repro artifact** `BSC_N1_903_MEMBER_DISPLACEMENT_CAUSAL_20261010.zip`: self-contained exact-SHA read-only verifier, 52 precise original instruction bytes with corresponding assembly, five verified E8 targets, three exact binary scalar values, independent 180/90° geometry tests, 18/18 tests PASS (including real EXE), five bounded LLVM disassembly snippets, evidence.json, Chinese report, SHA manifest; game EXE excluded. Grades: STATIC PASS, OFFLINE math/tool PASS, WINDOWS/WH3 NOT RUN, PATCH_AUTHORIZED=FALSE.