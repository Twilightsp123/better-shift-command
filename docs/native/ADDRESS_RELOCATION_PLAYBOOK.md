# Native Address Relocation Playbook — CA Update Recovery

This document exists so a major CA update means **relocating known semantics**, not repeating the original reverse engineering.

## 1. Validated executable baseline

Historical validated image base: `0x140000000`.

Validated executable SHA256:

```text
b7315fa718fd84e2e018e2c4df06600e9df0076156b474f148d9d558c939aa55
```

The Bridge does not rely on the whole-file hash alone. The Windows backend byte-locks 16 entry points. A guard mismatch is a hard stop.

## 2. Frozen 16-hook map

| Name | Old RVA | Old VA | Semantic role | Old guard bytes |
|---|---:|---:|---|---|
| move | `0x02EF9FF4` | `0x142EF9FF4` | native per-unit Move entry | `488bc4488958104889701848897820554154415541564157488da888feffff48` |
| attack | `0x02EF838C` | `0x142EF838C` | native per-unit Attack entry | `488bc448895808488968104889701857415641574883ec30498b18488bf1488b` |
| allocator | `0x02E18F54` | `0x142E18F54` | order slot allocator / queued clear-vs-append path | `48895c240855488d6c24c04881ec40010000488bd984d2752083b9102d000000` |
| halt | `0x02EE1478` | `0x142EE1478` | native Halt entry | `48895c24084889742410574883ec20488bf18ada4881c188020000e84816f2ff` |
| lua_move | `0x02D9C620` | `0x142D9C620` | Lua/common Move command path | `488bc44889580848897018488978205541564157488d68d84881ec1001000048` |
| lua_attack | `0x02D9BEB8` | `0x142D9BEB8` | Lua/common Attack command path | `48895c240848896c2410488974241857415641574881ecd0000000458af8488b` |
| publish_move | `0x01C8FD4C` | `0x141C8FD4C` | Move publication wrapper | `48895c2418574883ec408b0510cc2602488bd9488d4c245089442450488bfae8` |
| publish_attack | `0x02CBA778` | `0x142CBA778` | Attack publication wrapper | `48895c2418574883ec408b05b8202401488bd9488d4c245089442450488bfae8` |
| writer_begin | `0x01B432C4` | `0x141B432C4` | BCQ writer begin / packet span lineage | `48895c24084c8bda488bd94c89590833d2668911418b8300500000894110418b` |
| writer_finalize | `0x01B46624` | `0x141B46624` | BCQ writer finalize / packet length commit | `8039004c8bc9753180790100752b488b51088b4114440fb7820050000066442b` |
| buffer_copy | `0x01B247FC` | `0x141B247FC` | buffer copy path (not reader bounds checker) | `488bc44889581048897018574883ec20488bfa4c8d40088b920050000033db88` |
| stage_copy | `0x01B2600C` | `0x141B2600C` | staging/copy path (not cursor authority) | `48895c24084889742410574883ec20488bd98bf2488b4918498bf8e858330000` |
| move_handler | `0x02D95F8C` | `0x142D95F8C` | synchronous BCQ Move packet handler / HandlerScope authority | `48895c241048897c242055488d6c24a94881ec00010000488bfa488bd9488bd1` |
| attack_handler | `0x02D95A50` | `0x142D95A50` | synchronous BCQ Attack packet handler / HandlerScope authority | `488bc448895810555657488d68a84881ec40010000488bf20f2970d8488bd148` |
| selection_reader | `0x02DCAF24` | `0x142DCAF24` | selection parser; diagnostic only, not provenance authority | `40555356574157488d6c24c94881ecc00000004533ff4c8d456f488bda44897d` |
| free_memory | `0x004EC5C0` | `0x1404EC5C0` | native memory release hook for lineage invalidation | `4883ec584885c90f8412010000f605bc1a910302` |

The mapping order in `src/platform_windows.cpp` is the same as the detour array: Move, Attack, allocator, Halt, Lua Move, Lua Attack, publish Move, publish Attack, writer begin/finalize, copy/stage, Move/Attack handlers, diagnostic selection parser, free.

## 3. Structural anchors that survive address drift

Do not search only for old absolute addresses. Re-establish each semantic role:

### Command metadata

`0x142C68624` old VA was the shared command selection constructor. It proved:

```text
cmd+0x10 = subject count
cmd+0x14 = subject capacity
cmd+0x18 = subject pointer array
```

Old Move constructor `0x142D6DA64` proved:

```text
cmd+0xA8 = is_queued
cmd+0xA9 = fast
```

Old Attack constructor `0x142D6D2C0` proved:

```text
cmd+0x99 = is_queued
cmd+0x88 = target BattleUnit root
```

**Warning:** `command_object+0x88` here is an Attack target field. It is unrelated to the historically revoked claim that `battle_unit_root+0x88` was a generic Attack queue pointer.

### Consumer packet authority

Old synchronous handlers:

```text
Move   0x142D95F8C
Attack 0x142D95A50
```

At handler entry the Bridge reconstructs an exact physical packet interval from reader state and creates a thread-local HandlerScope lasting exactly through that handler call. The generic selection parser `0x142DCAF24` is diagnostic only and must not be promoted back to provenance authority.

Reader structural fields used by the recovered contract:

```text
reader+0x08 = error byte
reader+0x10 = data base
reader+0x18 = length/bound component
reader+0x1C = start/bound component
reader+0x20 = cursor
```

Primitive reader old VA `0x141B2479C` established the cursor/data/bounds relationship. The fixed packet header length is 7 bytes.

### Writer / physical lineage

Writer buffer is inline at `queue+8`, not a pointer loaded from `[queue+8]`. The writer cursor lives at `buffer+0x5000`. Finalize backfills a u16 packet length. Exact spans, copies and staging operations are tracked by sidecar lineage; content/time/FIFO matching is intentionally not used as provenance.

## 4. Relocation procedure after a CA update

1. **Archive the new `Warhammer3.exe` hash and PE metadata.** Never overwrite the old evidence.
2. Run the old 16 guards. Record exactly which roles mismatch.
3. For each mismatch, search the new executable using the old prologue bytes as a first hint only. If exact bytes moved unchanged, verify callers/callees before accepting the new RVA.
4. If optimization changed the bytes, recover by semantic neighborhood:
   - Lua/common Move/Attack path → command constructor → publisher;
   - publisher → writer begin/finalize → copy/stage;
   - BCQ Move/Attack handler → shared parser → downstream native Move/Attack;
   - allocator branch that uses the queued boolean to clear vs append.
5. Re-prove the field offsets listed in section 3. Do not assume offsets survived just because the function was found.
6. Capture new first-byte guards and update only `src/platform_windows.cpp` plus corresponding evidence/profile files.
7. Rebuild Bridge. Run offline C++/Lua/Python fixtures.
8. Run a **single controlled real-game Bridge validation** requiring:

```text
CAL_MOVE_ACCEPTED
CAL_ATTACK_ACCEPTED
EXPERIMENTAL_ARM_PASS
verified MOVE -> OUR_CONTROLLER + exact issue
stale revision -> rejected before callback/native side effect
ordinary player RMB -> external/UNKNOWN
verified ATTACK -> OUR_CONTROLLER + exact issue
VALIDATION_PASS
```

9. Only after Bridge validation passes, run the three Controller smoke cases in `COLD_START_RECOVERY.md`.

## 5. Stop conditions

Do not broaden reverse engineering if the known semantic chain can be relocated and the controlled Bridge validation passes. Do not change Controller geometry merely because native RVAs moved.

If the data layout itself changed, document the new relation and retain both old and new layouts by game version/hash.

## 6. Historical traps

These labels/addresses were corrected during development and must not be blindly restored:

- `0x141B247FC` is a buffer copy path, not the reader bounds checker.
- `0x141B2600C` is staging/copy, not authoritative cursor advance.
- `0x142DCAF24` generic selection parsing is not provenance authority.
- callback-time replace pulse is too transient to be the Lua cancel authority.
- direct `inner_root+0x1DB0` Attack queue reads were contradicted in runtime history.
