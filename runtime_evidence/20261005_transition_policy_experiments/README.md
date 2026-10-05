# 2026-10-05 Transition Policy runtime experiments

These logs are historical runtime evidence used to falsify several direct T2 implementations before the project returned to the documented D1 migration order.

- `script_log_051026_0842.txt`: direct T2-B Move→Attack terminal handoff candidate. Repeated `ATTACK_TERMINAL_HANDOFF ... mode=ISSUE_ACK` was observed and the user reported no Attack pause. This is useful T2-B evidence, but that direct patch is **not current runtime** after the T1 re-anchor.
- `script_log_051026_0950.txt`: direct T2-A immediate-MOVE adoption candidate. Early `STEERING_CORNER` adoption on fold-back routes correlated with formation self-compression.
- `script_log_051026_1020.txt`: stricter hairpin candidate. Repeated `HAIRPIN_PROGRESS_REQUIRED` rollback/reassert correlated with stepwise movement.

The later native-Move-passthrough build was a diagnostic isolation experiment, not the product architecture. It is preserved through Git history / archived source but was not promoted as a gameplay baseline.

Current authority after these experiments is the behavior-neutral T1 shared TransitionPolicy refactor. T2 must be reintroduced only through the staged D1 evaluator/hysteresis architecture.