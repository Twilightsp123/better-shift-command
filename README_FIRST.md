# READ THIS FIRST — Better Shift Command Native Queue Redesign

This documentation branch is **architecture-only**. The goal has changed: determine how to modify the original WH3 Shift order queue's completion/advance semantics instead of maintaining two competing Lua/Native command queues.

**Authoritative reading starts at [docs/current/README.md](docs/current/README.md).** Only the files linked there are current NQTR maintenance directions. For the actual work breakdown, read [docs/current/IMPLEMENTATION_PLAN.md](docs/current/IMPLEMENTATION_PLAN.md).

Baseline frozen: maintenance/t2move-h8-terminal-liveness-static @ e711e716f2411599d75184618fc1ee5cb85bcd54. Formal published Mod version remains v1.3.0; public Steam pack identity remains zzz_better_shift_command_steam.pack. NQTR is **not** built, merged, released or WH3-validated.

Old 2026-09 architecture, MCT/T1/T2 experiments, 9.0.1 build map, H1–H8 experimental designs and old long reading rules now live in [docs/past_doc/README.md](docs/past_doc/README.md) and are **not required reading**. Historical bytes and tests are preserved for targeted evidence lookup.

Before coding, see the single-authority model, unknown native queue-advance hook, P0 MinHook status9 problem and explicit no-guess rules in the current docs. Do not demand repeated WH3 testing while these remain unresolved.
