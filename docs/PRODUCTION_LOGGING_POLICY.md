# Production Logging Policy — v1.0.1

## Decision

Production uses `DEBUG_TELEMETRY=false`. High-frequency success telemetry is not the Workshop default.

## Production retains

- startup/version and Bridge ABI/version success;
- native component WRITE + byte verification when an embedded DLL actually changes/must be materialized;
- Controller fatal failure and Bridge gate/native errors;
- refusal/degradation warnings needed to diagnose incompatible builds/CA updates;
- session-end diagnostics.

## Production suppresses (debug-only)

- normal `NATIVE_EMBED_KEEP`;
- per-order `DISPATCH_MOVE` / `DISPATCH_ATTACK`;
- per-order `OWN_MOVE_ACK` / `OWN_ATTACK_ACK`;
- `PLAN_ACTIVATED` / ordinary `GEN_CANCEL` success flow;
- `ATTACK_HOLD_BEGIN/SUSPEND/DONE` success flow;
- heartbeat, Journal ORDER/action capture, transition/post-Attack samples, physical exit observations;
- `OWN_MOVE_CANONICALIZED` geometry diagnostic unless debug telemetry is enabled.

## Error boundary

`OWN_MOVE_PAYLOAD_MISMATCH` was removed as a release-fatal rule because exact XYZ equality is not the proven identity authority after CA rebuilds a native Move. Non-finite accepted coordinates still produce `OWN_MOVE_PAYLOAD_INVALID` and fail closed.

## Debug procedure

For a user report, create/use a debug build with `DEBUG_TELEMETRY=true`, reproduce once, collect the log, and return to production logging afterward.

## Evidence integrity

Historical HF5 debug evidence and v1.0.1 release validation are preserved as separate milestones. Do not rewrite old evidence to match new production logging behavior.
