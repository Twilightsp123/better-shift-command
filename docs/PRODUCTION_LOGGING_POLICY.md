# Production Logging Policy

## Decision

The research build's high-frequency telemetry is **not suitable as the default Workshop build**. It was required to prove geometry, engagement timing, physical separation and cancellation, but it adds repeated string formatting and log I/O during battle.

## Production default

`release/production/queue_probe.lua` sets:

```lua
local DEBUG_TELEMETRY = false
```

Production retains low-frequency operational events such as:

- startup/version/Bridge status;
- Controller failure and Bridge gate fault;
- verified command dispatch and native ACK;
- generation cancellation;
- Attack hold begin/suspend/done;
- invalid target/API failure;
- long-approach warning at low frequency;
- session end.

Production suppresses or avoids creating high-frequency diagnostics including:

- heartbeat;
- every Journal ORDER/action capture;
- every engagement interval `ATTACK_TARGET_OBSERVED`;
- every Attack transition wait sample;
- 250ms post-Attack samples;
- 1s physical exit observations;
- cold-idle diagnostic chatter;
- test-only pass/readiness markers.

Where possible the release derivative also skips the position/target-speed calculations that existed solely to format those diagnostics.

## Debug build

`release/debug/` has the same derived Controller with `DEBUG_TELEMETRY=true`. Use it only to reproduce a defect, then return to Production.

## Baseline integrity

The exact runtime-validated HF5 source/pack are stored unchanged under `runtime_validated/`. Production logging is a release derivative and must not rewrite the evidence baseline.

Before public release the production derivative needs one battle smoke test because any code derivative, even a telemetry-only one, deserves a final game load/behavior check.
