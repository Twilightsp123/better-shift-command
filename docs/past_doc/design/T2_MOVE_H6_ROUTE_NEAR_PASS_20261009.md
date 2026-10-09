# H6 — Route Guide Near-Pass (2026-10-09)

## Source observation — WH3 12:10 (H5)
- `script_log_091026_1210.txt`: uid 1006, generation 1, 9-node MOVE chain.
- Action 5 -> 6 was ACK-committed at model_ms **64200** and left action 5 route debt. Its strict tolerance was **3.889415 m**.
- Action 6 was marked `NATIVE_IDLE_ROUTE_FINISH` at **72700**; `ROUTE_UNRECOVERABLE` at **74000** with action-5 best distance **5.112033 m**, then **15.656335 m** from the guide and no progress for **8400ms**.
- The logs do not record complete body positions around the old guide. WHETHER H6's actual forward plane-crossing condition was met in that episode is **unverified**. H6 is a falsifiable experiment rather than a claimed in-game cure.

## Semantics
- Keep existing `CFG.route_debt_soft_handoff_grace_m=1.5` from H4 SC3; no new threshold or lookahead parameter.
- Only for a previously **Native ACK-committed** same-block MOVE->MOVE guide with outstanding route debt.
- Observe two successive real observer positions; require forward crossing of the canonical waypoint plane normal to the inbound leg, positive actual motion in that direction, and traversed segment miss <= strict debt tolerance + existing SC3 soft margin.
- Retire as `ROUTE_GUIDE_NEAR_PASS_ACCEPTED`, log `GUIDE_ONLY_NOT_PHYSICAL_ARRIVAL`. It is NOT `ROUTE_OBLIGATION_SATISFIED`, and independent H1 physical-arrival proof does not trust the new reason.
- No settlement from stale closest approach, idle timeout, queued Native i+2/i+3, rejected commands, stationary sampling, or a MOVE->ATTACK edge. Current Move->Attack, T1.6 commit cursor, generation/revision and Native ACK rules are unchanged.
- If distance stays outside the bounded margin or an incoming-plane crossing is unobserved, debt **remains unpaid** and existing route protection continues.

## Evidence and tests
- New `maintenance_tools/t2move_a/test_t2move_h6_near_pass.lua`: positive bounded forward crossing; lateral miss; reverse crossing; no early Attack; rejected Native ACK; prohibited U-turn.
- CI continues H4 controller tests, Native V3 parity and H5 negative race tests, H4 mutation gates, full regressions, verified Windows v142 Native 9.0.2 DLL and normal/DEBUG PACK seal.
- **Required WH3 test:** repeat uid 1006's 9-MOVE tight turn, with video and DEBUG logs. Confirm `ROUTE_GUIDE_NEAR_PASS_ACCEPTED` only on real crossing, `ROUTE_UNRECOVERABLE` absent, all actions complete in order, and no forced pause or skipped leg. Also verify short zigzags, 90/180, RMB replace, Attack->Exit.
- 9.0.2 Native DLL, map candidate and hook code remain byte-locked. No Steam publication.
