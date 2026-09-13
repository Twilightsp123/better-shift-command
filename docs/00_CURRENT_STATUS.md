# Project Status v30 — HF5 Runtime-Validated Controller Baseline

Date: 2026-09-13

## 1. Authoritative status

**P1/P2 Controller feature stage: COMPLETE / REAL-GAME VALIDATED.**

Current controller: `P2B-HF5 / 0.2.5`.

Latest authoritative real-game result archive: `WH3_Controller_P2B_Result_69ec469bbff5440d.zip`.

Schema-4 re-analysis of the same immutable game log records:

```text
runtime_logic_pass=true
controller_runtime_validated=true
phase1_pass=true
phase2_pass=true
attack_first_chain_pass=true
physical_disengagement_pass=true
missing=[]
failures=[]
chronology_errors=[]
```

The original schema-3 result already had `logic_pass=true`; schema 4 only separates runtime logic, visual acceptance and Bridge global provenance-release semantics, and treats user-interrupted post-Move observations as interrupted evidence rather than a functional failure.

## 2. Runtime-confirmed Controller behavior

- Move→Move predictive handoff works in game.
- Move→Attack predictive transition works in game and Attack remains a hard execution barrier.
- The player generation remains appendable after takeover; queued Shift commands extend the active shadow timeline rather than sealing it.
- `Shift Move* → Shift Attack → Shift pN` completes sampled eligible melee time and dispatches pN.
- Ordinary native `Attack T → Shift pN` is adopted without reissuing Attack, preserves engagement history, and dispatches pN after the same hold rule.
- Engagement credit requires `is_in_melee()==true` and `current_target()==intended target`; accepted Attack alone does not start the 3-second credit.
- Attack→pN native Move gets a matching Bridge ACK and real-game telemetry demonstrated substantial progress away from the target and at least one complete transition to `melee=false`.
- Ordinary RMB during Attack/Hold kills the old generation and the old pN does not revive.
- Controller-issued Move/Attack uses Bridge issue/revision bookkeeping; scripted self ACK is not re-admitted as player input.

## 3. Frozen Native Bridge baseline

Bridge version: `0.5.0-attack-native-token`.

The Bridge real-game validation closed the **experimental integration gate**. Keep these runtime facts frozen:

- verified Controller Move can be journaled as `OUR_CONTROLLER` with exact issue ID;
- stale expected revision rejects before callback/native side effects;
- ordinary player RMB remains external/UNKNOWN rather than being mislabeled as Controller;
- verified Controller Attack can be attributed under the validated experimental lane;
- journal revisions progress and u32 IDs are carried as canonical decimal strings.

### Important caveat

The Bridge archive intentionally keeps these global claims false:

```text
exact_source=false
verified_issue=false
production_release_approved=false
```

This is a **scope/proof caveat**, not a statement that the HF5 game behavior failed. v0.5.0 contains experimental-only ownership fallbacks validated under tightly scoped contracts, but it does not claim universal provenance coverage for every possible native storage/copy/interleaving path.

## 4. Production logging derivative

HF5's full telemetry was designed for research and validation. It logs per-order, per-engagement-sample, heartbeat, post-Attack and exit observations. The release-prep production derivative disables those high-frequency diagnostics while keeping low-frequency operational/error events.

The exact HF5 runtime baseline is preserved separately and is never overwritten by the logging derivative.

Before Workshop release, run one smoke battle with the production derivative:

```text
A. Shift P1 → Shift P2 → Shift Attack T → Shift pN
B. ordinary Attack T → Shift pN
C. ordinary RMB during Attack/Hold
```

No new reverse engineering is needed unless the Bridge guard preflight fails or this smoke test directly contradicts a frozen runtime fact.

## 5. Permanently revoked directions

Do not reintroduce:

- `ordered_position()` as the authoritative physical execution head;
- Move callback count/serial as one-player-gesture identity;
- `+0x98` alone as Shift/RMB semantics;
- `+0xB8` as a permanent Shift session ID;
- `RMB_OVERRIDE_LOCK` or destination-settle release;
- `NATIVE_OVERRIDE_FENCE` / fence requeue systems;
- Attack as an immutable generation terminator;
- a fixed approach timeout that cancels long-distance Attack before actual engagement;
- repeated escape Move spam as a substitute for one verified pN dispatch.

## 6. Next project phase

The technical feature stage is done. Next work is release engineering:

1. production logging smoke test;
2. final mod naming/metadata/icon and Workshop description;
3. GitHub repository publication of source, contracts, recovery manuals and tagged frozen baseline;
4. Steam Workshop publication of the production pack + required native dependencies/instructions;
5. post-release compatibility policy: on CA update, run guard preflight first; only relocate native addresses if guards fail.
