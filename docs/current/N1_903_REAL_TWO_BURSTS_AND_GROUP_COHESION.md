# N1 — WH3 V3 real game: two fast native order bursts with opposite crowding outcomes

**2026-10-10; actual captured game data + exact EXE machine-code evidence.** EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`. Same native UnitRoot `0x2128a6f80`, mode 0, sampled 36 of the unit's 60 source members. Do not switch BSC product diagnosis back to "vanilla Shift stops."

## The decisive same-unit negative control

| Captured same-unit period | Distinct original MOVE-work entrances | Queue count evolution | Subsequent real member motion |
|---|---:|---|---|
| **27.324–28.035s** | **16 in 711ms** | **16 → 1** | 28.1–33.5s, **0/26 frames** with nearest sampled member spacing <1; only **3/26** frames with a near and direction-opposing member pair |
| **33.556–34.239s** | **15 in 683ms** | **15 → 1** | 35–43s, **29/40 frames** with nearest spacing <1; **32/40** with a near direction-opposing pair; nearest observed distance **0.474** |

Native `MOVE+0x08` work entry is *not* guaranteed to mean physical arrival. No further same-unit work entry occurs between **34.239s and 47.460s**, while member physical movement continues through CA's progressive turn. In the later turn, the 36 sampled member identities are stable across all 40 frames and all **1440/1440 actor mode readings are 0**, with identical group and affiliation pointers. This **disconfirms member+0x104 mode divergence as the explanation of THIS episode** and argues against blaming rapid original queue preprocessing *alone*. Ordinary MOVE vs Shift need not follow identical paths to acknowledge the observed crowding.

Proximity/opposing-pair diagnostic is descriptive: 2D member spacing <2, each X/Z displacement-rate magnitude >0.25, cosine <−0.25. These values are **not collision radii or collision notifications**; the 197 opposed near-pair observations in 40 frames may repeat the same pair. User's supplied normal/queued movement confirms original Shift progressive bends and visible crowding; don't demand a new symptom existence test.

## New reverse-engineered existing group cohesion mechanism

The original code already has a **group-model-to-target distance** evaluator, RVA **`0x030D572C`**:
- Iterates native group member list +0x24/+0x28, checks each member+0x24C.
- Computes X/Z distance from member+0x88/+0x90 to indexed generated target; increments `group+0xD0C4` for members beyond native radius/mode threshold (instruction `0x030D580E`).
- Accumulates and divides by active member count. Writes current native tick into `group+0xD0B8` only when average falls below input threshold (`0x030D5862`, `0x030D5878`).
- Readiness query **`0x030D5628`** checks stamped tick and a native two-step time condition.
- Distance updater is called via `0x030D56BC` (direct sites `0x03044FAF`, `0x0304516B`, `0x03283806`). The actual observed V3 mode0 execution has not been linked to these callers.

In contrast the inspected original **conditional special MOVE transfer** in queue processor `0x0304433C` checks current original virtual +0x40 `0x03039FB0`, next +0x38, passes state to next +0x48 `0x03040864`, then calls **original pop `0x02F4FD10`**. This local path checks transfer state+0x20==4/+0x24!=0 and group flags via `0x02D63794`, **but does not directly query group+0xD0B8/+0xD0C4**. The V3 logger did not sample this exact branch taken/not-taken, so do NOT conclude all 15 quick entries were its result, and do NOT blindly replace its eligibility predicate with group average distance.

## Repair research decision now narrower

1. **Do not globally slow native queue head progression:** two similarly rapid same-unit bursts had very different physical crowding; CA may legitimately pre-plan a series of waypoints.
2. **Do not force all local model segment indices or action modes equal:** actual V3 members were already all mode 0; local spline phases reflect physical positions.
3. Determine which original mode0 group/route controller creates **differential member local curves under sharper bends**, and where native group distance/status constraints actually feed route-state reuse. If one actual native original formation policy permits dangerous target crossovers, change that **existing narrow policy**, not Lua command issuing or raw queue slots.
4. Real game before/after verdict for same Shift bend may be required later for actual efficacy; do not ask the user to re-prove that crowding exists.

**Repeatable local audit:** `BSC_903_REAL_QUEUE_MOTION_CAUSAL_20261010.zip` contains a SHA-pinned read-only PE byte/call verifier (14 exact opcode guards, six E8 call edges), a real-V3 timeline/near-motion analyzer and 10/10 tests (including actual uploaded V3 replay and exact original EXE). It does not redistribute the EXE or full game logs, install a Hook, or contain a finished DLL. **N1 root repair ABI/target remains open.**
