# Better Shift Command (BSC)

Windows x64 mod for Total War: WARHAMMER III.

**Current development direction:** reverse-engineer and directly patch WH3's **original** Shift movement, stopping, completion and attack handoff functions; keep the original input, order queue and native executor. No replacement Lua or Native command scheduler. The modification technique may use build-guarded in-memory detours, but only to change the original engine behavior, not to create another controller. This is not yet implemented.

- [Read current engineering docs](docs/current/README.md)
- [Native queue research map](docs/current/NATIVE_RESEARCH_MAP.md)
- [Phased implementation plan](docs/current/IMPLEMENTATION_PLAN.md)
- [Active risks and decisions](docs/current/RISKS_AND_DECISIONS.md)
- [Historical archive — not default reading](docs/past_doc/README.md)

Experimental source starting point: H8 commit e711e716f2411599d75184618fc1ee5cb85bcd54. Formal public Mod version v1.3.0 / Steam pack name zzz_better_shift_command_steam.pack have not been changed by this documentation work.

Source lives in source/, src/native_bridge/, tests/, maintenance_tools/ and native_maps/. Existing archive/ and runtime_evidence/ remain preserved. **Nothing on this branch represents an approved WH3 9.0.2 runtime release.**
