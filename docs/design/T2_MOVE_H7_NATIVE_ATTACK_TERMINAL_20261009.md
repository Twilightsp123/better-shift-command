# H7 — Exact Native Shift ATTACK Terminal Adoption (2026-10-09)

## WH3 H6 12:53 failure, independently observed
- Script: `script_log_091026_1253.txt`, WH3 9.0.2, Controller from H6; Native Bridge 1.0.18 unchanged.
- uid1010 generation4 MOVE->queued ATTACK at model_ms 164400, target1032: arrival brake unproven from 21.69 to 16.52m for >12s; manual MOVE REPLACE at 177200 cancels it.
- uid1010 generation13 MOVE->queued ATTACK at model_ms 193000, target1032: repeated `ATTACK_ARRIVAL_BRAKE_UNPROVEN`, reaches 17–20m at 202700–207500. At 207500ms the *matching Native active ATTACK* is reported as `NATIVE_ADVANCED_BEFORE_PERMISSION`, and Controller issues a MOVE rollback at 207500, ACK 207900. No ATTACK ACK for this generation before session ends.
- Contrast uid1010 generation1: the same feature eventually works only after `NATIVE_IDLE_ROUTE_FINISH` at 75700ms (remaining 15.82m), `DISPATCH_ATTACK` and ACK; the next ATTACK after EXIT similarly needs route completion at 117300.
- Shift key detected true and queued ATTACK captured, so this is a transition policy/premature rollback problem, not missing input, address regression or H6 guide near-pass branch.

## Narrow H7 behavior
- Retain the strict T2B-G11 deceleration / stopping-position pre-ISSUE gate; H7 **never** grants a new proactive ATTACK ISSUE.
- Only when **Native is already executing** the **exact immediately next i+1** ATTACK (V3 provider, `PLAYER_NATIVE` execution lineage), the fresh identity-bound T2B edge cache exists (one poll), canonical current action is `MOVE_ROUTE` rather than `EXIT_ROUTE`, target is live, and there are no prior route debts.
- Must have actual MOVE motion, two sampled positions, current plan progress at least existing `CFG.route_attack_min_progress` (0.60), and both cached and fresh physical distance <= min(current attack predictive threshold, existing `Core.move_idle_finish_envelope`). No new distance/time constants.
- Only opens the **adopt** window `ATTACK_NATIVE_EXACT_TERMINAL`; invokes the existing T1.6 transaction to mark `ATTACK_TERMINAL_HANDOFF` without inventing physical arrival. It does not change the original issue policy, movement algorithm, attack hold/exit, Native DLL/hook/map, RMB REPLACE, i+2 or invalid target behavior.
- Exception applies only to a pure MOVE_ROUTE current block. Exit Route -> Attack remains requiring route completion and existing post-attack engagement evidence.
- Synthetic fixtures: near positive, too far negative, wrong target, Native still on MOVE (issue window remains closed), and i+2 ATTACK. Native race base fixtures and all H4/H6 gates remain active.

## WH3 acceptance required
1. Test standalone MOVE then Shift+ATTACK at medium/far target; watch for the prior `ATTACK_ARRIVAL_BRAKE_UNPROVEN` loop. Under exact native promotion near the MOVE endpoint, `H7_NATIVE_ATTACK_TERMINAL_ADOPT_READY`, `NATIVE_SUCCESSOR_ADOPTED`, `ATTACK_TERMINAL_HANDOFF` should appear **without** `NATIVE_SUCCESSOR_ROLLBACK` on that ATTACK edge.
2. Test MOVE->ATTACK->Exit MOVE->ATTACK (current EXIT route remains strict), fast RMB attack replacing any existing route, and no i+2 skip.
3. Retest H6 uid1006 9-point MOVE route and native rollback. No visual smoothness or actual gameplay regression claims from offline CI alone.
4. If Native does not promote ATTACK until after Controller reassert, or the unit remains outside the existing physical terminal envelope, H7 intentionally will not fix that episode; fresh logs decide next step.

CI artifact retains legacy H4-soft naming but H7 source HEAD/manifest must be inspected. No Steam publication.
