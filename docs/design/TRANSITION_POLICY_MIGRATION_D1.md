# Transition Policy Migration D1

Status: **APPROVED IMPLEMENTATION PLAN — NO RUNTIME CHANGE IN THIS PACKAGE**

The migration deliberately avoids a broad convergence rewrite. Each stage must be independently testable and revertible.

## T0 — Freeze the corrected Native baseline

Baseline requirements before gameplay work:

- Native `1.0.17-corepath-wh3-6c104-movevtfix` remains unchanged.
- Full Move VTable `0x03910AA8` remains authoritative.
- No R1/R2/R3 experimental outcome resolver code is reintroduced.
- Current Windows delivery/candidate hashes are archived.

No EXE reverse engineering is needed for T1–T3 unless a new Native contradiction appears.

## T1 — Structural TransitionPolicy refactor, behavior-neutral

### T1H — Hidden policy/MCT scaffold (implemented)

- Add immutable PolicyProfile schema/presets and future adapter boundary.
- Register **no** MCT UI and make no `get_mct()` call.
- Route legacy `attack_hold_ms=3000` through `engagement_hold_seconds=3.0`.
- Reserve all movement policy values without applying them yet.

This is a substage of T1 and does not claim the shared transition evaluator is complete.


Goal: create the new policy plane without changing decisions.

Work:

1. Introduce `TransitionPolicy` namespace/module.
2. Move current Move→Move `route_handoff_ready()` decision into an evaluator adapter.
3. Preserve current strict Move→Attack result exactly.
4. Route proactive `advance()` and SC6 reconciliation through the same decision object where applicable.
5. Preserve current SC6 behavior in tests during this stage, including immediate-MOVE rollback, so refactor equivalence can be proven.

Gate:

- existing controller suite unchanged PASS;
- new equivalence tests compare old/new decisions over fixtures;
- mutation catches bypass of evaluator.

## T2 — Smooth-default behavior correction

This is the first intentional gameplay change.

### T2-A — Immediate future MOVE reconciliation

Change SC6 from:

```text
future.type ~= ATTACK => rollback
```

to:

```text
future_index == i+1
→ evaluate MOVE→MOVE or MOVE→ATTACK policy
```

Immediate Move successor may be adopted/soft-adopted if the current route semantics permit. `i+2` or later remains hard rollback.

### T2-B — MOVE→ATTACK terminal handoff

Promote bounded `attack_geometry` into a real transition policy:

- prior route debt must be clear;
- target must be exact and viable;
- bounded progress requirement;
- path-safe or terminal corridor proof;
- accepted Attack gives explicit `ATTACK_TERMINAL_HANDOFF` credit.

### T2-C — Hysteresis

Add separate `issue_window` and `adopt_window` so Native may be accepted slightly earlier than Lua would proactively issue.

Gate:

- no stop-before-Attack in standard straight/turn fixtures;
- no short-zig-zag waypoint swallowing;
- no multi-action skip;
- no target false-adopt;
- far-early Native successor still rolls back.

## T3 — Presets and MCT

Only after T2 default Smooth behavior is stable:

1. Add immutable `PolicyProfile` snapshot.
2. Implement Smooth/Balanced/Precise presets.
3. Add Custom advanced controls.
4. Missing MCT falls back to built-in Smooth.
5. MCT values alter only soft policy bounds.

Do **not** use MCT to hide a bad default. Smooth must pass runtime regression before MCT is considered complete.

## T4 — Attack/Exit policy tuning

After Move transitions are stable, optionally expose:

- Minimum Engagement Time;
- Disengage Priority;
- narrower Exit→Attack terminal handoff.

FEG, exact execution identity and bounded recovery remain architectural authorities.

## Separate stream — lifecycle/teardown

Battle teardown / observer suspend-resume and third-party UI listener errors are not part of Transition Policy D1. Track them separately so a teardown fix cannot silently change movement behavior.
