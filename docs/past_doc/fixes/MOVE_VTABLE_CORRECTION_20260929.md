# Move VTable Correction — 2026-09-29

## Root cause

The locked WH3 EXE (`6c104a63...3297`) was re-audited from top-level `Order::issue_move` / `Order::issue_attack` through allocator return, exact slot, constructor, VTable, sequence and payload.

The original RC8 current-state map conflated two sibling Move constructors:

- Full/player/top-level Move constructor `0x0300B094` -> VTable `0x03910AA8`.
- Simple/Intercept Move constructor `0x0300B038` -> VTable `0x0390E248`.

BSC hooks top-level Move at `0x030344D4`, so its outcome slot carries `0x03910AA8`. Original RC8 expected `0x0390E248`, causing normal Move outcomes to be downgraded to partial/no-sequence evidence and eventually causing owned Move fail-closed shutdown.

The allocator hypothesis from experimental R1/R2/R3 was wrong: direct machine code proves allocator `0x02F5248C` returns exact `slot_base` in RAX. The original `f.slot = allocator_return` design is retained.

## Core changes

1. `BridgeHost::outcome()` expects Full Move VTable `0x03910AA8`.
2. `EvidenceProbe::active_order()` (the CorePath execution-identity portion) recognizes Full Move VTable `0x03910AA8`, restoring SC6 exact Move identity.
3. Core synthetic fixtures model the real Full Move constructor instead of the Simple/Intercept sibling.
4. A regression injects the historical wrong `0x0390E248` into a top-level Move slot and proves it cannot count as successful Move calibration.
5. Per-kind calibration is hardened: only a complete accepted outcome with an engine sequence sets `accepted_move_seen` / `accepted_attack_seen`.
6. Native/Lua bridge version is bumped to `1.0.17-corepath-wh3-6c104-movevtfix` so an old DLL cannot silently satisfy the new Controller.

## Explicit non-changes

- 16 mandatory hook RVAs/guards unchanged.
- SC1-SC6 gameplay logic unchanged.
- Lua canonical queue logic unchanged except bridge version lock.
- Attack VTable remains `0x03910228`.
- Physical Entity/Component/Alive/ContactPair remains QUARANTINED.
- Smart Guard remains STAGED_DISABLED.
- No allocator-index resolver, container scan or constructor-witness hook is used.

## ACCEPTED_NO_SLOT caveat

The supplied static report claims accepted single-unit orders always receive a sequence, but the same Move/Attack reports show the queued-count `>=40` branch targeting an address later identified as `AL=1`. This contradiction is retained as an unresolved static-report caveat. The historical `ACCEPTED_NO_SLOT` contract is therefore kept fail-safe and is not removed by this fix.
