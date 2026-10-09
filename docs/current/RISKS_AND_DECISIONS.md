# Open Issues, Evidence Grades and Decision Log

This file is normative for proposed NQTR. Labels: FACT = verified in cited source/log; INFERENCE = plausible mechanism; OPEN = unproved; PROPOSED = choice not yet approved.

| ID | Status | Issue / decision | Next proof |
|---|---|---|---|
| NQ-001 | FACT | Native Bridge original player order executes before Lua observes it; Lua and Native can diverge. | trace BridgeHost::order and current Controller poll |
| NQ-002 | FACT | Lua rollback issues nonqueued MOVE, not proof that original Native queued tail survived. | actual native order snapshot after rollback |
| NQ-003 | FACT | 12:53 Shift ATTACK blocked by G11 policy and exact Native ATTACK later rolled back. | immutable log + deterministic reproduction |
| NQ-004 | FACT | 13:18 MinHook first MOVE creation fails with status9, after retry. | isolated Windows backend instrumentation |
| NQ-005 | OPEN | The true native completion / queue-head advancement function and safe detour do not yet have verified RVA or ABI. | RE callgraph + dataflow; dual independent signatures |
| NQ-006 | OPEN | Would early Native queue advance alone retain all engine route-guidance semantics? | geometry + queue state oracle, no assumed physics |
| NQ-007 | DECIDED GOAL | Modify WH3's **original native Shift behavior in its own call path**; do not replace it with a BSC Native scheduler, Lua shadow queue or replay system. | original-code braking/completion/attack dataflow + narrow patch proof |
| NQ-008 | OPEN | Which lock/thread handles order lifetime, queue write and cancellation? | Windows thread/exception instrumentation |
| NQ-009 | OPEN | 12:10 unpaid guide obligation, H6 conditional near-pass not confirmed in WH3. | modeled geometry and dataflow analysis |
| NQ-010 | OPEN | MH_ERROR_MEMORY_ALLOC is not necessarily exhausted RAM; MinHook executable-near allocation may fail. | allocator reason trace, Windows fault injections |
| NQ-011 | PROPOSED | All old D1/T1/H1–H8 architecture papers are archived, not current implementation authority. | docs/current + reference gate |
| NQ-012 | FACT | Native 9.0.2 mapping is static candidate; native_maps/CURRENT stays 9.0.1. | map and build provenance |
| NQ-013 | OPEN | Does the original Shift stop arise in terminal braking, arrival state, queue pop or successor activation? A new queue owner would not establish this. | comparative original native instruction dataflow and Windows fixture |
| NQ-014 | DECIDED GOAL | Lua may provide optional settings/diagnostics but cannot issue replacement MOVE/ATTACK, rollback or advance original native orders in the redesigned mode. | source contract + negative instrumentation test |

## Safety constraints
- Never revive retracted Entity+0x18 MovementComponent claim. Do not bind quarantined physical APIs into command completion.
- No guessed new Hook location, signature, VTable, native queue write offset or mutation without independent evidence.
- No unbounded retry of MinHook after uncertain partial apply; process-restart-required remains a legitimate fail-closed state.
- Existing high-level behavior acceptance remains exactly the user product contract in PRODUCT_CONTRACT.md.
- Questions that require WH3 runtime remain marked OPEN and are not hidden inside synthetic test success.

## Decision record
- 2026-10-09 / D-NQ-001: freeze H8 as a reference candidate only; start documentation-only NQTR on independent branch.
- 2026-10-09 / D-NQ-002: prioritize finding real Native queue completion/advance authority over more Lua threshold patches.
- 2026-10-09 / D-NQ-003: preserve old design/experiments byte-identically in docs/past_doc, make current directory only active documentation.
- 2026-10-09 / D-NQ-004: Retain native mapping as evidence only; never write the game queue based on guessed fields.
- 2026-10-09 / D-NQ-005 (user correction): **Directly patch original WH3 Shift behavior.** Reject the proposal for a BSC-specific Native transition decision owner or an alternative order scheduler. Research original queued MOVE terminal braking, completion and native ATTACK handoff before choosing any hook.

Do not call any proposal 'implemented' until committed code and the corresponding tests exist.
