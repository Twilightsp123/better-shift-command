# WH3 9.0.3 Native Research Map — formation-model Shift MOVE

**Correct defect and priority:** [PRODUCT_CAUSE_CORRECTION_20261010.md](PRODUCT_CAUSE_CORRECTION_20261010.md). Original Shift MOVE's user-observed defect is **asynchronous arrivals and turning of soldier models under one unit card**, causing orientation mismatch and crowding; not a proven vanilla unit stopping at every waypoint. MOVE→ATTACK stopping in past BSC was a Lua Controller regression.

## Existing 9.0.3 exact-file anchors — NOT patch permission

User-provided EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`. Game 9.0.3 label from user, version resource unverified; `0x140000000` image base.

| Unit/order-level feature | Research-only RVA | What has actually been shown | Not established |
|---|---|---|---|
| Native MOVE issuer | `0x030323C8` | slot allocation/MOVE construction | per-soldier steering/arrival |
| Ring pop | `0x02F4FD10` | head/count writes and cleanup | root cause of crowding |
| MOVE constructor/vtable | `0x030090BC` / `0x0390B4F0` | native MOVE object type | all soldier-model movement types |
| MOVE work and task lifecycle | `0x03025D70`, `0x030440F8`, `0x03043520` | auxiliary task count/state | soldiers independently owning Shift queues |
| Special native MOVE handoff | `0x0304433C` | conditional original state transfer | universal succession, formation turn coherence |
| Native state driver | `0x0311DE74` | state 0–4 paths and payload rebase | movement speed or model heading semantics |
| Route validator | `0x0310F560` | geometry/route updates and conditional flag | desired speed/arrival distance |
| Geometry early exit | `0x0311F8CB` | guarded route-setup skip | physical braking or intra-unit crowding |
| Normal ATTACK work | `0x03025788` | original attack activation path | any *vanilla* MOVE→ATTACK stop |

All above are exact-file static-machine-code research recorded in the N1_903 reports. No hook ABI, thread/lifetime safety, group coherency or physical outcome is proven. Old 9.0.2 hook map is historical and must not be treated as 9.0.3.

## New N1 exact-file unit/member/formation entry points (2026-10-10)

[N1_903_FORMATION_ENTRY_CALLGRAPH.md](N1_903_FORMATION_ENTRY_CALLGRAPH.md) proves that unit update `0x03043648` calls position-bearing member-list aggregator `0x030421A4` (root count `+0x184`, pointer array `+0x188`, member coordinates `+0x88/+0x90`) and group coordinate function `0x0302AE0C` (group pointer root `+0x32F8`, coordinate subobject root `+0x3C38`), **before** this path invokes original order stage `0x0304433C`. This is source/consumer lead only, **not** proof that member objects are soldier models or that group coordinates are each model destination. See read-only audit tool `maintenance_tools/native_shift_re/audit_903_formation_entry.py`.

**New type/collection distinction:** [N1_903_MEMBER_LAYER_TYPE_GAP.md](N1_903_MEMBER_LAYER_TYPE_GAP.md) proves two different native UnitRoot collections A `+0x184/+0x188` and B `+0x114/+0x118`, both accessed in the SAME root routine. A-member virtual `+0x58` can return another nested pointer array at `+0xBE4/+0xBE8`. Neither type is formally identified as every soldier model. The actual model destination and heading writer remains unknown. Do not revive retired `Entity+0x18` physical assumptions.

**Direct original MOVE→unit route link (new):** [N1_903_MOVE_TO_UNIT_ROUTE_DIRECT.md](N1_903_MOVE_TO_UNIT_ROUTE_DIRECT.md): original MOVE worker `0x03025D70` calls `0x0301287C` at `0x03025E91` and `0x03026022`; route configurator stores a native route descriptor at `root+0x270` (heap or inline branch). Adjacent native function `0x03012A6C` also loads `root+0x270`, reads member-like coordinates and dispatches virtual `+0xC8` before calling `0x0301287C`—**not proven reached from normal queued MOVE or a soldier model**. Distinct unlinked native task `0x0304725C` reads same route then iterates members with pseudo-random coordinate operations; it may be an unrelated AI/scatter task. Avoid false causal attribution.

**Corrected P0 research decision:** [Shared order vs independent model arrival](N1_903_SHARED_ORDER_GROUP_ARRIVAL_HYPOTHESIS.md). Common native MOVE order plus per-model arrival/leg promotion can explain mixed headings without differing high-level commands. First identify whether individual model leg indices actually advance independently; alternatively a single group target update plus physical slot steering may explain it. The original approach must not wait for exact arrival of all soldiers. Current code analysis **does not establish either mechanism**.

## HIGH PRIORITY — missing model-level map

| Required native object/path | Verified 9.0.3 RVA? | Required dataflow/evidence |
|---|---|---|
| Unit/group formation-origin/heading and slot target producer | **NO** | original UnitRoot MOVE task to formation target/slot updates |
| Soldier entity list, slot membership and per-model destination | **NO** | safe pointer, owner, object lifetime, producer/writer xrefs; old Entity+0x18 assumption rejected |
| Individual soldier arrival and leg/turn transition | **NO** | compare before/after native target, orientation and path-advance instructions |
| Unit-wide formation phase synchronization, if any | **NO** | native coordination rules, group transformation timing |
| Collision avoidance and model-space crowding response | **NO** | exact consumer of near-neighbor spacing and path state; distinguish effect from cause |
| Difference between queued intermediate MOVE and normal RMB MOVE | **NO** | native queued flag propagation and per-model negative control |

## N1 method

1. Trace current native queued unit MOVE into **formation origin/pivot and slot assignment**; identify original produced model-level targets, not merely queue-head count.
2. From each slot/target, follow exact soldier movement consumer, per-model arrival/turn criterion, heading state writes and collision response. Identify shared-vs-individual timing.
3. Compare actual decision when soldier A of a unit can turn while B is behind. Validate whether original unit/group synchronization exists and can be narrowly adjusted.
4. Distinguish model-level variance caused by formation target geometry, independent model phase, or avoidance/pathfinding. Record alternate explanations and falsifiers.
5. Review old Lua ATTACK rollback separately, not as native Shift MOVE defect. No original ATTACK patch unless new evidence demands it.

## Evidence and safety

Per new native candidate: exact EXE digest, RVA/instruction bytes, real x64 ABI, pointer provenance/aliases, call graph, read/write sets, ownership/lifetime, unit-versus-soldier scope, negative RMB/blocked-model cases and uncertainty grade. No mutation of raw OrderHead, task counters, VTables, entity component offsets or transfer flags.

Old 16-Hook map, N1 ring-pop and route geometry studies remain relevant **as navigation into native code**, but do not demonstrate which soldier-specific condition creates mixed headings and crowding.

Runtime patch implementation remains blocked until model-level cause, safe local delta and offline/Win64 proofs exist. Do not request repeated user WH3 tests during N1.
