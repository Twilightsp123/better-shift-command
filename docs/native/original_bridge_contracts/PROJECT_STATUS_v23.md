# WH3 Native Bridge — Project Status v23

Date: 2026-09-13
Current candidate: `0.5.0-attack-native-token`

## Status change

**Native Bridge experimental integration gate: CLOSED / REAL-GAME VALIDATED.**

The one-game v0.5.0 runtime validation passed every required marker. The bridge is now sufficient to begin the actual Shift-smoothing / mixed-action Controller layer without reopening broad native semantic probing.

## Runtime PASS evidence

Authoritative order from `script_log_120926_2359.txt`:

```text
CAL_MOVE_ACCEPTED revision=1
CAL_ATTACK_ACCEPTED revision=2
CAL_ATTACK_CLEAR_PASS revision=3
EXPERIMENTAL_ARM_PASS
VERIFIED_MOVE_PENDING issue_id=1 expected_revision=3
MOVE source=OUR_CONTROLLER issue=1 revision=4
OWN_MOVE_PASS
STALE_GATE_PASS old_revision=3 callback_invoked=false
PLAYER_RMB_PASS source=UNKNOWN revision=5
VERIFIED_ATTACK_PENDING issue_id=2 expected_revision=5
ATTACK source=OUR_CONTROLLER issue=2 revision=6
OWN_ATTACK_PASS
VALIDATION_PASS
```

`VALIDATION_RESULT.json` has `validation_pass=true`, all required markers true, and no fail lines.

Candidate runtime facts:

- version: `0.5.0-attack-native-token`
- source digest: `51fc8e51dd4d4b22d2ae8d704f66a92b459f84e1aa735e8c740f1672f41ff11c`
- experimental issue build: true
- Windows build: PASS
- Windows private-process smoke: PASS
- EXE preflight: PASS
- native byte guards: 16
- runtime DLL SHA256: `238cde4548f5bffc3e25962da04dd65baa2cdff5365f0a237dc21213054f075c`

Rollback also passed: `ROLLBACK_RESULT.json` records `state=ROLLED_BACK`, restoring the pre-validation baseline.

Evidence directory: `evidence/runtime_v050_pass/`.

## What is now frozen

Do not reopen or casually modify these paths while building the Controller:

1. verified MOVE ownership path;
2. expected-revision stale rejection before callback/native side effects;
3. player ordinary RMB remaining external/`UNKNOWN` rather than `OUR_CONTROLLER`;
4. verified ATTACK ownership path;
5. v0.5.0 experimental calibration and arm logic;
6. journal revision progression and decimal-string ID ABI.

Any future Controller bug must first be treated as a Controller-layer issue unless new evidence directly contradicts one of these runtime facts.

## Release caveat

This closes the **experimental integration gate**, not the production-release gate.

The following global claims remain intentionally false:

```text
exact_source=false
verified_issue=false
production_release_approved=false
```

Reason: v0.5.0 contains experimental-only ownership fallbacks used under tightly scoped validation contracts. They are sufficient for Controller development and runtime experimentation, but are not represented as a universal production provenance proof.

## Next phase — Controller implementation

The next milestone is no longer Native Bridge research. It is the actual mixed-action Controller.

Implementation order is frozen as follows:

1. Restore the proven v6.5 physical Move handoff kernel.
2. Build a canonical Lua-owned Shadow Action Timeline from accepted native MOVE/ATTACK actions.
3. Enforce ATTACK as a hard semantic barrier: Move lookahead may never cross it.
4. Implement MOVE -> ATTACK dispatch only near the current Move endpoint; do not use Move→Move predictive lead across the barrier.
5. Implement ATTACK hold semantics, distinguishing attack-order acceptance from actual engagement when possible.
6. Dispatch Controller MOVE/ATTACK only through the verified Native Bridge issue API.
7. On any external/player replacement order, kill the old scripted generation immediately using revision change / external accepted order evidence.
8. Integrate the final Shift route example: `Move A -> Move B -> Attack Enemy -> hold -> Move C`.
9. Run one focused end-to-end runtime validation of the Controller; do not reopen broad bridge probes unless the bridge contract itself is contradicted.

## Controller acceptance invariants

The Controller is not complete until all of these hold:

- smooth Move→Move handoff matches the v6.5 baseline;
- ATTACK is never skipped by lookahead, proximity promotion, stall bypass, or predictive takeover;
- Attack hold does not begin merely because the ATTACK order was accepted if the unit has not actually engaged;
- an intervening unrelated enemy contact cannot falsely count as engagement with the intended target when target identity can be checked;
- ordinary player RMB supersedes the stale scripted plan immediately;
- Shift append extends the current player generation instead of replacing it;
- no stale scripted action can revive after a player replacement;
- all controller-issued native orders use exact issue/revision bookkeeping from the bridge;
- no coordinate/time/FIFO self-echo heuristic is introduced.
