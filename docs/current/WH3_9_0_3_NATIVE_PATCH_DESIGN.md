# WH3 9.0.3 — Native Shift Behavior Patch design specification

**Date:** 2026-10-09
**Status:** DESIGN + PARTIAL EXACT-BINARY N1 STATIC RE — user-provided 9.0.3-labelled EXE inspected, ring-queue pop/write code recovered, MOVE braking/completion still unknown; no Hook authorized. [Tooling instructions](../../maintenance_tools/native_shift_re/README.md) describe PE/build SHA and Ghidra decoded-operand scouts; their outputs are *not* verified native queue writers.
**Development branch:** `research/n1-native-shift-behavior-patch-20261009`.
**Prior evidence:** `N1_STATIC_FINDINGS.md` and `N1_EXECUTABLE_RE_PLAN.md` are **9.0.2-only historical RE seeds**, not a 9.0.3 address map.

## 0. Purpose, immutable architecture and build gating

Improve WH3 **original** Shift commands. WH3 remains the sole owner of:
- Shift input, append vs ordinary right-click replace;
- original MOVE/ATTACK order objects, order storage/sequence, head advance and retirement;
- locomotion, path planning, formation, collision, AI, target/attack simulation and animation.

BSC may make **localized, version-guarded changes to proven WH3 native predicates or transition decisions**, with original functions retaining side effects, ownership and lifecycle. It must not introduce any Lua/C++ alternative command queue, canonical route scheduler, ACK-controlled reissue, rollback MOVE/ATTACK, independent order consumption, fabricated head mutation, or forced attack dispatch.

A Win64 DLL may be the runtime patch carrier; this is **not** a request to modify `Warhammer3.exe` on disk.

**9.0.3 version discipline:**
- User-provided 9.0.3-labelled EXE exact SHA256 is **518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a** (read-only local hash verified); 9.0.3 version resource itself has not been independently authenticated. This hash is not a released runtime build map.
- 9.0.2 SHA256 `fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785` and every 9.0.2 RVA/VTable/guard remain historical, *never runtime-valid for 9.0.3 by assumption*.
- 9.0.2 native map is useful as a structural **search seed** only. A 9.0.3 map must be a separate unpromoted candidate with per-site proof and independent, exact-executable bytes.
- Runtime loading/patch installation must fail closed on hash or guard mismatch, missing ABI proof, unsupported game version, invalid state or failed partial installation.

## 1. Three simultaneous reverse-engineering tracks

### L1 — original order lifecycle
Locate, in the actual 9.0.3 EXE:
1. The native Shift queued flag, append/REPLACE semantics and queue object identity.
2. Command creation and consumer execution; callgraph from producers to consumer/tick and order-state transitions.
3. Original MOVE completion decision, store(s) to count/head, retirement/destruction and next order activation. These may be separate functions and must not be conflated.
4. Thread and object lifetime ownership, REPLACE/HALT, cancelled command, target dead, attacked/interrupted unit paths.

The exact user-supplied EXE now has instruction evidence for count/head under a `root+0x288` array subobject (alias offsets `+0x2D00` and `+0x2D04`), 0x120 stride and ring pop/wrap at RVA `0x02F4FD10`. See [N1_903_ORDER_LIFECYCLE_STATIC.md](N1_903_ORDER_LIFECYCLE_STATIC.md). This **does not** establish permission to write the head, a completed MOVE, queue lifetime safety or a patch point.

### L2 — original locomotion and waypoint arrival
Trace from a verified original **executing** MOVE object to steering/desire speed, terminal braking, arrival flag and path state. Determine their ordering relative to MOVE-complete and successor activation:
- **H-A:** queued intermediate waypoint unconditionally enters terminal braking before head advance.
- **H-B:** next MOVE activation clears/rebuilds movement even when current order completed early.
- **H-C:** complete predicate waits for a hard arrival/stop state unrelated to the queued successor.
- **H-D:** native geometry/path planner cannot continue through discrete queued orders without larger changes.
All four remain hypotheses until proved by opcode/dataflow and negative controls.

### L3 — original queued ATTACK handoff
Trace native MOVE→ATTACK target validation and activation, order retirement, and normal right-click ATTACK. Distinguish original WH3 delay from previous BSC H8 Lua rollback: a log of a BSC rollback is not evidence of broken vanilla handoff.

**Priority:** L1 + L2 concurrently, L3 after producer/consumer linkage. Do not assume any universal `ShiftAdvance()` function.

## 2. Two candidate patch modules (NOT guaranteed to be two Hooks)

### Patch A — queued MOVE→MOVE continuity

Proposed behavior *only if engine evidence allows*:
- An original *current* MOVE has a confirmed, still-valid original *next* MOVE in the **same native queue**, with WH3-controlled lifetime and safe access.
- For a confirmed *intermediate guidance point*, WH3 may avoid unnecessary terminal full-stop and use its existing movement/steering handoff, while **the game's own completion, head advance, object retirement and next-order activation** remain authoritative.
- Must preserve route bends, no i+2 skipping, no path debt/canonical shadow route, no forced fixed-speed U-turn, no replacement of normal RMB.
- Even if the original engine supports successor look-ahead, a next-order read may be unsafe without native lifetime/thread proof. No standalone reader cache is a workaround.

Possible sites, ordered by preference:
1. **Original queued-waypoint braking/arrival branch** with original continuation (best if confirmed).
2. **Original next-order activation's movement-state preservation** (if that is proven to reset velocity/path unnecessarily).
3. A bounded combination of original predicates, preserving all native calls/lifecycle.
If changing those conditions requires independent route execution or mass refactoring of navigation/formation, **NO-GO** for minimal Patch A.

### Patch B — queued MOVE→ATTACK

After Patch A is understood, inspect whether native queued ATTACK is lost, delayed, or revalidated by WH3 vs old Lua. Prefer no changes if the cause is *entirely* old BSC reissue. Otherwise patch only an evidenced original queued attack transition/eligibility decision, preserving native target identity, cancel/death behavior and attack activation. Never synthesize an ATTACK command or periodically call the original attack issuer to fake smoothness.

### Optional ATTACK→EXIT MOVE→ATTACK contract

Minimum engagement time and EXIT route are product requirements, **not permission to invent a scheduler**. Analyze whether native orders/states can represent them without shadow-command execution. If they require issuing a second queue or repeatedly overriding native attack, mark **DEFERRED/UNSUPPORTED** and report the limited scope; do not hide this behind synthetic PASS.

## 3. Explicit causal decision table and feasibility

| Proven original behavior | Candidate minimal change | Feasibility |
|---|---|---|
| Terminal braking occurs before completion only for queued intermediate MOVE | Narrow original brake/arrival condition adjustment | A — preferred, still requires negative proofs |
| Successor native MOVE activates but unnecessarily resets locomotion | Narrow original activation state-preservation change | B — harder, may involve several functions |
| Independent order execution intrinsically requires full-stop or no safe successor look-ahead | Cannot safely achieve continuity by local predicate alone | C — reject minimal patch, do not resurrect Lua scheduler |
| Original queued ATTACK works without old BSC; old Lua overwrites it | Remove legacy Lua control, no Patch B necessary | A/B depending on MOVE result |
| Original queued ATTACK itself delays or drops order | Locate exact native target/activation predicate | B if bounded, C if large replacement |

**Decision authority is evidence**, not appearance from old 9.0.2 BSC logs.

## 4. Evidence ledger and 9.0.3 source discovery process

Inputs: preferred SHA-verified WH3 9.0.3 `Warhammer3.exe`; alternatively a Ghidra/IDA project/export tied to its SHA, image base, unmodified original bytes, function xrefs and caller/callee graphs. No gameplay tests to acquire static inputs.

Per site mandatory columns:
`site_id, EXE_SHA256, RVA, bytes/mask, containing_function, actual x64 ABI, object provenance, read/write fields, caller/callee evidence, branch/side effects, thread/lifetime, competing interpretation, proof grade, negative control, proposed behavior delta`.

Algorithm:
1. Verify x64 PE, exact executable SHA, image base, sections/exception unwind. Set `9.0.3/unmapped` if SHA unknown.
2. Treat 9.0.2 known constructors, candidate VTables, writer and Native MOVE/ATTACK as **xrefs seeds**, not address candidates to blindly install.
3. Recover 9.0.3 issuer/allocator and constructor/vtable identities independently. Differentiate original issue entry vs executing/tick order.
4. Classify decoded accesses to head/count as read/write/RMW; verify **root provenance**; raw offset-byte matches are insufficient. Follow write-site control dependence backward to completion and forward to retirement/activation.
5. From verified MOVE consumer, trace arrival/desired-speed/stop/path-update and queued successor discriminant. Build timeline of state changes and head writes.
6. Trace ATTACK successor activation/target validity separately and compare against normal RMB.
7. Classify H-A/B/C/D as proved/falsified/unknown. Do not invent new RVAs, signatures, vtable layouts or ABI in notes.

Evidence grades:
- `SOURCE`: what BSC source says;
- `MAP`: historical or candidate relocation evidence;
- `BINARY`: exact 9.0.3 opcode and call/dataflow evidence;
- `WINDOWS`: isolated backend/call-through fixture;
- `WH3`: final in-game confirmation.
Higher grade cannot be inferred from passing a synthetic unit test.

## 5. Stage gates and offline verification

**P0 — Freeze and scope 9.0.3.** Maintain H8 and existing 9.0.2 files unchanged. Record observed EXE SHA only as research provenance, not a promoted 9.0.3 Hook map. Research scripts/docs and static reports only; no runtime modifications. **PASS:** no old RVA automatically promoted.

**P1 — Binary producer→consumer xrefs.** Deliver graph for original creation, MOVE tick, completion, head write, retire and successor activate. Record missing links. **PASS:** each claimed edge backed by specific original instructions and exact build.

**P2 — Causal reconstruction.** Compare native queued MOVE→MOVE, final MOVE, MOVE→ATTACK and normal RMB branches. Order of brake/completion/activation documented. **PASS:** a specific defect-making branch with rival hypotheses explicitly tested against disassembly. If none found, stop rather than tune.

**P3 — Local patch contract / no-go.** For each proposed site, define preconditions, side effects preserved, exact original decision delta, native call-through, fail-closed on unsafe state; model original state semantics only where recovered. Tests: straight, 90/135/180-degree, short zigzag, i+1/i+2, target invalid/death, REPLACE, HALT, multiple units, cancellation, engagement/EXIT constraints. **PASS:** order identity, count, head progression and ownership remain original; no skipped action, queue mutation or nonqueued RMB change.

**P4 — Isolated Windows proof.** Only after P1–P3: small x64 patch carrier, secure hash/guard check and reversible/disable-safe hook; verify exact ABI, trampoline, unwind, cancellation and fault-injected partial installation. Independently isolate legacy `MH_ERROR_MEMORY_ALLOC` / `OBSERVER_MINHOOK_CREATE_FAILED` via allocation/proximity instrumentation. Avoid 16-hook legacy bootstrap by default; hook count is proof-derived, not precommitted. **PASS:** no partially enabled patch, stale trampolines or uncontrolled retry.

**P5 — Integration and one bounded WH3 acceptance.** Build proper WinX64 DLL, normal and DEBUG PACK plus source/evidence/SHA256 manifests. After all static + offline + Windows checks, execute one consolidated WH3 test matrix: MOVE→MOVE, corners, short zigzag, MOVE→ATTACK, ATTACK→EXIT MOVE→ATTACK (only if implemented), right-click REPLACE, cancel, target death, multi-unit, game exit. Mark each `STATIC`, `OFFLINE`, `WINDOWS`, `WH3` separately. No Steam publication without actual WH3 success.

### Research tooling checkpoint (2026-10-09)

Committed read-only PE/9.0.2 historical guard similarity scanner and Ghidra Jython scalar-field xref exporter under maintenance_tools/native_shift_re/, plus 9 synthetic PE/offline contract tests and separate CI workflow. These are **N1 preparation**, not successful executable disassembly, not ABI evidence and not a Native Patch. Exact EXE binary acquired and original ring pop found; **MOVE completion and terminal brake** remain P1 blockers.

### N1 exact-file static RE checkpoint (2026-10-09)

[N1_903_ORDER_LIFECYCLE_STATIC.md](N1_903_ORDER_LIFECYCLE_STATIC.md) records exact PE SHA, verified ring queue pop (`0x02F4FD10`) and five direct callers. These confirm original head/count mutation but **not** native MOVE completion/terminal braking, target handoff or safe detouring. 25/25 selected direct calls independently instruction-validated. All are static; no WH3 runtime or Ghidra integration.

## 6. Red lines / stopping conditions

- No 9.0.2 patch guard, old RVA or VTable is a valid 9.0.3 Hook without new binary verification.
- No direct writes to head/slots, no H8 Native/Lua replacement scheduler, no forced command replay or attack overwrite.
- Stop Patch A if original motion/queue architecture requires a second movement executor or unsupported raw object mutation.
- Unknown completion function, unknown ABI, ambiguous byte signature or unsafe object access => NO PATCH.
- No user-led repeated game tests to develop an unproven mechanism; real play validation comes once near the end.

## Immediate next concrete deliverable

The user-provided EXE has been analyzed with LLVM; queue pop `0x02F4FD10` and several callers have actual instruction evidence. Next: resolve state flags in `0x030433B0`/`0x03043424`, original next-order activation in `0x0304433C`, and original MOVE braking. Do not advance to a Hook based on ring pop alone.

## Links

- [N1 prior source audit](N1_STATIC_FINDINGS.md) — 9.0.2 source/map evidence only
- [Former 9.0.2 executable procedure](N1_EXECUTABLE_RE_PLAN.md) — methodological precedent, not current map
- [Target architecture](TARGET_ARCHITECTURE.md)
- [Risks](RISKS_AND_DECISIONS.md)
