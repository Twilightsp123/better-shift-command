# Native RE Map — known locations vs unknown semantics

## Grounded 9.0.2 known sites (candidate, not runtime-promoted)
See native_maps/candidates/wh3_9.0.2_fec656f4.json and generated_native_map.hpp. Keep exact EXE SHA and byte guards.

| Site / layout | Grounded meaning | NOT proved |
|---|---|---|
| Move 0x030351AC, Attack 0x03033544 | Native order entry / capture detours | final 'order finished' or queue-head advance |
| Lua MOVE 0x02ED6404, Lua ATTACK 0x02ED5C9C | Lua API ingress | player Shift click originates here |
| publish_move 0x01CAFDDC, publish_attack 0x02DF3410 | command publication hooks | a safe, lossless 'replace progression policy' lever |
| writer_begin, writer_finalize, copy, stage, handlers, selection, free | packet pipeline / lifetime observation | authority to suppress arbitrary game commands |
| active order: count root+0x2F88, head root+0x2F8C | read-only stable-snapshot order head | queue-head writer lock/lifetime protection |
| slots root+0x288, stride 0x120, VTable +0x18, seq +0x20 | read-only type/sequence identity | direct safe mutation of slot/queue index |
| Full Move VTable RVA 0x03913618 | top-level MOVE outcome identity | all MOVE subclasses are equivalent |
| Attack VTable RVA 0x03912988 | ATTACK outcome identity | permission to skip target/lifetime verification |
| Simple Intercept Move VTable RVA 0x03910438 | internal sibling constructor | valid top-level MOVE identity |

## Investigation priority
1. Static call/dataflow from top-level Order entry and command publication to queue write and original execution.
2. Trace both MOVE and ATTACK native complete predicates, event/flag writes, consumer(s) of OrderHead, head increment/erase/destructor and next-order activation. Record *exact function, caller and context* for each.
3. Prove a **common transition decision point** (if one exists). Distinguish input append, native issue, scheduling, completion event, queue pop and movement control updates. Do not assume one function covers all.
4. Verify native queue mutations preserve engine sequence, target identity, order lifetime, revision and interaction with external orders.
5. Re-derive guards and VTables for current WH3 build, cross-check the candidate map, and grade every new site as STATIC, WINDOWS_FIXTURE or WH3_RUNTIME.
6. Assess if read-only queue inspection can be combined with a safely reversible detour. Never write root+offset directly based on the read-only probe alone.

## Required RE deliverable per site
- target EXE SHA/build, RVA, original bytes/mask, function signature/ABI and calling convention, predecessor/successor graph, dataflow evidence;
- alternative interpretations, thread/context ownership, exact exception/suspend handling, rollover behavior, negative false-match fixtures;
- initial proof grade and promotion gates, stored in RISKS_AND_DECISIONS.md.
- no new 'release-authorized' address from a mere callgraph guess.

## Hook installation P0 is a separate prerequisite
At 13:18, MH_CreateHook for first MOVE failed with MH_ERROR_MEMORY_ALLOC. The current platform_start_observer sets attempted=true before creating hooks, retries once after 50ms, then locks the process if that fails. Do not add unbounded retry or partially enable a guessed hook. First isolate MinHook allocator/nearby executable page behavior in a mock Windows process with byte-identical runtime assumptions.
