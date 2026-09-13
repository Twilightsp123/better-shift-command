# Runtime Validation Index

Start with `validation/HF5_RUNTIME_VALIDATION.md` for the current release baseline.

Bridge validation source material is under `native/original_bridge_contracts/` and the frozen source tree. HF5 schema-4 evidence is under `validation/runtime_validated_HF5/`.

Evidence hierarchy:

1. controlled real-game result/log;
2. Bridge guard/preflight and runtime ACK facts;
3. offline Lua/C++/Python regression fixtures;
4. static reverse-engineering findings.

Do not promote a static inference over contradictory runtime evidence.
