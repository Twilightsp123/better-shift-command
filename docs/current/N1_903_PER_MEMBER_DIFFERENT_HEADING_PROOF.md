# N1 WH3 9.0.3 — Proven different member target/facing data under ONE native MOVE

**Evidence date:** 2026-10-10. **Positive static finding, not runtime velocity or a repaired mod.**

User-provided exact EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, PE image base `0x140000000`. The game version 9.0.3 label is user-supplied; VERSIONINFO has not been independently confirmed.

## Full original instruction dataflow, NOT a different-Shift-command assumption

1. Original MOVE issuer `0x030323C8` reaches native group route update `0x0302DB44` and member fanout `0x030D5490`.
2. One constructor-backed original formation strategy VTable `0x0390F180`, directly referenced by RIP-relative LEA at `0x030C7E1E`, points virtual **+0x48 to `0x030CA218`**.
3. That strategy computes member-indexed position records and **varying 16-bit heading-like codes** from row and column offsets. Original `0x030CA5A8` calls `0x030C2F64`, which writes member-specific position fields into record `+0/+4/+8` and code to **record+0x22** at `0x030C2FB8`.
4. Group fanout `0x030D5490` reads **record[i]+0x22** at `0x030D54F7` for each member and calls original `0x02F5F868`. That constructor stores the code into **payload+0x40** at `0x02F5F8AD`.
5. Native member receiver `0x0306B9F0` reads **payload+0x40** at `0x0306BACE`, dispatches to member virtual `+0x100` or `+0xE8`; original member functions can write the supplied code into **member+0xB0** at `0x0315F54C` or `0x0315F34D`.

Thus a SINGLE original high-level MOVE can produce distinct member positions and facing instructions. No distinct per-soldier high-level Shift queues are required. These data are **not proved to be measured physical velocity vectors**; an original formation may intentionally assign different facings.

## Exact original 3×3 branch counterexample

The `0x030CA218` generator uses `sqrt(member_count)`, row/col counters and a true original `0.5f` constant (RVA `0x0391CBC8`) to center the slots. For a 3×3 member arrangement and same base facing code `0`:

- row 0, column 0: offsets (-1,-1) cause branch `0x030CA45C–0x030CA465`, giving `base-0x2000 = 0xE000`.
- row 2, column 2: offsets (+1,+1) cause branch `0x030CA481` and `0x030CA586`, giving `base+0x6000 = 0x6000`.
- Their difference modulo 16 bits is **0x8000**. This is a real original *assigned facing-code* difference on this strategy, not a simulation of actual WH3 movement speed.

A separate simple motion-geometry **possibility example**, NOT a WH3 observation, swaps two model positions (-1,0) and (1,0) during an abrupt 180-degree formation turn. Displacements (2,0) and (-2,0) have negative dot product and intersect at the center. A common group MOVE with different assigned model trajectories can therefore geometrically permit crossing/crowding, even without individual Shift waypoint-completion decisions.

**Critical limitation:** strategy `0x030CA218` is original and constructor-backed, but which strategy ordinary queued Shift chooses for a specific unit/formation is unverified. The game might deliberately assign different member facings in this strategy, and collision/pathfinding could avoid physical overlap. This is **positive proof of different member target/facing instructions and a possible collision mechanism**, NOT proof of the actual complained-of cause or a safe Hook.

## Reproducibility

Read-only `audit_member_heading_divergence.py` in conversation artifact **BSC_903_PER_MEMBER_DIRECTION_STATIC_PROOF_20261010.zip** verified **42 exact x64 instruction guards, 6 direct E8 call targets, native strategy VTable target, constructor RIP-reference, and original half-grid scalar** against the pinned game EXE. **8/8 local tests PASS**, including exact EXE verification, alternative-base-code checks, hash-failure protection and isolated collision-geometry counterexample. Archive includes complete source, tests, original LLVM excerpts, JSON evidence, Chinese full report and SHA256 manifest; game EXE excluded.

**N1 next causal discriminator:** confirm which native strategy ordinary Shift selects, and distinguish each member's *assigned orientation/slot destination* from its **actual movement velocity** and path-follow completion. Do not force common member+0xB0 orientation, synchronize local path indices, or replace native group formation rules. No DLL/PACK/Windows/WH3 test, **no playable patch yet**.
