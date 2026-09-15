# Reverse-Engineering Handoff — What Was Proven, Why Native Work Was Needed, and How to Reuse It

## 1. Layered architecture

### Layer A — CA public battle Lua

Useful public/game-facing primitives include BattleUnit identity/position, `is_in_melee()`, `current_target()`, and UnitController operations such as `goto_location`, `attack_unit`, and `release_control`.

These APIs are retained wherever they answer the question directly. HF5 uses public `is_in_melee + current_target` for **engagement eligibility**, because that is a different problem from command provenance.

### Layer B — reverse-engineered native command semantics

Native work was required for questions the public Lua surface did not reliably answer:

- whether an accepted command was queued/Shift append or replacement;
- exact per-unit revision / replacement chronology after Controller takeover;
- distinguishing Controller-issued native acceptance from external/player commands;
- retaining mixed Move/Attack chronology after Controller commands rewrite native queues;
- exact u32 IDs despite WH3's Lua 5.1 `lua_Number` being float32 in the validated build.

### Layer C — Native Bridge v0.5.0

The Bridge converts the recovered native facts into a narrow journal/API. Controller code consumes the journal rather than reading arbitrary EXE memory directly.

### Layer D — Lua Controller HF5

The Controller owns a persistent appendable shadow action timeline, an execution cursor, predictive Move/Attack transitions, engagement history and player-replacement cancellation.

## 2. Why public callbacks/queries alone were insufficient

### Move callback is not one player gesture

Runtime history showed Shift drawing can produce an N+1 callback pattern: P0/origin has no native target slot while P1..PN correspond to actual queued targets. Large callback bursts therefore cannot serve as one-gesture identity.

### `ordered_position()` is not the physical execution head

It was observed to sweep rapidly over future queued path points while the unit could not physically have reached them. Using it as route progress caused virtual advancement and destroyed predictive handoff behavior.

### post-callback replace pulses are transient

Native `is_queued==0` really does choose replace/clear semantics, but the associated pulse can be cleared by native update before Lua CommandEvent dispatch. Therefore callback-time pulse polling cannot be the sole cancellation authority.

### current selection is not command recipient identity

Per-unit native mutation established reliable subject attribution in prior runtime work; current UI selection timing is not authoritative.

### exact u32 identity needs strings

Validated WH3 Lua reports `Lua 5.1` with 4-byte `lua_Number`. Values above 2^24 cannot all be represented exactly as numbers. Bridge u32 IDs/revisions/serials are therefore canonical decimal strings.

## 3. Reverse-engineered command facts retained as contracts

### Queued/replace semantic

Native queued boolean is the real semantic switch:

```text
is_queued == 0 → clear/replace
is_queued != 0 → append/Shift
```

Move constructor old location `0x142D6DA64` stored `is_queued` at `cmd+0xA8`; Attack constructor `0x142D6D2C0` stored it at `cmd+0x99`.

### Subject vector

Old shared constructor `0x142C68624` established singleton subject layout:

```text
cmd+0x10 count
cmd+0x14 capacity
cmd+0x18 pointer array
```

### Attack target

The producer Attack command stores target BattleUnit root at `command+0x88`; Bridge v0.5.0's experimental Attack-token fallback additionally checks exact recipient root, queued bit, target root and target global UID before binding a pending Controller issue.

### HandlerScope consumer authority

Move/Attack packet handlers (`0x142D95F8C`, `0x142D95A50` in the validated executable) are the synchronous envelope used for physical provenance. The generic selection parser is diagnostic only.

### Historical tactical order ring facts

Earlier runtime work identified the per-unit tactical ring used to understand Move/Attack chronology:

```text
unit wrapper -> [wrapper+0x08] = battle unit root
slots base = root+0x0288
slot stride = 0x120
capacity = 40
count/read/write = root+0x2F88/+0x2F8C/+0x2F90
slot+0x20 = sequence (0 is valid)
MOVE destination geometry = slot+0x58/+0x5C/+0x60
runtime-confirmed Attack target path used target root and global UID root+0x3EA0
```

These facts are useful recovery evidence but HF5 release control should prefer the Bridge journal rather than rebuilding direct Lua memory readers.

## 4. Controller semantics built on those facts

### Persistent appendable generation

A queued Shift action extends the current generation even after takeover. An Attack is a hard **execution barrier**, never an immutable end-of-program marker.

Executed prefix is immutable; future suffix remains appendable.

### Player replacement

A nonqueued external Move replaces/cancels the old generation. Old ACKs or later stale actions may not revive it.

### Attack hold

Attack acceptance is not engagement. Eligible model time requires:

```text
is_in_melee()==true
AND current_target()==intended target
```

Only adjacent eligible observations within the observation-gap limit are credited. If pN appears late, previously accumulated eligible time is retained.

### Attack-first

Ordinary player Attack is adopted rather than reissued. It starts engagement history, remains appendable, and a later Shift pN uses the same hold/exit logic.

## 5. Revoked hypotheses and why

- `+0x98 == Shift/RMB`: false; it is a movement-record discriminator/width-related field, not gesture semantics.
- `ordered_position == current physical destination`: false in queued paths.
- Move callback serial == player gesture generation: false; callbacks burst for compiled path vertices.
- RMB_OVERRIDE_LOCK / NATIVE_OVERRIDE_FENCE: false architecture; ignoring records does not cancel CA's native queue and can permanently disable the controller.
- Attack seen == program complete: false; later queued pN can arrive in Journal long after Attack becomes visible.
- fixed 30-second Attack approach timeout: false behavior policy; long-distance pursuit can legitimately exceed it before first eligible melee.

## 6. Bridge proof boundary

v0.5.0 has real-game evidence sufficient for this Controller, but its global flags intentionally remain conservative. Experimental ownership fallback does not distinguish every theoretically identical interleaving in all possible native paths. Do not rewrite documentation to claim universal exact-source proof.

## 7. How another developer should reuse this work

1. Do not build a new heuristic Shift detector.
2. Use the existing Bridge API/journal and decimal-string IDs.
3. Keep the HF5 shadow timeline/generation rules.
4. If CA updates the executable, relocate the documented native roles using `ADDRESS_RELOCATION_PLAYBOOK.md` and re-run the narrow Bridge gate.
5. Only reopen broad reverse engineering when a specific frozen contract is contradicted.
---

## 2026-09-15 release-layer update (v1.0.1)

The reverse-engineered hook/address contract remains the v0.5.0-era guarded contract. v0.5.1 did **not** redo the native address map. It changes issue calibration policy only: MOVE and ATTACK require their own natural accepted-kind evidence instead of forcing both kinds before every scripted issue.

Controller 0.2.6 also stops using 0.05 m exact destination equality as a second source/provenance authority after Bridge issue/source/revision identity has already matched. CA's accepted finite native Move destination is treated as canonical for tracking.

For deployment/build details see `../deployment/STEAM_SELF_CONTAINED.md` and `../../tools/release_v1.0.1/`.
