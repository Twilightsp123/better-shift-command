# 2026-09-29 Transition Policy runtime evidence

These artifacts are preserved to explain why `BSC-TPOL-D1` exists.

- `script_log_290926_1818.txt`: corrected Native bridge is operational; contains exact Native successor rollback events including `NATIVE_ADVANCED_BEFORE_PERMISSION` for Attack and multiple future-Move rollback events. The same log also contains unrelated `jg77_battle_ui.lua` teardown errors; those belong to the separate lifecycle stream.
- `script_log_290926_1833.txt`: cleaner battle load without `jg77_battle_ui.lua`; records `NATIVE_FUTURE_OVERRUN` / rollback while exact active execution is a MOVE.
- `BSC_COREPATH_RC8_WINDOWS_DELIVERY.zip`: audited Windows build evidence for Native `1.0.17-corepath-wh3-6c104-movevtfix`.

Do not use the UI teardown errors as proof of TransitionPolicy behavior, and do not use D1 design documents as proof that D1 is already implemented.
