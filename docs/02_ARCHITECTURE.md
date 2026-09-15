# Architecture — Better Shift Command v1.0.1

## Purpose

The mod keeps CA pathfinding/locomotion in control and improves the timing of queued Move/Attack handoffs. A guarded Native Bridge supplies command semantics that public battle Lua does not expose reliably enough for takeover/cancellation safety.

## Five layers

1. **CA public battle Lua** — BattleUnit position/identity, `is_in_melee()`, `current_target()`, UnitController `goto_location`, `attack_unit`, `release_control`.
2. **Reverse-engineered command semantics** — native queued/replace bit, subject identity, target identity, revision chronology, publication/handler/entry paths and Controller self-attribution.
3. **Native Bridge v0.5.1** — guarded Windows x64 adapter exposing a narrow Journal/API and per-kind issue calibration.
4. **Controller 0.2.6** — appendable persistent shadow timeline, predictive Move/Attack transitions, engagement history, player replacement cancellation, accepted-native-destination authority after strong self identity closes.
5. **Self-contained Steam loader** — embeds Bridge + MinHook in PFH5 and materializes exact native bytes at battle load when missing/different.

## Canonical action model

```text
immutable executed prefix | mutable future suffix
[P1][P2]                  | [ATTACK T][pN][...]
```

Queued input appends. A nonqueued external order replaces/cancels. ATTACK is an execution barrier, not a generation terminator.

## Per-kind calibration

The v1.0.1 Bridge separates "global experimental lane has enough evidence to arm" from "this specific kind is safe to issue":

```text
MOVE issue   -> accepted_move_seen required
ATTACK issue -> accepted_attack_seen required
```

This prevents pure Move routes from depending on an unrelated prior Attack while still preventing a scripted kind from being issued before that kind has been naturally observed/accepted.

## Native Move ACK authority

Controller source/revision identity closes before geometry is trusted:

```text
OUR_CONTROLLER + issue id + unit uid + MOVE + expected revision -> ACK
```

CA may rebuild/canonicalize a destination. Finite accepted native XYZ becomes the authoritative target for subsequent tracking. Geometry difference is telemetry, not ownership identity.

## Supported runtime chains

```text
Shift P1 -> Shift P2 -> ... -> Shift Attack T -> Shift pN
ordinary Attack T -> Shift pN
pure Shift Move route without prior Attack
```

Attack acceptance does not start the 3-second timer. Eligible model time still requires `is_in_melee()==true` and `current_target()==T`.

## Safety invariants

- player ordinary replacement order always wins;
- stale ACKs cannot revive cancelled generations;
- Controller self ACKs are not re-admitted as player input;
- Move lookahead cannot cross Attack;
- scripted MOVE cannot issue before natural accepted MOVE evidence;
- scripted ATTACK cannot issue before natural accepted ATTACK evidence;
- non-finite native Move payload fails closed;
- no repeated escape-order spam;
- no `ordered_position()` authority;
- no heuristic `+0x98 == Shift` rule.
