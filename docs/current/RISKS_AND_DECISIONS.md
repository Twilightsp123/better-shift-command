# Open Issues, Evidence Grades and Decision Log

**2026-10-10 binding product correction:** [PRODUCT_CAUSE_CORRECTION_20261010.md](PRODUCT_CAUSE_CORRECTION_20261010.md). The native Shift MOVE problem is **intra-unit soldier model asynchronous arrival/turning and crowding**, not a proven unit-wide stop. MOVE→ATTACK pause belongs to the earlier Lua Controller regression. Older findings about native braking, queue progress or state transfer are **mechanism evidence, not causal proof** of model crowding.

This file is normative for proposed NQTR. Labels: FACT = verified in cited source/log; INFERENCE = plausible mechanism; OPEN = unproved; PROPOSED = choice not yet approved.

| ID | Status | Issue / decision | Next proof |
|---|---|---|---|
| NQ-001 | FACT | Native Bridge original player order executes before Lua observes it; Lua and Native can diverge. | trace BridgeHost::order and current Controller poll |
| NQ-002 | FACT | Lua rollback issues nonqueued MOVE, not proof that original Native queued tail survived. | actual native order snapshot after rollback |
| NQ-003 | FACT | 12:53 Shift ATTACK blocked by G11 policy and exact Native ATTACK later rolled back. | immutable log + deterministic reproduction |
| NQ-004 | FACT | 13:18 MinHook first MOVE creation fails with status9, after retry. | isolated Windows backend instrumentation |
| NQ-005 | UPDATED / HISTORICAL GAP | Exact-file 9.0.3 queue pop/head writer is now identified (see NQ-020), but no safe detour ABI or proof that queue advancement explains per-model formation crowding. | trace formation-model target and turn consumers, not raw head mutation |
| NQ-006 | OPEN | Would early Native queue advance alone retain all engine route-guidance semantics? | geometry + queue state oracle, no assumed physics |
| NQ-007 | DECIDED GOAL | Modify WH3's **original native Shift behavior in its own call path**; do not replace it with a BSC Native scheduler, Lua shadow queue or replay system. | original-code braking/completion/attack dataflow + narrow patch proof |
| NQ-008 | OPEN | Which lock/thread handles order lifetime, queue write and cancellation? | Windows thread/exception instrumentation |
| NQ-009 | OPEN | 12:10 unpaid guide obligation, H6 conditional near-pass not confirmed in WH3. | modeled geometry and dataflow analysis |
| NQ-010 | OPEN | MH_ERROR_MEMORY_ALLOC is not necessarily exhausted RAM; MinHook executable-near allocation may fail. | allocator reason trace, Windows fault injections |
| NQ-011 | PROPOSED | All old D1/T1/H1–H8 architecture papers are archived, not current implementation authority. | docs/current + reference gate |
| NQ-012 | FACT | Native 9.0.2 mapping is static candidate; native_maps/CURRENT stays 9.0.1. | map and build provenance |
| NQ-013 | SUPERSEDED INCORRECT PREMISE | Earlier N1 assumed a vanilla Shift MOVE stop. User corrected this: native defect is models arriving/turning out of sync within one unit, with mutual crowding; prior braking-centered hypothesis is not product evidence. | follow new NQ-038/039 and formation-to-model dataflow |
| NQ-014 | DECIDED GOAL | Lua may provide optional settings/diagnostics but cannot issue replacement MOVE/ATTACK, rollback or advance original native orders in the redesigned mode. | source contract + negative instrumentation test |
| NQ-015 | OPEN / N1 BLOCKER | No matching WH3 9.0.2 EXE/disassembly in accessed materials; current repository identifies issuer and optimistic order-reader but not native MOVE update/head writer/next activation. | hash-verified EXE/Ghidra xrefs and read/write dataflow; see N1_STATIC_FINDINGS.md |
| NQ-016 | SOURCE-VERIFIED NEGATIVE | Optional Smart Guard `state_transition_hook` is a filtered Pursue/TakeUpPositions path, NOT established Shift queue progression despite its name. | separately reverse native per-frame queue consumer; do not reuse Hook17 blindly |
| NQ-017 | SOURCE-VERIFIED LIMITATION | EvidenceProbe::active_order double-reads count/head/slot; it is not synchronized and does not grant queue mutation/lifetime authority. | investigate original thread ownership, atomics/locks and retirement |
| NQ-018 | PARTIALLY CLOSED / 9.0.3 EXE | User-provided 9.0.3-labelled EXE SHA `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a` and one original 40-slot head/count pop primitive now have real instruction evidence. Game-version resource, other Hook addresses/ABI and braking/completion/activation remain unverified. | pursue state/steering dataflow in N1_903_ORDER_LIFECYCLE_STATIC.md |
| NQ-019 | OFFLINE TOOLING + EXECUTABLE RE | Existing PE/Ghidra scouts have synthetic tests; **separate direct LLVM/PE analysis of real user-provided EXE** established ring pop. Ghidra runtime has not been tested; no playable WH3 behavior proof. | inspect virtual completion predicate, movement state and target handoff |

| NQ-020 | EXACT FILE STATIC EVIDENCE | Original ring pop at 0x02F4FD10 increments aliased head (+0x2D04 from UnitRoot+0x288), decrements count (+0x2D00), and wraps at 40; five verified direct calls. This is a risky *mutating lifecycle primitive*, NOT a patch recommendation. | identify caller-specific MOVE completion and native braking independently |

| NQ-021 | EXACT FILE MOVE STATUS DATAFLOW | Native MOVE constructor 0x030090BC writes VTable 0x0390B4F0. Virtual +0x10 resolves to 0x030440F8, setting object+0x20 from (related_state+0x240 == 0). In state path 0x030433B0 this flag gates ring pop. Original meaning of related-state+0x240, MOVE terminal brake, and next activation remain OPEN. | trace related-state writer, MOVE virtual +0x08, and native successor activation; see N1_903_MOVE_STATUS_CHAIN.md |

| NQ-022 | EXACT FILE TASK COUNT | `related_state+0x240` is an auxiliary native task/suborder-like collection count: append `0x02F2FFB0`, cleanup `0x02F4FD5C`, per-unit update `0x03043520`. This count feeds the MOVE completion-status byte but is NOT a geometric arrival predicate. | classify task objects and track correct lifetime; see N1_903_SUBTASK_AND_HANDOFF.md |
| NQ-023 | EXACT FILE CONDITIONAL HANDOFF | `0x0304433C` can call current order vfunc +0x40, next order +0x38 and +0x48, followed by original pop/collection cleanup. For MOVE vtable +0x40 the special state object is returned only under narrow native conditions; this is NOT universal queued MOVE lookahead. | understand MOVE+0xA0 object and native braking/activation before local patch decision |

| NQ-024 | STATIC VERIFIED SPECIAL-TRANSFER BOUNDARY | Exact 9.0.3 MOVE vtable +0x38 returns true; ATTACK vtable +0x38 returns false and ATTACK +0x48 is a noop. Native queue special handoff 0x0304433C therefore admits a MOVE successor but vetoes an ATTACK successor on this specific path. No proof of default MOVE→ATTACK failure or general MOVE continuity. | Trace ordinary ATTACK activation separately; see N1_903_MOVE_VS_ATTACK_TRANSFER.md |
| NQ-025 | STATIC VERIFIED STATE REUSE, PHYSICS UNKNOWN | MOVE +0x48 at 0x03040864 receives the existing transfer object, sets state+0x20=1, copies task payload and binds it to successor MOVE+0xA0. Current MOVE+0x40 only exposes the pointer under strict checks incl state==4. | Identify lifecycle/movement meaning of states 1/4 and terminal braking; do not bypass eligibility or refcount. |

| NQ-026 | EXACT-FILE MOVE STATE ORIGIN | The native MOVE+0x08 task work path saves address of MOVE+0xA0 into init+0x50. Task constructor copies it to task+0x80; conditional initializer 0x02F41644 obtains a state object via 0x0310ED2C and writes it through task+0x80 back to MOVE+0xA0. | Verify task creation branches, full pointer/refcount ownership, and movement meaning; see N1_903_MOVE_STATE_ORIGIN.md |
| NQ-027 | EXACT-FILE NATIVE TRANSFER REUSE LIMIT | Native state controller has a path writing state+0x20=4; successor adoption writes state+0x20=1. MOVE+0x08 may detach an existing transfer object on byte-flag, validator or scalar consistency check using engine constants 0.0 / approximately 0.01, decrementing refcount. | Classify state enumeration and actual scalar; no forced transfer or distance tuning. |

| NQ-028 | EXACT-FILE NORMAL ATTACK ROUTE | Generic original head processor 0x030433B0 dispatches active order virtual +0x08/+0x10 via 0x03043424. Issuer-derived ATTACK vtable +0x08 is 0x03025788, which submits original auxiliary attack tasks via 0x02F2FFB0. Rejection of the separate MOVE transfer gate does NOT prevent regular native ATTACK activation. | Identify MOVE predecessor's completion timing, ATTACK target validity and normal RMB contrast; see N1_903_ORDINARY_ATTACK_DISPATCH.md |

| NQ-029 | EXACT 9.0.3 STATE-MACHINE REBASE | Driver 0x0311DE74 switches over state+0x20 values 0–4. MOVE receiver 0x03040864 sets state=1 and pending payload+0x120..0x140; state-1 driver later copies to+0x60..0xA8. No physical motor semantics proven. | trace state-1 post-rebase speed/path calls; see N1_903_STATE_MACHINE_REBASE.md |
| NQ-030 | HANDOFF FLAG SAFETY CONTRADICTION | One native branch writing state+0x20=4 at 0x0311E4B5 simultaneously clears byte state+0x24 at 0x0311E4B9. Current MOVE transfer provider 0x03039FB0 requires state=4 and state+0x24!=0. Thus state4 alone cannot justify forced handoff. | find proven writer of state+0x24=1 with valid state4 and lifetime; no flag patch. |
| NQ-031 | SHARED SCALAR REFERENCE FRAME, UNPROVEN PHYSICS | Both outgoing current MOVE 0x03025DD2 and successor MOVE 0x030408AF call scalar getter 0x0301C1B4, selected by MOVE+0x9A bit4. Receiver builds state+0x140 values, stage1 copies them to state+0xA0 before outgoing reuse validates consistency. Scalar units unknown. | correlate actual original motor/path consumer, not thresholds. |

| NQ-032 | EXACT-EXE FLAG WRITER FOUND | Original state callback `0x0311E80C` writes state+0x24 at `0x0311EB10`, determined by result of complex native `0x0310F560` and another gate on `[rbx+0x4E4]`. Accepted route sets state 2; other exits set state 4. Thus state4+flag1 reachability still needs proof; see N1_903_TRANSFER_FLAG_WRITER.md. | trace validator/predicate and later state4+flag1 lifecycle; do not force flag. |\n\n| NQ-033 | INSTRUCTION-VERIFIED ROUTE PROCESSOR | 9.0.3 `0x0310F560` updates path/working fields and dispatches `0x030EA7D0` / `0x030EA6F4`; latter path reaches `0x030E88C8` with spatial distance arithmetic and derived-route writes. It is not a pure Boolean to force true. | Trace path output to actual motor/braking; see N1_903_ROUTE_GATE_ANALYSIS.md |
| NQ-034 | CONDITIONAL FLAG TRUTH TABLE | In callback `0x0311E80C` with DIL initially zero, original `state+0x24` writer yields 1 only if `0x0310F560` returns AL nonzero AND native `[rbx+0x4E4]>=2`. Meaning of mode, AL and eventual state4+flag1 reachability unverified. | Recover mode usage and state2->state4, no forcing flags or Hook. |

| NQ-035 | ORIGINAL STATE4 TRANSITIONS DIFFER | Separate state2->helper path at 0x0311E56E calls 0x0311EC28, which sets state4 at 0x0311ED63 without adjacent flag clear; a different state4 writer 0x0311E4B5 does clear +0x24. Native helper side effects/true Shift reachability not yet proven. | compare state4+flag1 lifecycle to motor updates; see N1_903_STATE4_GEOMETRY_BRANCH.md |
| NQ-036 | GEOMETRY EARLY RETURN, NOT YET BRAKING | State4 processor 0x0311F534 uses geometric sqrt at 0x0311F7D1 and threshold comparator 0x0311F8BB–C5, clears inner+0x6C and jumps to epilogue when gated. No verified desired-speed/velocity write here. | follow early-exit vs continued motor dataflow before any Hook. |

| NQ-037 | BRANCH DIFFERENTIAL VERIFIED, BRAKING STILL OPEN | 9.0.3 state-4 geometric early exit at `0x0311F8CB` jumps straight to cleanup, skipping guarded route helpers, nested `+0x40` pointer assignment and nested `+0x6C=1`. No downstream motor-speed writer or physical stop causality established. | Trace `0x0312D088` route object to native locomotion consumer, compare queued MOVE and ordinary RMB; see N1_903_STATE4_ROUTE_SETUP_DIFF.md. |

| NQ-038 | USER-CONFIRMED PRODUCT DEFECT | Original queued Shift MOVE makes soldier models inside one unit card turn/reach route points asynchronously; their orientations diverge and they squeeze/crowd each other. Actual native responsible function remains UNKNOWN. | rederive 9.0.3 formation slot assignment, per-soldier arrival/turning, and group coordination from UnitRoot; see PRODUCT_CAUSE_CORRECTION_20261010.md |
| NQ-039 | PRODUCT REGRESSION / OLD LUA | The noticeable MOVE→ATTACK stop was caused by BSC Lua active arbitration/reissue/rollback, not proven native vanilla behavior. H8 logs support overwrite of accepted native ATTACK. | disable old Lua active issuer in future Native mode; test original ATTACK without BSC competition before considering native attack patch |
| NQ-040 | ACTIVE N1 ROOT-CAUSE GAP | Existing ring pop, transfer states and route geometry evidence does not identify the source of model-level crowded turns. Blind geometry/desired-speed patch would optimize the wrong symptom. | locate formation-to-model target producer, individual soldier steering/arrival and collision consumers; prove first divergence and feasibility |

| NQ-041 | EXACT BINARY FORMATION-LEVEL ENTRY LEAD | Original unit update `0x03043648` calls `0x030421A4` (loops root+0x184/+0x188 position-bearing members, reads member+0x88/+0x90) and `0x0302AE0C` (uses root+0x32F8 and root+0x3C38) before queue stage `0x0304433C` on observed path. These objects are not yet proven individual soldiers nor per-model waypoint targets. | Trace array producers, member object types, group target writers and individual steer/turn consumers; see N1_903_FORMATION_ENTRY_CALLGRAPH.md. |

## Safety constraints
- Never revive retracted Entity+0x18 MovementComponent claim. Do not bind quarantined physical APIs into command completion.
- No guessed new Hook location, signature, VTable, native queue write offset or mutation without independent evidence.
- No unbounded retry of MinHook after uncertain partial apply; process-restart-required remains a legitimate fail-closed state.
- Existing high-level behavior acceptance remains exactly the user product contract in PRODUCT_CONTRACT.md.
- Questions that require WH3 runtime remain marked OPEN and are not hidden inside synthetic test success.

## Decision record
- 2026-10-10 / D-NQ-017 (user correction, highest precedence): explicitly separate **vanilla intra-unit soldier crowding on chained Shift MOVE** from **BSC Lua Controller MOVE→ATTACK stopping regression**. Stop prioritizing terminal braking, early queue-head advancement or geometry threshold tuning until connected to actual model-level divergence. Preserve earlier exact-file N1 research as engine mechanism evidence only. No runtime patch authorized.

- 2026-10-09 / D-NQ-001: freeze H8 as a reference candidate only; start documentation-only NQTR on independent branch.
- 2026-10-09 / D-NQ-002: prioritize finding real Native queue completion/advance authority over more Lua threshold patches.
- 2026-10-09 / D-NQ-003: preserve old design/experiments byte-identically in docs/past_doc, make current directory only active documentation.
- 2026-10-09 / D-NQ-004: Retain native mapping as evidence only; never write the game queue based on guessed fields.
- 2026-10-09 / D-NQ-005 (user correction): **Directly patch original WH3 Shift behavior.** Reject the proposal for a BSC-specific Native transition decision owner or an alternative order scheduler. Research original model-level formation target, waypoint progression and coordination; old Lua ATTACK regression is a separate track.

- 2026-10-09 / D-NQ-006: N1 first static source/map triage recorded; no new RVA/ABI promoted, no original shift patch authorized.
- 2026-10-09 / D-NQ-007: switch current executable target to WH3 9.0.3; preserve all 9.0.2 source/maps as historical evidence, do not treat previous RVAs as runtime-compatible with 9.0.3.
- 2026-10-09 / D-NQ-008: N1 tooling is read-only, must never auto-promote bytes/offsets to confirmed Hook or patch. Offline test successes are tooling contracts only. Require actual exact-build MOVE completion/braking dataflow before N2.

- 2026-10-09 / D-NQ-009: user-provided 9.0.3-labelled EXE statically analyzed; native ring pop and callers identified. No runtime Hook, ABI or gameplay claim promoted; see N1_903_ORDER_LIFECYCLE_STATIC.md.

- 2026-10-09 / D-NQ-010: exact-file MOVE constructor/virtual status dataflow identified; cannot equate status zero-check with physical arrival or authorize head manipulation.

- 2026-10-09 / D-NQ-011: native task-count and conditional successor-transfer paths documented. No forced status/queue-head mutation and no new Hook authorized.

- 2026-10-10 / D-NQ-012: exact-file static native MOVE/ATTACK special-handoff eligibility differs; do not force ATTACK eligibility or assume the branch is universal Shift progression. No patch authorized.

- 2026-10-10 / D-NQ-013: exact-file state-object writeback and native conditional invalidation documented. No fabricated eligibility patch, counter edits or forced transfer authorized.

- 2026-10-10 / D-NQ-014: ordinary ATTACK head activation confirmed distinct from native MOVE transfer. No `ATTACK+0x38` forcing; no substitute ATTACK issue.

- 2026-10-10 / D-NQ-015: original `state+0x24` writer and validator call now located. Native flag cannot be treated as fixed boolean permission or tuning constant; no Hook approved.\n\n- 2026-10-10 / D-NQ-016: reject patching the stateful route processor to always accept or bypassing mode/flag checks; exact-file evidence documents side effects and per-path mode requirement.

Do not call any proposal 'implemented' until committed code and the corresponding tests exist.
