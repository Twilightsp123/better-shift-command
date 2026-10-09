# Native Reverse-Engineering Map — WH3's Original Shift Code Paths

## Grounded 9.0.2 known sites (candidate, not runtime-promoted)
See native_maps/candidates/wh3_9.0.2_fec656f4.json and generated_native_map.hpp. Keep exact EXE SHA and byte guards.

| Site / layout | Grounded meaning | NOT proved |
|---|---|---|
| Move 0x030351AC, Attack 0x03033544 | Native order entry / capture detours | Shift braking, current order completion, successor activation or original execution state |
| Lua MOVE 0x02ED6404, Lua ATTACK 0x02ED5C9C | Lua API ingress | player Shift click originates here |
| publish_move 0x01CAFDDC, publish_attack 0x02DF3410 | command publication hooks | a safe, lossless 'replace progression policy' lever |
| writer_begin, writer_finalize, copy, stage, handlers, selection, free | packet pipeline / lifetime observation | authority to suppress arbitrary game commands |
| active order: count root+0x2F88, head root+0x2F8C | optimistic read-only double-read of active-order head (NOT an atomic/locked queue snapshot) | queue-head writer lock/lifetime protection |
| slots root+0x288, stride 0x120, VTable +0x18, seq +0x20 | read-only type/sequence identity | direct safe mutation of slot/queue index |
| Full Move VTable RVA 0x03913618 | top-level MOVE outcome identity | all MOVE subclasses are equivalent |
| Attack VTable RVA 0x03912988 | ATTACK outcome identity | permission to skip target/lifetime verification |
| Simple Intercept Move VTable RVA 0x03910438 | internal sibling constructor | valid top-level MOVE identity |

## Investigation priority — original engine, not a second executor
1. Trace **original Shift append/replace** input to queue write and command object identity; determine when/where the queued flag affects native behavior.
2. Trace **original MOVE terminal deceleration and steering state**: desired speed, arrival radius, braking switch, queued successor lookahead and any forced halt. Determine whether the visible stop occurs *before* native queue-head advancement.
3. Trace **native MOVE completion and successor activation** separately: completion state/predicate, event/flag writes, OrderHead changes, object retirement and next MOVE/ATTACK activation. Record exact function, caller and context for each.
4. Trace **native MOVE→ATTACK handoff** and target validation. Distinguish vanilla failure from the H8 Lua rollback symptom; no off-target intervention.
5. Connect each observed undesirable behavior to a particular original native decision branch, including whether only queued Shift commands pass it. Do not assume one universal queue-advance Hook exists.
6. Re-derive guards and VTables for 9.0.2, grade evidence STATIC/WINDOWS/WH3, and assess reversible narrow patch feasibility. Do not directly write OrderHead/slots based on read-only probes.
7. Verify every localized modification leaves WH3's original queue identity, future tail, lifetime, attack target, REPLACE and ordinary RMB behavior intact. **No Lua or C++ replacement order queue.**

## N1 repository audit checkpoint
See [N1_STATIC_FINDINGS.md](N1_STATIC_FINDINGS.md): the current source observes **order construction and active order reads**, but contains no verified original per-frame MOVE completion, braking, OrderHead writer, or successor activation function. The optional Smart Guard `state_transition` handler is **not** a demonstrated Shift advance hook. Target 9.0.2 EXE/disassembly required for the next reverse-engineering step. No queue writes permitted.

## Missing high-priority evidence
- No verified location yet for the original engine's MOVE terminal braking/desired-speed calculation.
- No verified location yet for the original engine's MOVE completion predicate or next native order activation.
- No proof that queue-head advance is the cause, rather than an effect, of the stop-and-go behavior.
- No verified native original Shift ATTACK handoff function or shared RMB divergence point.

## Required RE deliverable per site
- target EXE SHA/build, RVA, original bytes/mask, function signature/ABI and calling convention, predecessor/successor graph, dataflow evidence;
- alternative interpretations, thread/context ownership, exact exception/suspend handling, rollover behavior, negative false-match fixtures;
- initial proof grade and promotion gates, stored in RISKS_AND_DECISIONS.md.
- no new 'release-authorized' address from a mere callgraph guess.

## Hook installation P0 is a separate prerequisite
At 13:18, MH_CreateHook for first MOVE failed with MH_ERROR_MEMORY_ALLOC. The current platform_start_observer sets attempted=true before creating hooks, retries once after 50ms, then locks the process if that fails. Do not add unbounded retry or partially enable a guessed hook. First isolate MinHook allocator/nearby executable page behavior in a mock Windows process with byte-identical runtime assumptions.
