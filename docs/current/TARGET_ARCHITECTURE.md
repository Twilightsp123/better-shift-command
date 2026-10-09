# Target Architecture — Patch WH3's Original Shift Behavior

**Decision: modify the game's existing native Shift implementation, not replace Shift with Lua, a new Native order scheduler, or a parallel queue.** This is a reverse-engineering goal, NOT a proven working patch.

## Exactly what stays original
- The player's Shift / right-click command entry, controls and UI.
- The game's own order objects, command queue, engine sequence, queue append/replace, cancellation and queue-head ownership.
- The game's native locomotion, collision/avoidance, formation, combat, animation and target handling.
- Normal right-click / non-Shift behavior except when an independently identified shared defect must be fixed without regression.

## Exactly what BSC changes
Only the smallest set of **existing engine functions or decision predicates** that produce native Shift's undesirable behavior. Candidates require reverse-engineering proof:
1. Enqueued MOVE's terminal braking / steering / movement state update, especially before a following MOVE.
2. MOVE completion / activation of the next original order, which may be in a different function from braking.
3. MOVE → ATTACK transition and target handoff when already queued.
4. If needed, route geometry/waypoint guidance interpretation that influences stopping and cornering.

Do not assume this is one hook or only the queue-head increment. If the stop happens before the order is complete, advancing the queue may not be a sufficient or correct fix.

## Intended runtime path
Player original Shift input → **WH3 original command encoding & order queue** → WH3 original movement/attack execution with **targeted native behavior patches inside that same engine path** → original native order completion / successor execution.

**No second execution authority.** Lua must not own a canonical shadow queue, issue MOVE/ATTACK to replace engine orders, rollback a legitimate native ATTACK, or replay native queued tails. Optional Lua may expose settings or diagnostics only; aim for Native-only functionality where feasible. Native detours are a means to replace/adjust an original decision *within the same call path*, not a license to implement a second command dispatcher.

## How to implement without modifying the on-disk EXE
WH3's source is unavailable. A version-guarded WinX64 DLL may patch original function behavior in process memory, e.g. a narrow inline detour that invokes the original function with a modified native decision. This is **modifying the original engine's effective code path**, not editing the user's executable file. Exact hook, ABI, thread/lifetime ownership and guards must be proven first. If direct conditional patching is impossible, state that explicitly before deciding on a fallback.

## Native invariants
- The original order list remains authoritative before AND after the patch; verify actual Native head, queue count, engine seq, target identity and future tail.
- Each native command completes once. No BSC-specific second notion of route completion that progresses a shadow queue.
- REPLACE/HALT cancels or replaces original native commands according to WH3's own lifecycle.
- A legitimate native ATTACK can never be overridden by an unsolicited nonqueued MOVE.
- No artificial 'time passed, therefore waypoint visited' completion, no arbitrary bypass of i+1/i+2 order obligations.
- If unsupported EXE, unverified bytes, missing allocation or unsafe state, fail closed / preserve original behavior wherever safe. No partial Hook startup.

## Rejected architecture
- Current H1–H8 Lua canonical plan + Native reassert feedback loop.
- Merely porting that Lua scheduler into C++.
- An independent Native BSC queue controlling the engine's normal queue.
- Reimplementing WH3 pathfinding, steering, AI combat or formation simulation.
- Direct writes to OrderHead or raw queue slots without demonstrated engine ownership/lifetime semantics.

The next decision is NOT how fast a new scheduler should advance. It is **which original WH3 Shift functions cause the stop, corner and attack-handoff defects**, and whether their behavior can be patched locally.
