# Native Shift Patch — Implementation Plan (original engine behavior, no replacement)

**Scope correction 2026-10-09:** the task is to patch existing WH3 Shift behavior directly. The former "Native queue transition owner" / alternative single-writer scheduling proposal is REJECTED. Working branch retains its historical NQTR label but this document is authoritative for **direct original-engine modification**. H8 baseline: e711e716f2411599d75184618fc1ee5cb85bcd54. Documentation-only stage; no Native patch implemented.

## Stage 0 — Freeze existing work and align docs (NOW)
**Work:** archive 59 old doc blobs without editing them; collect the actual user requirements and WH3 12:10, 12:53, 13:18 failure evidence, SHA/build/ABI, H8 test baseline and previous false assumptions. Make direct-native-patch goal explicit in all current docs; preserve all Lua/Native source unmodified.
**Pass:** docs archive byte-identical, new docs single reading entry, checked by CI, no changed game behavior.

## Stage 1 — Reverse the original Shift execution path (critical path)
**Questions, in this order:**
1. Where does Shift queueing choose append vs REPLACE and which original object stores MOVE/ATTACK?
2. What original native movement/steering function causes speed loss near a queued MOVE destination? Is the stop due to native braking, arrival mode, waypoint representation, command transition, or interaction between these?
3. Where is MOVE judged complete, where does OrderHead actually change, and how is the next original MOVE or ATTACK activated? Are those separate call sites?
4. Where is target validation and queued MOVE→ATTACK handoff performed? Is stalled attack from original WH3 or was it introduced by H8's Lua second writer?
5. What is the threading/lifetime context, and which branches are restricted to queued Shift commands vs shared with ordinary RMB?

**Method:** static x64 callgraph/dataflow on target WH3 9.0.2 EXE, current candidate map and VTables; compare already-known Native Bridge hook sites. Produce annotated function signatures, RVAs/bytes/guards, proof grade, disassembly, alternate interpretations, state diagram and an explicit *cause→candidate patch site* table. No guessing that OrderHead increment alone is the solution.
**Pass:** each planned change has a specific original WH3 decision path and an independently checkable relationship to the undesirable behavior. If evidence cannot establish one, mark BLOCKED rather than fabricate an address.

## Stage 2 — Establish minimal original-code patch contract
**Work:** for each proven site define the smallest in-place behavioral delta: e.g. avoid unnecessary terminal braking before valid queued next MOVE, alter the native completion predicate for a guide corner, or preserve correct activation of native queued ATTACK. Preserve original queue storage, order lifetime, native sequence, engine execution and user REPLACE.
**Pass:** old-vs-patched state transition table, preconditions and fail-closed fallback for exactly the same original engine order objects; no new BSC queue, canonical Lua state or independent command issuing API.
**No-go:** arbitrary distance/time tuning or rewriting movement/navigation algorithms.

## Stage 3 — Deterministic offline differential proofs
**Work:** construct short original-native order traces and a patch-site model from Stage 1 evidence, not an invented independent scheduler. Compare unpatched vs targeted patched engine decision for MOVE→MOVE (straight, 90°, 135°, 180°, U-turn, short zigzags), MOVE→ATTACK, ATTACK→EXIT→ATTACK, REPLACE, i+1/i+2, target death and multi-unit.
**Pass:** only the intended branch decisions differ; queue count, next-order identity and Native queued tail remain unchanged unless original logic legitimately consumes an order. Introduce counterexample fixtures for 12:53 attack rollback and 12:10 debt only for aspects actually evidenced.
**No-go:** asserting gameplay smoothness from simulated geometry.

## Stage 4 — Implement a *Native direct patch*, not a new Controller
**Preconditions:** Stage 1 site/ABI verified; Stages 2–3 negative proof gates passed.
**Work:** guarded WinX64 inline detour/branch patch at the proven original function(s); prefer calling original functions, altering only localized predicates/inputs/outputs. Native engine remains owner of input, queue, movement and attack. Retire/disable the old Lua active scheduler/reassert in this mode. If Lua is retained, settings/diagnostics only and no MOVE/ATTACK issuing.
**Pass:** Windows isolated fixtures demonstrate exact call-through, no double execute, unchanged original queue/targets and rollback to original behavior on unsupported build or disabled mod.
**No-go:** moving the Lua algorithm to C++ and claiming the engine has been modified.

## Stage 5 — Robust Hook installation / P0
**Work:** instrument MinHook allocator behavior for 13:18 status9 first MOVE hook failure in isolated Win64 process. Prove cleanup for 0..16 hook partial-creation failures, near-page allocation limits, process-wide pinning and Stop/Quit behavior; do not add unbounded retries or skip guards.
**Pass:** MSVC v142/MASM build, existing CTest 14/14 minimum, new fault injection, no dangling trampoline or partially enabled engine patch. Parallel with Stage 1, required before game-facing use.

## Stage 6 — Full regression, packaging, bounded final WH3 verification
**Work:** run H4–H8 frozen tests for backwards reference, new native call-through/differential tests, exact 9.0.2 map/hash and packaging contracts. Produce complete source, WinX64 Native DLL, normal and DEBUG PACK, manifest and reproducible SHA256. Only after static + Windows gates, one combined real WH3 acceptance for Shift MOVE/ATTACK, EXIT, normal RMB, multiplayer/multiple units if feasible, and Quit-to-Windows.
**Pass:** original Shift really behaves better on screen and native queue remains intact; no Lua dispatch or shadow-plan dependency; separate BUILD/STATIC/WINDOWS/WH3 results.
**No automatic Steam publish.**

## Dependency diagram
Stage 0 → Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 6. Stage 5 can proceed in parallel with Stage 1 but must close before Stage 6.

## Immediate next task
**Start Stage 1:** reverse WH3 original Shift motion-braking and current-order completion/next-order activation jointly; use the 9.0.2 EXE binary or reliable prior disassembly when available. Report verified sites, unknowns and disconfirming facts. Do NOT resume H9 Lua handoff experiments or create a C++ replacement queue.

## Deferred
Visible MCT, arbitrary performance tuning, old D1/H1–H8 policy extensions and Steam publication. Historical documents are in docs/past_doc and are no longer default reading.
