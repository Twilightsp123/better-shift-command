# Product Contract — Direct Native Shift Behavior Patch

## The user's explicit architectural requirement
**Modify WH3's own Shift logic, not replace it.** Keep original Shift/RMB input, original queue, original order objects, original head advance/retire, original Native locomotion and combat. BSC patches the native behaviors that make the original Shift inconvenient. No Lua shadow scheduler, no BSC parallel Native queue and no periodic MOVE/ATTACK reissuance.

## Required gameplay
- Shift MOVE → MOVE → MOVE should be smooth, not stop after each waypoint. Guidepoints are approximate, bounded corners acceptable, but do not erase essential route bends.
- 90°, 135°, 180°/U-turn, short legs, dense zigzags and multiple units must maintain sane geometry and no exaggerated route compression or collisions.
- Shift MOVE → ATTACK should hand off reliably without freeze, bogus brake predicates or BSC overwriting a legitimate Native ATTACK.
- MOVE → ATTACK → EXIT MOVE → ATTACK must preserve chosen target identity, minimum engagement time when relevant and native exit semantics.
- Normal RMB MOVE, normal RMB ATTACK, REPLACE and HALT must continue to work exactly as intended and cancel stale Shift tail.
- No unbounded loop/timeout that traps a queued command indefinitely; no phantom early completion or silent skip.

## Patch requirements
- First establish whether undesirable stopping comes from the engine's braking, original queue completion, next-command activation, or their combination. Don't assume an earlier queue-pop is sufficient.
- Change as little original x64 code as necessary, at proven version-guarded function(s). Prefer matching Shift/queued context and leaving ordinary RMB untouched.
- All original Native order objects and queue state stay authoritative. Do not create a second execution/controller authority in Lua or C++.
- Preserve original order IDs, lifetimes, generation/revision/cancellation and native queued tail; no artificial 'ACK means waypoint arrived' rule.
- No hardcoded tuning search: each geometry/time constant must come from an observed engine/physical model or an explicit acceptable design bound.
- Fail closed if ABI/site/build is unsupported; avoid half-installed hooks and unsafe state mutation.
- Exhaust controlled offline/Windows proof before one bounded final in-game acceptance.

## Non-goals
- Rebuild CA pathfinding, physics, formation or combat.
- Edit the game's EXE on disk as a mod installation prerequisite.
- Treat old H1–H8 Lua shadow-plan algorithms as the next development target.
- Expose MCT, modify campaign AI, or publish Steam before native patch verification.
