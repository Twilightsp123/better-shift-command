# N1 executable reverse-engineering procedure — Native Shift Behavior Patch

**Status:** PLANNED, not performed on target executable. **Date:** 2026-10-09.  
**Owner of commands and order lifetime:** WH3 native engine; BSC does not own a second queue or command executor.  
**Prior evidence:** [N1_STATIC_FINDINGS.md](N1_STATIC_FINDINGS.md).  
**Target:** WH3 9.0.2 `Warhammer3.exe`, SHA256 `fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785`.

## 0 — Required inputs, acquisition, version gate

**Preferred:** a copy of the user's installed, unmodified `Warhammer3.exe` from WH3 9.0.2. No game session required. Never modify the disk executable. The file may be too large to upload; if so, use option B.

- **A: exact PE binary**: record SHA256 and file size, verify PE/AMD64, preferred image base, section bounds, EXE version/build. Reject 9.0.2 RVA reuse if SHA mismatch. Do not assume a same-numbered game version is byte-identical.
- **B: analyzed Ghidra/IDA project or exports**: from the *same SHA-matched PE*, provide executable SHA, image base, function disassembly/decompilation, callers/callees, cross-references to the known order constructors/VTables, and especially a dump of candidate `root+0x2F88`/`root+0x2F8C` **write** instructions and their surrounding functions. Include exact original machine bytes. A detached text report without provenance is weak evidence.
- **C: bounded binary excerpt**: if neither A nor B is transferable, collect architecture/PE metadata and sections covering candidate functions, including relocations/unwind, but this may be **insufficient to find consumers**. Truncated windows of existing 16 hooks cannot by themselves recover unknown runtime progression.

Recommended hash verification on Windows (PowerShell):

```powershell
Get-FileHash "C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\Warhammer3.exe" -Algorithm SHA256
```

**Stop rule:** mismatched SHA -> **new version mapping task**, not silently using 9.0.2 RVAs. No installer, pack, multiplayer or WH3 runtime is required for N1.

## 1 — The exact native questions to settle

We need *five different events*, even if some are implemented by the same function:

1. When a Shift MOVE is **appended versus REPLACEd**, and where original order identity and future tail live.
2. Which **per-frame/tick** engine function drives current MOVE and chooses arrival, braking, desired speed, steering, and terminal mode.
3. Which condition marks the original MOVE **complete**; is completion contingent on zero speed, distance, arrival flag, path state or something else?
4. What original instruction(s) mutate queue count/head or retire an order; does lifecycle involve head increment, compaction, ring wrap, destructor, cancel/reset or another container?
5. Where next MOVE or ATTACK is **activated**; whether activation itself resets locomotion/path or target state.

*Do not conflate order issuance at RVA 0x030351AC with frame execution. Do not conflate Smart Guard's optional `state_transition` hook with ordinary Shift progression.*

## 2 — Static analysis work plan and prioritized search

### Track A — Producer to consumer (priority P0)

Start from SHA-verified native MOVE/ATTACK issue function candidates (`0x030351AC`, `0x03033544`), allocator (`0x02F53128`), and original constructors (`0x0300B518`, `0x0300BDC0`, `0x0300B8C4`) as *search anchors only*.

1. In Ghidra, rename them conservatively as `candidate_issue_move`, `candidate_issue_attack`, `candidate_order_alloc`, etc.; verify function boundaries, true x64 ABI, and byte guards before naming any engine semantics.
2. Collect forward dataflow for stored queue element, root, sequence, object type, payload and the queued flag; distinguish original game writes from BSC wrapper reads.
3. Follow actual root/container and order object **consumer** xrefs. Inspect virtual dispatch through candidate full MOVE VTable `0x03913618`, ATTACK VTable `0x03912988`; identify methods as constructors/destructors/serialization/execution only from their implementation/callers.
4. Build a graph from issuer/allocator and type identity to consumer tick or command dispatcher. If the graph cannot be established, record **UNLINKED**, not a guessed edge.

### Track B — Write analysis of queue lifecycle (priority P0)

Root candidate fields: count `+0x2F88`, head `+0x2F8C`, slots `+0x288`, stride `0x120`. These are **read-observed layouts**, not authority to mutate.

1. In *decoded instructions*, search references to candidate head/count fields; classify READ/WRITE/RMW and register-derived aliases to root. A raw occurrence of little-endian `8c 2f 00 00` is not a verified field access; optimized code may access the same field through shifted pointers/offset calculations.
2. For each write, retain instruction VA/RVA, containing function, predecessor/successor blocks, object-base provenance, callers/callees, and bytes/masks.
3. Find what controls writes during **normal Shift arrival**, **non-Shift right-click REPLACE**, **HALT/cancel**, **attack target death**, and **forced interruptions**; do not assume all paths share one function.
4. Locate any native **destructor / order retire / next activation** calls. Determine whether the head write is cause, effect, or bookkeeping of the movement handoff.

### Track C — Terminal MOVE and animation/steering boundary (priority P0)

1. Starting at verified active MOVE consumer, trace conditions and calls reading destination `slot+0x58` and state that influences speed/arrival/path.
2. Locate exact branch that differentiates queued-with-successor MOVE versus terminal MOVE, if it exists. If no discriminator exists, record that separately.
3. Reconstruct the **relative ordering** of terminal braking, move-complete predicate, queue-head mutation, old-order retirement, and successor activation.
4. Determine whether next MOVE naturally inherits continuous motion or starts a new path with a movement reset. No geometry/threshold patch before this answer.
5. Contrast with ordinary RMB and unqueued last MOVE. Route-point skipping and 180-degree turns must remain impossible in unsupported contexts.

### Track D — Native ATTACK handoff (priority P1)

Trace original queued successor ATTACK activation, target existence/identity validation, and semantics when current MOVE completes. Separate true vanilla behavior from known H8 Lua reissue/rollback failures. Do not treat original attack object's construction as proof it was activated.

### Track E — lifetime, threading, patch preconditions (priority P0 before N4)

Confirm which thread runs each candidate, whether queue mutation is synchronized, original object ownership/lifetime, exception/unwind constraints, concurrent unit handling, enable/disable safety and precise call ABI. A read-only double snapshot is not a queue write protocol.

## 3 — Competing causal hypotheses and falsifiers

| ID | Candidate explanation | Required proving evidence | Disconfirming evidence |
|---|---|---|---|
| H-A | Terminal MOVE forces braking before original completion/head advance | per-frame native branch and speed-state write before completion; compare queued vs terminal | no braking state change until after successor activated |
| H-B | Successor activation rebuilds path and resets locomotion, even if MOVE completion is early | activation path clears/reinitializes native movement state; exact old/new order identities | state preserved and no reset performed at activation |
| H-C | Original guidepoint completion insists on exact arrival/stop independent of future queue | verified completion predicate tied to arrival and its path context; prove queue discriminator absence/presence | arrival predicate is bypassed automatically with queued successor |
| H-D | MOVE→ATTACK delay is only caused by H8's Lua arbitration, not vanilla | native ATTACK originally activates but is overwritten by BSC issue path | original native handoff itself delays/blocks ATTACK in unmodified logic |

All remain **OPEN** until target EXE-level evidence exists. Multiple explanations can coexist.

## 4 — Candidate selection and narrow-patch design decision

**Outcome A — one localized native decision (preferred):** a verifiable queued MOVE-only predicate can avoid unnecessary braking or adjust completion while preserving original order activation and path/lifetime.

**Outcome B — 2–3 interdependent original native decisions (conditionally acceptable):** completion and successor activation both need an original-call-path alteration; prove lifetime/order invariants and fail closed before attempting.

**Outcome C — large movement/path engine rewrite required:** reject the minimal Native Shift Patch premise and record an explicit feasibility no-go. Do **not** silently move H8's Lua queue scheduler to C++.

A candidate is eligible only with:
- exact EXE SHA, function start RVA, instruction range, original bytes/masks and independent ABI evidence;
- actual xrefs and read/write/call graph back to original order semantics, **not** just a relocated familiar byte sequence;
- queue-specific condition or proven normal-RMB-safe original branch;
- complete semantics for order identity, cancel/REPLACE, target identity, retire and consecutive activation;
- disconfirming evidence search, rollback/fail-closed proposal and missing uncertainties disclosed.

**No direct writes to OrderHead, slots, VTables or guessed component offsets.**

## 5 — Required N1 deliverables

1. **Verified native graph** with separate nodes for issue, construction, per-tick MOVE, terminal braking, completion, queue mutation, retire and next activation. Unknown nodes remain explicitly UNKNOWN.
2. **Evidence ledger** for each candidate with `build_hash, RVA, exact bytes, ABI/register args, typed object/root derivation, read/write sets, callers/callees, proof level, alternatives, negative controls, disassembly reference`.
3. **Braking timeline** and MOVE→MOVE vs MOVE→ATTACK transition state diagram for original game.
4. **Risk register** for thread safety, object lifetime, RMB regression, patchguard, MinHook allocator and version changes.
5. **Feasibility verdict A/B/C** and exact N2/N3 decisions that can be differential-tested without inventing native behavior.

N1 pass requires a *real* original executable/dataflow relationship supporting at least one defensible patch hypothesis. N1 failure or blocked status is legitimate; bytes without a proven native execution chain do not satisfy the gate.

## 6 — Offline-only gate and follow-on work

Before actual binary is supplied, available work: source audit, historical repro isolation, version contract, proof schema and tooling plan. After EXE/verified disassembly: static analysis and native site ledger, then strictly evidence-derived offline differential tests. No WH3 runtime test in N1; no binaries/PACKs/releases until implementation and Windows stability gates pass.

Related documents: [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md), [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md), [N1_STATIC_FINDINGS.md](N1_STATIC_FINDINGS.md), [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), [RISKS_AND_DECISIONS.md](RISKS_AND_DECISIONS.md).
