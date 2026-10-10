# Real WH3 V3 evidence: native Shift progressive turn STILL crowds models (2026-10-10)

**Binding correction to BSC research acceptance.** The user explained that CA's original queued Shift path can decompose an about-180-degree turn into gradual subturns (described as 90° + 90°). **That geometry is valid original behavior, NOT a bug to remove.** We are fixing crowding and divergent model motions *during* native progressive turns, not forcing instantaneous 180° heading flips or geometrically identical normal RMB routes.

## The reported defect has met its existence proof gate

Real WH3 V3 logs from the same UnitRoot `0x2128a6f80` captured 36 stable member identities over both nonqueued and queued original MOVE (the unit source count was 60; the subset is 36).

- In the **35–43 second original queued MOVE interval** (40 sampled frames), the observed unit-centroid 2-second-window **travel direction** changed gradually from about +33° to -146°, a continuous net sweep around **179°**; this is **not a readout of the game's internal waypoint or exact 90° subdivision**.
- During that progressive turn, **29/40 frames** had a nearest sampled member distance below 1.0 game-world coordinate units, **10/40** below 0.7, minimum **0.474**. These thresholds are descriptive, not actor collision radii or physical hit tests.
- Over the captured **same-unit** V3 movement samples: ordinary MOVE **0/139** frames had nearest member distance below 1.0; queued MOVE **85/194**. We do **not** require these different user-command paths to have matched terrain/corner geometry to accept the user-observed native Shift crowding defect. The numbers remain descriptive observational evidence, not a proof of the *specific original-code cause*.
- The user's earlier original trajectory samples additionally included near-distance opposing member movement (e.g., recorded at ~14.65 s, ~18.86 s, and ~37.33 s). Do not reinterpret facing code as velocity; existing independent member X/Z pose deltas and change-rate measurements support actual differential movement.

**GRADE: WH3 OBSERVED DEFECT = PASS.** Do not ask the user to further prove that original Shift has crowding, and do not treat exact regular RMB-vs-Shift route matching as a gate.

## Three distinct standards, no moving goalposts

**1. Defect exists: PASS (now).** User-visible crowding + time-aligned native member coordinates, spacing compression and direction spread during real *progressive* Shift turns is enough to accept this symptom.

**2. Native patch selection: OPEN.** Need a version-guarded, actual-executed original code decision that controls group target/slot association, per-member trajectory handoff or collision/avoidance, and whose output can logically account for the crowding. Do not confuse an unobserved code path with this user's path: V3 reports `0x03025D70` active but `0x0302DB44`/`0x030D5490` group fanout unhit, so the actual MOVE task path via `0x0301287C` and `0x02F2C734` takes priority. A function-level causal hypothesis can be sufficient to build a *reversible test-only patch* after ABI and negative checks; mathematically proving every possible WH3 collision is NOT required.

**3. Patch works: compare the SAME native queued Shift turn case before/after.** Retain CA's progressive 90°+90°-like route. Reduce near-spacing duration and harmful relative heading spread without skipping required bends, pathfinding failures, native order corruption, attack regressions, or permanently blocked stragglers. Ordinary RMB and ATTACK serve as no-regression controls, **not geometry-matched fault-proof requirements**. Physical engine gameplay improvement can only be certified in final controlled WH3 acceptance; STATIC tests do not make that claim.

## Next work actually required for a patch

- From the **V3-confirmed active** original MOVE worker `0x03025D70`, trace `0x0301287C` into its actual native task `0x02F2C734`, group/member target producer, per-member motion consumer and any route-stage or anti-crossing predicate. Determine why the V3-probed independent `0x0302DB44` / `0x030D5490` route did not run; don't build a patch solely on that route's mode3 3×3 example.
- Discriminate **a shared group target generating crossing individual paths** from **models independently advancing local track/turn phases**. Change the smallest already-original group/slot/leg predicate, not raw member velocity, all-model exact-arrival barriers, Lua reissuing, or direct native OrderHead.
- Use offline evidence-derived tests + isolated Windows guarded hook/rollback tests before a *single* in-game before/after Shift test. The existing V3 log is the prepatch reference.

## Reproducibility

Conversation archive **BSC_903_SHIFT_ARC_EVIDENCE_20261010.zip** includes `analyze_shift_arc.py` (stdlib only; re-reads original `captured_move_v3.jsonl` and `verdict_v3.json`), 2 small synthetic unit tests, `turn_frame_metrics.csv`, `turn_evidence.json`, Chinese reading note and SHA256 manifest. No original game EXE or user's raw game logs are redistributed in the archive. Script output is descriptive/observational and does not authorize a Native Hook.

**As of this document: no fixed DLL/PACK.** The defect is accepted; exact patch location/ABI and improvement are distinct work items.
