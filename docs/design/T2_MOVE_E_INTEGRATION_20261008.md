# T2-MOVE-E — isolated joint controller integration (NOT WH3 promoted)

2026-10-08. Parent: `maintenance/t2move-d-evidence` at `1249a2c902d83861594a8e945c489bf9e4c83996`.
Candidate branch: `maintenance/t2move-e-integration`.

## Purpose and separation

This is the **first live-controller code candidate** that can adopt an exact Native `i+1 MOVE` through cached A/B/D policy evidence. It is not released or merged to the T2-B validated construction baseline. WH3 is unavailable; the gameplay promotion gate is deferred.

- D gathers the frozen exact-current position/route proof, revision, lifetime and deterministic debt signature.
- E binds current/successor **action table identity** in addition to D's scalar action identity; a replanned canonical action cannot impersonate a cached proof.
- SC6 continues to read exact V3 current/future execution once, and only exact immediate `i+1 MOVE` can reach E. `i+2` is never legalized.
- E rechecks the current generation/revision/lifetime/action IDs/table objects, debt signature, prior poll freshness and recognized execution lineage.
- A interprets the frozen shared Move `issue_window`; B may open an adopt-only **temporal** one-poll band while preserving route legality. E does not recompute pre-promotion geometry from post-promotion trajectory.
- The same R1.TransitionPolicy evaluator constructs the one decision. Proactive Move issue remains unchanged; SC6 consumes only `adopt_window`.
- On adoption, unchanged T1.6 `Core.begin_transition_txn()` -> `OBSERVED` -> `Core.commit_transition_edge()` applies `STEERING_CORNER` completion or `PATH_SAFE` debt registration, and preserves earlier SC3 debt.
- Closed/absent/stale proof falls through to bounded existing rollback. An unavailable Native recovery budget does not create false credit.

## Known conservative limits

- Pre-promotion proof is required; if the current Move was semantically complete before any D capture, E does **not** infer permission from later Native motion.
- Hysteresis never broadens a route, corner, debt, or adjacent-leg limit.
- No T2-B G1.1 behavior change, no gameplay CFG scalar modification, no Native/address changes.
- No guarantee yet that offline success eliminates WH3 fold-back/stepwise movement: RT-TP-04/05 will be required when runtime access returns.

## Verification

Require direct controller fixture: PATH_SAFE and STEERING_CORNER adopt with correct commit/debt credit; too-early/overrun/revision/identity rejects; no duplicate Native issue; no repeated rollback on an adopted current successor. Retain full 46-job maintenance and all A/B/C/D tests. Do not claim WH3-PASS from simulated fixtures.
