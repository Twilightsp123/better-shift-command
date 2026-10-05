# Direct T2 experiment archive — historical, not current runtime

These files preserve 2026-10-05 experiments that were performed before the documented D1 T1/T2-C prerequisites were respected.

- `controllers/t2b_direct_runtime_candidate.lua`: direct Move→Attack T2-B candidate that produced good WH3 runtime behavior; use as evidence/reference when reimplementing T2-B through the shared evaluator.
- `controllers/native_move_passthrough_diag.lua`: diagnostic passthrough build used to isolate destructive Move rollback; rejected as product architecture because BSC must improve Move→Move rather than surrender it to vanilla Shift.
- archived T2-A/hairpin tests remain under `archive/legacy_move_scheduler_tests/`.

Current runtime authority is the behavior-neutral T1 shared evaluator in `source/better_shift_command.lua`.