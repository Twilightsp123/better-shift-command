# Architecture — Better Shift Command v1.0.0

## Purpose

The mod keeps CA locomotion in control wherever possible, but uses a native journal to recover command semantics that the public battle Lua surface cannot reliably provide. The Controller then performs early handoffs instead of replacing CA steering with a custom locomotion system.

## Four layers

1. **CA public battle Lua** — BattleUnit position/identity, `is_in_melee()`, `current_target()`, UnitController `goto_location`, `attack_unit`, `release_control`.
2. **Reverse-engineered command semantics** — native queued/replace bit, subject identity, Move/Attack publication/consumer paths, exact revision chronology, Controller self-attribution.
3. **Native Bridge v0.5.0** — guarded Windows x64 adapter exposing a narrow Lua journal/API. Controller code does not scan arbitrary EXE memory.
4. **HF5 Controller** — persistent appendable shadow timeline, execution cursor, predictive Move/Attack transitions, engagement history, and player replacement cancellation.

## Canonical action model

A generation is appendable while it remains the same player Shift program:

```text
immutable executed prefix | mutable future suffix
[P1][P2]                  | [ATTACK T][pN][...]
```

Queued input appends. A nonqueued external order replaces/cancels the generation. `ATTACK` is an execution barrier, **not** an end-of-program marker.

## Supported runtime chains

```text
Shift P1 -> Shift P2 -> ... -> Shift Attack T -> Shift pN
ordinary Attack T -> Shift pN
```

Attack acceptance does not start the 3-second timer. Eligible model time requires `is_in_melee()==true` and `current_target()==T`. A late pN keeps already-earned eligible time.

## Safety invariants

- player ordinary RMB always wins;
- stale ACKs cannot revive cancelled generations;
- Controller self ACKs are not re-admitted as player input;
- Move lookahead cannot cross Attack;
- no repeated escape-order spam;
- no `ordered_position()` authority;
- no heuristic `+0x98 == Shift` rule.
