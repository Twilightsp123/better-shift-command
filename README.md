# Better Shift Command (BSC)

A Windows x64 Total War: WARHAMMER III mod project.

**Current research target:** user-supplied WH3 9.0.3-labelled EXE, SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` (game version label not independently verified from VERSIONINFO). **No authorized new Native gameplay patch yet.**

## What BSC actually fixes

**Vanilla Shift MOVE → MOVE:** soldier models **within the same unit card** reach and turn at queued route points asynchronously, so their headings diverge and they crowd/jostle against one another. The defect is **formation and per-model movement coherence**, NOT a proven native full-stop at each intermediate MOVE waypoint.

**MOVE → ATTACK pause in old BSC:** the conspicuous stop/rollback came from the past Lua Controller conflicting with native ATTACK. That is a **BSC regression**, not evidence that unmodified WH3's attack transition needs patching.

**Architecture:** reverse-engineer and minimally patch the original WH3 native formation/waypoint behavior. WH3 still owns the original queue, per-soldier movement/steering/collision, and ATTACK. No replacement Lua/Native command scheduler, no repeated reissue or OrderHead modification. A DLL may implement verified narrow in-process patches in future.

## Current documents

- [Product diagnosis correction — read first](docs/current/PRODUCT_CAUSE_CORRECTION_20261010.md)
- [Product contract and acceptance](docs/current/PRODUCT_CONTRACT.md)
- [WH3 9.0.3 formation-native architecture](docs/current/WH3_9_0_3_NATIVE_PATCH_DESIGN.md)
- [N1 reverse-engineering research map](docs/current/NATIVE_RESEARCH_MAP.md)
- [Corrected stage plan](docs/current/IMPLEMENTATION_PLAN.md)
- [All current docs](docs/current/README.md)
- [Read-only N1 PE/disassembly proof tools](maintenance_tools/native_shift_re/README.md)
- [Historical documents (not current design authority)](docs/past_doc/README.md)

The old H8 code baseline is `e711e716f2411599d75184618fc1ee5cb85bcd54`; formal public version v1.3.0 and Steam pack name `zzz_better_shift_command_steam.pack` are unchanged by this research branch.

Previous exact-file N1 findings concerning native queue pop, MOVE task/state transfer, route validation and geometry remain static engine evidence, **not proof that the unit-card's soldier crowding comes from stopping or braking**. No new DLL, PACK, Windows runtime validation or WH3 gameplay success is claimed.
