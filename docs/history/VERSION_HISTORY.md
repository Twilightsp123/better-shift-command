# Version History — Engineering Milestones

- **v6.5.x** — predictive Move handoff kernel proved useful in real battles.
- **v6.5.7a/b** — stale route resurrection / override-lock failures; abandoned.
- **v6.6.0/SP1** — `ordered_position` and gesture-boundary architecture disproved; abandoned.
- **v7.x native attribution work** — recovered unified order chronology, Shift queued semantics, target identity and Bridge requirements.
- **Native Bridge v0.5.0** — controlled real-game validation PASS; frozen v1.0.0 dependency.
- **P1C/P1D/P1E** — Controller bootstrap, terminal Attack transition and test-contamination fixes.
- **P2A/P2B** — engagement hold and disengage; removed invalid fixed approach timeout.
- **HF3/HF4** — fixed idle Shift entry and replaced immutable plan freeze with appendable active shadow timeline.
- **HF4.1** — validation/reporting cleanup.
- **HF5 / Controller 0.2.5 / v1.0.0** — Attack-first adoption; full P1/P2 runtime validation and first public release baseline.
- **Steam self-contained prototype** — embedded exact Bridge + MinHook bytes in PFH5 and materialized them at first battle load; proved first-battle native deployment and same-battle use.
- **v1.0.1 TESTFIX A** — introduced per-kind calibration/native canonicalization fix but accidentally changed native build family to VS2022/v143; real game failed at `OBSERVER_MINHOOK_CREATE_FAILED`; rejected as release artifact.
- **v1.0.1 TESTFIX B / v142** — same logic rebuilt on validated v142 family; real-game hook install PASS, pure Move armed with `accepted_attack=false`, long/multi-unit routes continued past issue 50, predictive Attack remained functional.
- **v1.0.1 formal release** — Controller 0.2.6 + Bridge 0.5.1-per-kind-calibration, v142-only release builder, self-contained Steam deployment, production logging cleanup.
