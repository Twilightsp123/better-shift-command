# Hidden MCT Interface — TPOL-T1H

Status: **IMPLEMENTED RUNTIME SCAFFOLD; NO USER-VISIBLE MCT UI**

## Purpose

T1H reserves the policy/profile interface now without introducing an MCT dependency or a new test surface while formal runtime testing is inconvenient.

## Runtime contract

The controller contains `R1.Policy` with:

- schema metadata and safe ranges;
- Smooth/Balanced/Precise preset values;
- `compile(values, source)`;
- `from_mct_values(values)` — future adapter boundary;
- `snapshot_hidden()` — current runtime source;
- immutable active snapshot at battle script load.

T1H deliberately contains **none** of the following:

```text
get_mct()
register_mod(...)
create_settings_page(...)
add_new_option(...)
```

Therefore no BSC MCT page, checkbox, slider, dropdown, or visible option is created in this stage.

## What is actually wired in T1H

Only one profile field is connected to existing runtime behavior:

```text
engagement_hold_seconds = 3.0
→ engagement_hold_ms = 3000
→ CFG.attack_hold_ms
```

This is behavior-neutral relative to the prior production baseline because the old literal was already 3000 ms.

The following fields are captured/reserved but intentionally do not alter gameplay yet:

- `movement_cornering`;
- `attack_handoff`;
- `route_fidelity`;
- `native_successor_tolerance`;
- `disengage_priority`.

They become active only in the later T2/T3 migration stages after dedicated regression gates exist.

## Future MCT adapter

A future MCT script should do only two jobs:

1. read user-facing options;
2. convert them to a plain Lua table and feed that table into `R1.Policy.from_mct_values(values)` before the per-battle snapshot is frozen.

The adapter must not directly mutate SC1–SC6 CFG globals.

## Why no UI now

The hidden stage lets live battle observation continue with one stable default profile while preventing an unfinished MCT surface from becoming part of the support/compatibility contract.
