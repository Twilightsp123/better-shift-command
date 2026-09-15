# Runtime Validation Index

## Current release baseline

Start with [`validation/V1.0.1_RUNTIME_VALIDATION.md`](validation/V1.0.1_RUNTIME_VALIDATION.md).

v1.0.1 release validation specifically covers:

- v142-built Bridge v0.5.1 installs native hooks in game;
- pure Shift MOVE arms with `accepted_attack=false`;
- long/multi-unit Move routes survive beyond the old 5 cm payload hard-fail;
- predictive ATTACK still issues/ACKs after the calibration change.

## Historical feature baseline

[`validation/HF5_RUNTIME_VALIDATION.md`](validation/HF5_RUNTIME_VALIDATION.md) remains authoritative for the original full P1/P2 feature validation: Move handoff, Move->Attack, Attack-first adoption, engagement hold/disengagement, APPEND and player override safety.

Bridge v0.5.0 validation source material remains under `native/original_bridge_contracts/` and `validation/runtime_validated_HF5/`.

## Evidence hierarchy

1. controlled real-game result/log;
2. Bridge guard/preflight and runtime ACK facts;
3. offline Lua/C++/Python regression fixtures;
4. static reverse-engineering findings.

Do not promote a static inference over contradictory runtime evidence.
