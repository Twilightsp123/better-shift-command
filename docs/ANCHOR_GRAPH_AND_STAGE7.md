# Anchor Graph and Stage-7 Reverse Engineering

## Why the anchor graph exists

Raw byte signatures are excellent for unchanged code but weak for highly
repeated wrappers and codegen drift. The BSC anchor graph treats addresses as a
small related system rather than sixteen unrelated constants.

Examples in the current graph:

- `move -> allocator`
- `attack -> allocator`
- `lua_move -> publish_move`
- `lua_attack -> publish_attack`
- `move_handler -> selection`
- `attack_handler -> selection`
- Move/Attack, Lua Move/Attack, and handler family delta relationships
- the paired RIP-relative publication globals

On WH3 9.0.2, the normalized publication prologue occurs 481 times. The graph
first uses the Lua ingress call edges to collapse those repeated wrappers, then
cross-checks the paired RIP targets. Regional address shift is not a release
proof.

## Evidence hierarchy

1. exact unique guard;
2. normalized unique guard;
3. hard anchor-graph constraints;
4. constructor/VTable dataflow;
5. Ghidra exact disassembly/callgraph evidence for unresolved cases;
6. optional BinDiff old/new function matching when a baseline executable exists;
7. Windows build/CTest and WH3 runtime smoke before promotion.

No Stage-6/7 result writes production addresses into the runtime automatically.

## Resolution gate

If a site starts ambiguous, a single hard edge is insufficient for automatic
Stage-6 resolution. The fixed-point result must leave one RVA and that RVA must
be supported by at least two independent hard relationships. Regional shift is
never counted as hard support.

## Stage-7 roles

Ghidra Headless is the exact-disassembly fallback for the current executable.
It validates function boundaries, callers/callees, exact callsites and basic-block
shape, and its evidence is SHA-bound to the Stage-7 bundle. BinDiff is a separate,
optional cross-build matcher that requires an old executable or old BinExport.
A BinDiff match is only a candidate source; it must be rechecked with Ghidra/static
relationships and the normal build/runtime gates before promotion.
