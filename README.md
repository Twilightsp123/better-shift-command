# Better Shift Command (BSC)

Windows x64 mod for Total War: WARHAMMER III.

**Current development direction:** research and redesign the native Shift order queue transition/completion mechanism to avoid competing Lua/Native command ownership. This is a proposed next architecture, not an existing native patch.

- [Read current engineering docs](docs/current/README.md)
- [Native queue research map](docs/current/NATIVE_RESEARCH_MAP.md)
- [Phased implementation plan](docs/current/IMPLEMENTATION_PLAN.md)
- [Active risks and decisions](docs/current/RISKS_AND_DECISIONS.md)
- [Historical archive — not default reading](docs/past_doc/README.md)

Experimental source starting point: H8 commit e711e716f2411599d75184618fc1ee5cb85bcd54. Formal public Mod version v1.3.0 / Steam pack name zzz_better_shift_command_steam.pack have not been changed by this documentation work.

Source lives in source/, src/native_bridge/, tests/, maintenance_tools/ and native_maps/. Existing archive/ and runtime_evidence/ remain preserved. **Nothing on this branch represents an approved WH3 9.0.2 runtime release.**
