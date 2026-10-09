# Product Contract — BSC Native Queue Redesign

## Why BSC exists
Warhammer III native Shift queue produces undesirable stops, handoff behavior and route deviations. BSC's job is to improve *real in-game movement* while retaining predictable player control; not merely make Lua telemetry report compliant route steps.

## Required behaviors
- Shift MOVE → MOVE → MOVE: continuous motion through **approximately guiding** intermediate points. Bounded rounded corners are allowed. Avoid stops at every marker and visibly unnatural detours; do not silently delete a major planned turn.
- 90/135/180-degree turns, short route legs, reversals, multi-unit routes and queue revisions must have defined semantics and no double-commit or compression into mutually colliding movements.
- MOVE → ATTACK: next attack must execute promptly when valid transition conditions are met, without the Controller cancelling the game's own correct attack or waiting forever for a particular deceleration curve.
- MOVE → ATTACK → EXIT MOVE → ATTACK: target identity, minimum engagement hold (existing default 3 seconds) and EXIT route obligations remain intact.
- Non-Shift RMB REPLACE/HALT and new player orders take precedence over old BSC generations. No stale Lua plan may resurrect cancelled commands.
- Never counterfeit exact order identity using current_target, animation state, ACK alone or guessed VTables; never skip canonical i+1 merely because native execution appears to be i+2.
- Route fidelity is a requirement on **geometry / obligation**, not absolute point-centre arrival. Guidance accepted != actual waypoint visited, and neither is established by issue/ACK alone.
- No infinite rollback ↔ reassert loop, silent Native queued-tail deletion, process hang or partial-hook start.

## Engineering requirements
- Avoid empirical threshold tuning as a substitute for architecture. New distance/time values need a physical model or independently justified bounds.
- Every new RE claim requires build-specific static proof and evidence grade.
- A single component must own the *permission to advance* each active order. The engine still owns locomotion, avoidance, physics, attack execution and animation.
- Build-specific binary compatibility is fail-closed: exact EXE SHA, byte guards, v142/MASM builds and CTest before any game-facing candidate.
- No endless human test loop: exhaust deterministic fixtures and Windows isolated tests first. WH3 testing is a bounded final acceptance gate, not the default debugging instrument.

## Explicit non-goals
- Do not replace CA's unit pathfinding, steering/physics, attack simulation or formation movement.
- Do not ship a permissive 'let any queued future execute' fallback.
- Do not enable quarantined Entity/Component/Alive/ContactPair research to gain authority.
- Do not repurpose the public Steam pack identity to name provisional NQTR experiments.
