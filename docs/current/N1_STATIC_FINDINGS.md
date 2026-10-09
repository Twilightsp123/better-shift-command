# N1 — Native Shift Behavior Patch: first static evidence audit

**Date:** 2026-10-09  
**Working branch:** research/n1-native-shift-behavior-patch-20261009  
**Parent docs HEAD at branch creation:** 235fc6b8956332e99acfaeb88d1b3b658de35ad3  
**Historical H8 baseline:** e711e716f2411599d75184618fc1ee5cb85bcd54  
**Target binary:** WH3 9.0.2 Warhammer3.exe SHA256 fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785

## Executive finding

The repository exposes the **order creation/publication path** and an **optimistic read-only view of the active order**, but contains no verified evidence locating the **original WH3 movement-terminal braking function, MOVE-completion predicate, OrderHead writer, retired-order destructor, or successor activation**. Therefore N1 has identified reliable **research entry points**, not an authorized original-behavior patch site. N2–N4 cannot be marked ready. The target EXE and/or target-version disassembly/Ghidra project are unavailable in this audit; do not assign new RVAs.

**Architecture fixed:** WH3 remains owner of its own Shift queue and MOVE/ATTACK execution. Native DLL is only a version-guarded modification/instrumentation vehicle. H8 Lua replay/reassert/rollback is not the implementation plan.

## Evidence grading used in this report

- **S — source-observed:** directly in versioned BSC source, including declarations and its own observation behavior. This is **not** proof of the engine's undocumented ABI.
- **M — map candidate:** 9.0.2 relocation map assertion (guard/relationship/derived type). Not runtime promoted and not independently re-disassembled here.
- **X — WH3 executable-disassembled:** opcode-level xrefs, control flow, object writes and ABI from matching EXE. **None newly established in N1.**
- **W — WH3/Windows observed:** controlled executable/runtime correlation. **None newly performed in N1.** Prior log references remain history.

The 9.0.2 map's L1–L4 relocation labels describe strength of an **address relocation**, NOT X-level proof that the site owns Shift queue progression.

## Grounded source and candidate anchors

| Anchor | 9.0.2 candidate RVA | What this audit can support | What it does not support | Grade |
|---|---:|---|---|---|
| Native MOVE | 0x030351AC | Intercepted in platform_windows.cpp:100 and BridgeHost::order; source wrapper forwards original trampoline, observes result/allocated slot | Not a per-frame MOVE executor or terminal arrival predicate | S + M |
| Native ATTACK | 0x03033544 | Symmetric order issue/interception; captures target identity | Not native queued MOVE→ATTACK activation or target-lifetime rule | S + M |
| allocator | 0x02F53128 | BridgeHost::allocate observes allocation when p == root+0x278; tracks returned slot | Not proof of consumer or removal/destructor | S + M |
| halt | 0x0301C5E0 | BridgeHost::halt passes through and records external HALT | Not proof of normal RMB replace path | S + M |
| publish MOVE / ATTACK | 0x01CAFDDC / 0x02DF3410 | BridgeHost::publish forwards original; candidate map declares calls to writer_begin/finalize | Not queue progress or steering update | S + M |
| Lua MOVE / ATTACK ingress | 0x02ED6404 / 0x02ED5C9C | Adapter hook exists; forwarded via BridgeHost::binding | No proof normal player Shift input goes through these Lua APIs | S + M |
| packet handlers | 0x02ECFCD0 / 0x02ECF79C | Candidate map declares both call selection 0x02F04F70 | No verified packet-handler → queue-head writer edge | M |
| base/full MOVE constructor | 0x0300B518 / 0x0300BDC0 | Listed in 9.0.2 map's derived constructor set | Not MOVE per-frame update function | M |
| ATTACK constructor | 0x0300B8C4 | Listed derived constructor | Not target execution/queued handoff function | M |
| MOVE / ATTACK VTables | 0x03913618 / 0x03912988 | Map derived identities used by BridgeHost::outcome and EvidenceProbe::active_order | Not evidence of a virtual completion slot; not universal MOVE variants | S + M |
| **original progress/completion** | **unknown** | No repo-proven RVA/ABI/guard | Must find actual engine write and edge | OPEN |

Other mapped core hooks (writer_begin/finalize, copy, stage, selection, free) observe packet provenance, not confirmed queue advancement. Guard bytes, byte-relocation masks and callgraph relations are recorded in native_maps/candidates/wh3_9.0.2_fec656f4.json; never transplant them to a guessed progress Hook.

## Partial source-observed graph (not a WH3 execution callgraph)

    candidate publish_move / publish_attack
       -> candidate writer_begin / writer_finalize  [M: map relationship]
       -> packet serialization / handler / selection [M: separate reported relation]
    candidate Native MOVE / Native ATTACK
       -> BridgeHost::order -> original native trampoline [S: wrapper around engine code]
       -> BridgeHost::allocate during scoped issue [S: observed allocations]
       -> BridgeHost::outcome reads allocated slot +0x18 VTable/+0x20 sequence [S]
    later: EvidenceProbe::active_order(root)
       -> read count +0x2F88, head +0x2F8C, slot at +0x288 + head*0x120 [S]
    --------------------------------------------------------------
    ORIGINAL per-frame MOVE update?             [UNKNOWN]
    ORIGINAL terminal speed/braking decision?    [UNKNOWN]
    ORIGINAL completion -> OrderHead write?      [UNKNOWN]
    ORIGINAL order retire -> successor activation?[UNKNOWN]
    ORIGINAL queued MOVE -> ATTACK handoff?      [UNKNOWN]

**Important:** these rows are separately observed components, **not** an asserted end-to-end engine call chain. In particular no bridge from producer/slot creation to original consumer has yet been demonstrated.

## Exact source findings / negative proofs

1. src/native_bridge/include/wh3/bridge_host.hpp:13–25 declares NativeOrderFn as `uint32_t(void*,uint32_t,void*,uint8_t)`, NativeAllocatorFn as `void*(void*,uint32_t)`, NativePublishFn as `uint32_t(void*,void*)`. These are the **existing detour interface's expectations**, not independently reconstructed WH3 9.0.2 ABI proof. Require x64 register use, stack/unwind and original call-site validation before patching.
2. src/native_bridge/src/bridge_host.cpp:339–387 shows `BridgeHost::order` calling the original trampoline at 361; its `outcome` at 279–293 identifies the issued order from the allocated slot, and uses low AL as the accepted flag. Nothing here performs native order-completion advancement.
3. src/native_bridge/src/bridge_host.cpp:388–390 shows the allocator hook's condition `p == root+0x278`; this is a **producer observation**. It is not evidence that the same function updates movement state.
4. src/native_bridge/src/evidence_probe.cpp:57–85 reads root fields twice and compares count/head/type/sequence/payload. This is an **optimistic double-read**, NOT a lock, fully atomic snapshot or safe write protocol. It can fail or miss an ABA state change; do not write OrderHead, modify slot data or assume queue lifetime from it.
5. src/native_bridge/src/platform_windows.cpp:445–555 verifies target SHA/guards, creates 16 MinHook detours and authorizes legacy V3 issuing. This is **legacy observer/issuer bootstrap**, not a direct Shift behavior patch. It also contains the previously observed MH_ERROR_MEMORY_ALLOC first-hook failure path.
6. Do not mistake `state_transition_hook` for original Shift queue advancement: platform_windows.cpp:119–127 and bridge_host.cpp:670–762 tie it to optional **Smart Guard Pursue/TakeUpPositions** filtering, not general queued MOVE completion. 9.0.2 `smart_guard` optional RVA 0x030E319C is **staged disabled**; the function name is misleading for N1.
7. evidence_probe.cpp additionally contains quarantined Entity/MovementComponent assumptions at offsets +0x18 etc. They are not adopted here. Only the top-level active-order reader is relevant as a *read-only diagnostic* seed.

## Reverse-engineering worklist (requires matching EXE/disassembly)

**R1 — identify issuer, consumer and mutation xrefs separately.** Open exact SHA-verified WH3 9.0.2 binary in Ghidra/IDA; record image-base convention. Revisit mapped constructors and two native order entry sites, documenting actual prologue, callsites, parameter flow and call edges. Use cross-references to `root+0x2F88`, `root+0x2F8C` and `root+0x288` to classify **reads vs writes**. The literal offsets alone are not unique signatures. Retain instruction address, containing function and reachability context for each.

**R2 — follow OrderHead writers.** Trace stores to head/count and called helpers backwards to the completion predicate, and forwards to object retire/destructor and successor activation. Determine whether head increments, head resets, count shrinks, ring-buffer compaction or pointer changes are separate events. Check for queue updates on normal REPLACE/HALT and cancel. Do not assume a named ShiftAdvance function exists.

**R3 — follow full MOVE object's runtime dispatch.** Inspect method xrefs through full MOVE VTable and other MOVE subclasses, distinguishing constructor/destructor/serialize from tick/update/completion. For likely per-frame movement decisions, track approach-speed/arrival/steering writes and whether queued successor changes the branch. Prove whether braking is before or after completion/head write (or independent).

**R4 — follow native ATTACK successor path.** Identify target validation and actual activation of queued ATTACK after MOVE, separately from H8 Lua policy rollback. Trace normal right-click attack, failed/dead target, interrupt and exit movement for negative controls.

**R5 — prove locality before proposing any hook.** For a candidate, store function start RVA, exact/masked original bytes, ABI/callers, SSA or disassembly evidence, thread/lifetime context, queue-shift discriminator, fall-through and fail-closed strategy. Explicitly reject candidates shared with normal RMB unless an original conditional distinguishes safe behavior.

For each result update an evidence row: `site_id | exe_sha | RVA | instruction range | read/write object | branch condition | callers | successors | original bytes/mask | ABI | proof S/M/X/W | alternative explanation | reproduction artifact`. Zero new entries may be promoted from a mere guess.

## Current hard dependency / acceptance gate

The repository source and candidate map **do not contain the target PE bytes or a 9.0.2 Ghidra/IDA analysis** in the materials accessed for this audit. This prevents original X-level xref/dataflow findings. A matching user-owned EXE or a saved Ghidra project/disassembly export (with hash + image base and relevant xrefs/decompilation) is necessary for R1–R5. No new game test is needed to prepare it.

**N1 status:** repository source/map triage COMPLETE; true original-code RE **BLOCKED ON MATCHING EXE/DISASSEMBLY**. N2 causal design, N3 differential behavioral simulation and N4 runtime patch are NOT authorized.

## Reproducible, limited static checks performed

- Read all nine docs/current files from parent HEAD and searched for unqualified `Native Transition Owner`, `Single Transition Authority` or `BSC controls native queue advancement`: **0 matches**. Existing documents already reject the obsolete architecture.
- Compared Git blob SHAs for platform_windows.cpp, bridge_host.cpp, evidence_probe.cpp, bridge_host.hpp and 9.0.2 candidate map to frozen H8: **5/5 identical**.
- Inspected candidate map: 16 required core hook descriptors, 9.0.2 target EXE hash, derived MOVE/ATTACK VTables, unpromoted static status. These checks establish *consistency of text/material*, NOT executable ABI correctness.
- This environment has no working GitHub network access from the local container and no WH3 EXE. No MSVC compile, MinHook run, CTest, Ghidra disassembly or WH3 validation has been performed here.

This stage is **research-only**: no Lua, C++, native address map, DLL or PACK was modified.
