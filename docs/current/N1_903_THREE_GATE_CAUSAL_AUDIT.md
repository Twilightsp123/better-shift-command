# N1 — Three-gate static causal audit: binding, model displacement, avoidance (2026-10-10)

**EXE:** SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, image base `0x140000000`. Game 9.0.3 is user-supplied label; game EXE only available offline, not run on Windows. **No DLL, PACK, Hook, runtime observations or fixed game behavior.**

## Gate 1 — consecutive MOVE model↔slot binding

Original `0x030D5490` pairs `group_member[i]` with strategy-generated `record[i]`. **More precise new fact:** `0x030D54FC` calls `0x02F5F868`, whose instructions copy the record's positional fields into a distinct per-member task struct and its facing from R9W into task+0x40 (`0x02F5F86E–0x02F5F8AD`). The per-member receiver `vfunc+0x368` is called at `0x030D550F`. Group postprocess `vfunc+0x20` occurs **after the entire member loop** at `0x030D5522`. Therefore modifying only the old generated record *after* dispatch does not by itself retroactively change the already-copied task parameters. Later independent group callbacks may still affect the member.

This proves **index-based issuance and by-value task copy in the audited path**, but does not prove stable identity or selected strategy across two *actual queued Shift* moves. The runtime mode is a mutable native field `[[UnitRoot+0x3D48]+0x248]`; static EXE cannot reveal the field value for a unit in the user's battle.

## Gate 2 — actual member motion versus facing

Original member tick `0x03060700` reads its own member+0x2E0 controller and writes a newly computed pose through E8 `0x0306091D → 0x0315C1E4`. The latter derives XYZ difference rates into member+0xE0/+0xE4/+0xE8 and angle difference rate into member+0xEC, then updates pose. Original controller local path segment is updated later. **These are per-member motion differences, not different high-level Shift orders.**

Conditional two-member example under the original rate formula and file's scalar baseline: X:-1→+1 yields +20; X:+1→-1 yields -20. This **is an offline input/geometry example, not measured velocities from WH3**. A rendered game unit may have avoidance/steering responses not visible in the selected body.

## Gate 3 — does native avoidance erase the crossing?

Original `0x03086910` computes a relative-position dot member displacement-rate and branches by sign (`0x03086A50–0x03086A88`). It can reach `0x03058E0C` pair geometry at `0x03086AD5`. It also directly calls **`0x030C6788`** at two sites `0x03086C37` / `0x03086C67`. The inspected `0x030C6788` block checks member-pair distance against radii, then records **group member-contact bitsets** at `0x030C68D9` and `0x030C691A`, with auxiliary lists/counters. This is *contact/proximity recording in this path*, **not a demonstrated direct desired-speed, model-velocity or detour-target correction**. The bitsets may be consumed later; cannot conclude the engine lacks avoidance globally. Neither can we claim Shift already avoids the user's crossings.

Another group postprocessor `0x030E0AA8 → 0x030E07C0` may update 48-byte record status bits, but follows the by-value task dispatch and is not a verified immediate re-slot optimizer.

## Conditional geometric counterexample, NOT gameplay

Assume mode3-style 3×3 centred target layout, retained member indices, rigid unit target-frame rotation, synchronous straight interpolation and no avoidance. Original member[i]→record[i] issuance enables 36/36 pairs to coincide at t=0.5 on an exact 180° rotation, but 0 on 90° and 135° at t=0.5. A one-time bijective opposite-index remapping preserves the 180° target point set and eliminates the specific all-member midpoint convergence. This **does not demonstrate WH3 uses this strategy, fixed interpolation, or actually collides**; remapping may violate rank identity and combat orientation.

## Final causal disposition

| Evidence gate | Static result | Actual native gameplay result |
|---|---|---|
| Two consecutive MOVE assignments | index pairing and task copy proven on one native issuer path | strategy, member identity/order across consecutive real MOVE: **NOT OBSERVED** |
| Model movement | per-member pose/rate writer and controller update proven | time-aligned pair trajectories on real Shift: **NOT OBSERVED** |
| Avoidance | movement-direction check and group contact bitset recording proven elsewhere | actual Shift path corrected/not corrected by avoidance: **NOT OBSERVED** |

**No authorized patch site or proven root cause yet.** The closest candidate IF dynamic proof confirms crossing is one-time constrained member↔record pairing **before `0x02F5F868` creates copied tasks**, not raw OrderHead mutation, postprocess-only record edits, forced local segment indices, member modes or Lua command replay.

## Repeatable self-contained evidence

Complete offline archive supplied in the conversation: `BSC_903_THREE_GATE_CAUSAL_AUDIT_20261010.zip`. It contains `verify_triptych.py`, `test_triptych.py`, exact-EXE evidence JSON, bounded original disassembly snippets, SHA256 manifest and detailed Chinese report. **29 frozen opcode byte matches, nine original E8 call targets, mode3 VTable method and 14/14 offline tests** pass. Original EXE not redistributed. This proves static program structure and conditional geometry only. WH3 runtime unavailable in this execution environment; don't invent observations or claim a completed fix.
