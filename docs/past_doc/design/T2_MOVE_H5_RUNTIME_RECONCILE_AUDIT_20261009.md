# H5 — Native reconciliation runtime audit (WH3 9.0.2)

Date: 2026-10-09. Isolated `maintenance/t2move-h5-runtime-reconcile-audit`;
parent `6027a28fcf9eb6766aec60b7c74ee16af01e2acf`. Scope: telemetry and two fail-closed Controller tests,
not a gameplay patch. H4 soft corners, T1.6 commit, 9.0.2 Native map/DLL
are unchanged.

## H4S real-game `script_log_091026_1144.txt`

The battle demonstrates Bridge and Observer startup, 4/4 H4 soft turns
accepted on own Native ACK in 300–400 model-ms, 11 predictive MOVEs,
no controller failures, no `MOVE_AFTER_NODE_COMPLETE`, no
`NATIVE_IDLE_ROUTE_FINISH`, and no `ROUTE_UNRECOVERABLE`.
Across 80 H2 blockers (78 current chord, 2 prior-debt), the corresponding
legacy issue window was false. All four soft turns issued after window
opened. This is not proof of onscreen constant velocity.

Three distinct native rollbacks occur early during player queue input:
- uid 1004 gen 1 model-ms 17400: exact i+1, missing frozen
  `MOVE_PREPROMOTION_CACHE`. The Native queued command can execute
  before an exact-current sample creates the required certificate.
- uid 1004 gen 1 22000: i+2 overrun; intermediate canonical action owed.
- uid 1006 gen 1 40800: nine orders captured in one poll, i+2
  already active; no permission to bypass the intermediate action.

These are not H2 route-veto failures. H5 does not grant adoption
without evidence or for i+2, which would lose the player's route.

A fourth reassert, uid 1004 gen 2 model-ms 82400, belongs to
`maybe_reassert_exit`: contact fallback, 900ms no progress, 0.47 speed.
The attack-to-exit-to-move-to-attack episode is present, but the log
cannot verify actual MOVE->ATTACK visual stop-free motion or sustained
physical disengagement. Another enabled mod reports a missing JSON
module, and this is not a clean A/B matched-route setup.

## Code targets and limits

- `rollback_native_future_to_current`: add canonical index gap, cache
  presence, age and open-window state to rollback diagnostics only.
- `R1.observe_t2move_d`: **retain** exact current V3 proof capture;
  do not synthesize a missing sample.
- `R1.T2MoveEPreview`: **retain** live Native revision, generation,
  lifetime, one-poll freshness and frozen debt verification.
- `Core.reconcile_native_successor`: **retain** i+2 hard block and
  T1.6 exact i+1 commit only after proof.
- `Core.maybe_reassert_exit`: treat independently; the observed
  contact-stall fallback does not prove a scheduler/ACK race.

## Regression and future validation

H5RN-01: same-poll i+1 that outruns first prepromotion certificate
must not commit. H5RN-02: same-poll i+2 must not skip canonical i+1.
H4 6 Controller / 4 Native baseline and mutation gate stay active.
CI must PASS, then pack is an instrumentation build only.

Separate live visual tests: long 45/90/135/180 corners, short 5–15m
zigzag, Move->Attack, Attack->Exit->Attack, two units, RMB replace and
append. Record exact pack SHA and matched same-unit route before any
claim of smoothness or speed gain.

Future behavior changes require proving that current Native Hook can
safely intercept queue promotion or freeze execution before it
overruns. No new distance/angle/time tuneables, auxiliary Q, disabling
rollback, historical merges or Steam release.
