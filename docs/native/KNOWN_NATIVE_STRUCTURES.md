# Known Native Structures and Semantic Anchors

This file is a recovery map, not a promise that offsets survive future CA builds.

## Lua BattleUnit root

Historical runtime contract:

```text
BattleUnit userdata
 -> wrapper pointer
 -> [wrapper+0x08] = battle unit root
```

## Tactical order ring (historical recovery evidence)

```text
slots base          = root + 0x0288
slot stride         = 0x120
capacity            = 40
count/read/write    = root + 0x2F88 / +0x2F8C / +0x2F90
slot+0x20           = sequence (0 is valid)
Move XYZ            = slot+0x58/+0x5C/+0x60
formation/width     = slot+0x98 (auxiliary, NOT Shift semantics)
target global UID   = target_root+0x3EA0 (validated historical contract)
```

HF5 production control should use the Bridge journal rather than rebuilding direct Lua memory readers. These offsets exist primarily to help recover the native system if the Bridge must be relocated.

## Producer command layouts

Shared subject vector (old constructor `0x142C68624`):

```text
cmd+0x10 = subject count
cmd+0x14 = subject capacity
cmd+0x18 = subject pointer array
```

Move constructor (old `0x142D6DA64`):

```text
cmd+0xA8 = is_queued
cmd+0xA9 = fast
```

Attack constructor (old `0x142D6D2C0`):

```text
cmd+0x88 = target BattleUnit root
cmd+0x99 = is_queued
```

Do not confuse `command+0x88` with the revoked historical claim that `battle_unit_root+0x88` was a generic Attack queue.

## BCQ reader/writer lineage

Reader fields recovered for the validated build:

```text
reader+0x08 = error byte
reader+0x10 = data base
reader+0x18 = length/bound component
reader+0x1C = start/bound component
reader+0x20 = cursor
```

Writer buffer is inline at `queue+8`; writer cursor is at `buffer+0x5000`. Finalize backfills a u16 packet length. Physical lineage is tracked by exact spans/copies, not payload/time/FIFO guesses.

## Native semantic switch

```text
is_queued == 0 -> clear / replace
is_queued != 0 -> append / Shift
```

This was recovered from executable control flow and runtime correlation. It replaces older heuristic interpretations of movement-record fields.
