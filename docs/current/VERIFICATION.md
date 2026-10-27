# BSC — corrected verification and evidence gates

**First read [PRODUCT_CAUSE_CORRECTION_20261010.md](PRODUCT_CAUSE_CORRECTION_20261010.md).** The vanilla Shift MOVE issue is **asynchronous individual soldiers within a unit arriving/turning into one another**; native full-stop at intermediate waypoints is **not** an established defect. MOVE→ATTACK pausing was a legacy **Lua Controller** regression.

## Binding proof standards after real V3 capture (2026-10-10)

[N1_903_PROGRESSIVE_SHIFT_TURN_REAL_BASELINE.md](N1_903_PROGRESSIVE_SHIFT_TURN_REAL_BASELINE.md): **DEFECT EXISTS = PASS**. At 35–43 s of actual original queued MOVE on one unit, centroid motion direction progressively swept ~179°, while member spacing stayed <1.0 in 29 of 40 frames; ordinary MOVE had 0/139 such frames in this recording and Shift 85/194. This is *observed within-unit crowding during gradual CA turns*, not a demand that CA move through 180° in one step. Do not require identical normal RMB path geometry to accept the reported defect. Do not make the user re-prove it.

**PATCH SITE = OPEN:** Need x64 instruction/dataflow showing candidate original target/phase/steering policy affects actual execution. V3 active MOVE was `0x03025D70`; the independent `0x0302DB44→0x030D5490` fanout was not hit, so it is not safe to patch mode3 grid logic based on this capture. **PATCH EFFECT = OPEN:** only a later before/after test of the SAME original queued Shift bend will establish improvement; preserve the CA progressive turn path and all normal order semantics. An exact normal-right-click geometric match is NOT a prerequisite.

## Evidence tiers

- **STATIC:** exact-file disassembly, original function/dataflow, group/formation slot and per-soldier pointer provenance, ownership/ABI. Native ring pop or route-processing instructions alone do not establish model-level behavior.
- **OFFLINE:** only evidence-derived differential tests of a localized original engine predicate; synthetic model tests cannot prove actual soldier formation quality.
- **WINDOWS:** exact-hash guarded runtime patch installation, ABI, call-through, fault cleanup and disable/quit safety; never silently retry forever.
- **WH3:** one consolidated final in-game test. Required to assert that *soldier models* turn together better, avoid intra-unit crowding, or that Lua regression is absent.

## Static and offline regression matrix

1. **Formation allocation:** trace one unit MOVE command through original formation target/pivot/slot assignment to individual soldier destination and turn/arrival logic. Ensure same-card soldier identity and model lifetime.
2. **Model phase coherence:** same unit's leading vs trailing soldiers on straight, 90°,135°,180° turns, dense short zigzags; verify native branch invariants for early turn/target promotion vs mixed model phases.
3. **Blocked/late model cases:** path obstruction, variable model speed, collision/avoidance, incomplete formation, terrain and casualties; localized patch must not deadlock whole unit waiting for an absent model or ignore route bends.
4. **Formation semantics:** maintain unit facing, relative slot assignment, steering/turn ability, collision behavior and recovery, without implementing our own physics solver.
5. **Queue invariants:** original head/count, sequence/identity, i+1/i+2, future tail, CANCEL/REPLACE/HALT and non-queued RMB remain engine owned; do not inject extra MOVE/ATTACK.
6. **Lua attack regression isolation:** with old BSC control reissue/rollback disabled in new mode, original MOVE→ATTACK activation/target identity cannot be overwritten by BSC. Separate original-engine ATTACK Hook needs independently evidenced native defect.
7. **Optional ATTACK→EXIT→ATTACK:** if implemented by proven native semantics, check engagement minimum, exit route, target viability and cancellation; otherwise mark DEFERRED rather than spoofing commands.
8. **Lifecycle/Win64:** thread ownership, reference counting, entity lifetime, model/formation restructuring, MinHook allocator failures, partial installation and quit; do not automatically require legacy 16-hook host.
9. **Fail closed:** unsupported EXE, missing ABI, invalid formation state or disabled patch preserves original WH3 behavior; no half-patched engine.
10. **Historical counterexamples:** H8 12:53 rollback and prior Lua route debt remain regressions to prevent in *new BSC*, not evidence of native model-level crowding mechanics.

## Final WH3 physical acceptance (only once after prior gates)

Observe and record soldier-level relative position, headings, assigned slot deviation and crowding in one card before/at/after queued guidepoint turns. Distinguish mixed soldier headings from legitimate temporary differential turning caused by obstacle avoidance. Aggregate unit velocity alone is insufficient. Test no extra pause/reissued commands in MOVE→ATTACK with legacy Lua Controller absent, then REPLACE and unit combat/cancel. Report STATIC/OFFLINE/WINDOWS/WH3 status separately, plus source, DLL/PACK and SHA manifest only after they actually exist.

**Current status:** N1 model/formation execution path unknown; no patch-ready exact RVA/ABI, no Windows or WH3 behavior pass. No repeated user gameplay testing during research, no premature Steam publication.


## 2026-10-24 — R74 Group roster writer verification

STATIC ORIGINAL EXE SHA256 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496: 88/88 instruction/opcode starts with GNU objdump, 12/12 direct E8, 9/9 PE UNWIND, 4 typed VTable entries. OFFLINE: 24/24 local tests including exact EXE and adversarial synthetic interleave. PUBLIC CI only focused 45 pins and 12 E8; private original EXE skipped. WINDOWS IN-GAME / WH3 GAMEPLAY: NOT RUN. Overlap, member identity generation and causal repair: NOT PROVEN. No Hook authorization. Complete R74 ZIP kept outside GitHub without licensed binary.


## 2026-10-26 R75 evidence grade and stopping gate

CURRENT EXE SHA256 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496: **17/17 decoded direct E8 call sites**, matched raw bytes, exact call destination, PE exception/unwind owner, GNU objdump instruction start. Local Python 21/21 including two full matching-EXE tests; synthetic schedule has no runtime evidentiary grade. GitHub public CI checks manifest and negative fixtures and SKIPs original game EXE. No Windows WH3 Hook or gameplay validation. The R75 ZIP contains complete local source/disassembly/evidence and R74 history. Neither no-race nor race is proved from these observations.


## 2026-10-26 R76 evidence / phase gate

EXACT PRIVATE EXE (9bd58c63...f42be496): 112 whole instructions + GNU objdump starts, 9 E8, 7 Jcc, 6 PE UNWIND owners, 2 typed member VTable slots. 27/27 local unittest including actual EXE+objdump; no EXE 25 PASS / 2 SKIP. PUBLIC GitHub subset: 44 pins, 8 E8, 5 conditional branches, 2 typed slots. Real game WH3 instance / Windows Hook / gameplay repair: NOT TESTED / NOT AUTHORIZED. Local full offline ZIP contains disassembly and full test logs, excluding the EXE.


## 2026-10-27 R77 — current build formation index + geometry test grades

**Original EXE static:** exact SHA 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496; 66 exact whole decoded opcode starts, 9 E8 destinations, 3 PE unwind boundaries, 1 ordinary member vtable slot. **Offline synthetic:** 3×3 grid negative controls for linear 180, 90+90, rigid 180, per-member phase offsets and kinematic R/H; 32/32 local tests including 2 private original EXE tests; public CI skips both without EXE. **Not achieved:** queued Shift hit in this A branch, specific strategy mode, final world goal same as record, actual member motion traces, game repair. ZIP kept out of GitHub (without game EXE). No in-game Hook authorized.


## 2026-10-27 R78 typed A Packet physical position chain

Private EXE SHA 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496: 118 whole opcodes and llvm-objdump starts, 16 relative E8, 11 PE unwind functions, 3 constructor-linked member vtable slots, 36/36 local unittest including original EXE. Public CI includes 39 focus pins, 12 E8, 10 PE funcs and 3 virtual methods; original EXE case SKIP. Grade EXACT_EXE_STATIC_ONLY, NOT actual queued Shift trace, no safe Hook or gameplay patch. Full ZIP delivered separately without EXE.


## 2026-10-27 R79 nav goal provenance verification

Private matching EXE SHA256 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496: 98 original whole opcodes AND llvm-objdump true instruction starts; 11 PE UNWIND function bounds; all 8 direct E8 call sites to setter 0x0311E5DC (7 owners), PE float 0.01f. Local 34/34 tests including exact binary. Public GitHub subset: 31 pins, 8 E8, 11 function bounds; original licensed EXE SKIP. Synthetic dedup protocol cannot claim gameplay. Full offline ZIP holds remaining pins/disassemblies plus previous R78. No Hook or gameplay patch authorized.


## 2026-10-27 R80 original EXE goal selector provenance

EXE SHA256 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496, ImageBase 0x140000000: 98/98 original machine instructions and llvm-objdump instruction starts, 8/8 E8, 10/10 Jcc, 5/5 PE unwind ranges; 37/37 local tests including original licensed EXE and re-disassembly. Public CI covers focus 58 sites / 6 calls / 3 Jcc / 5 PE functions; private EXE skipped. No WH3 runtime, safe Hook or gameplay patch. Complete archive R80 ZIP includes local audit and R79 history without game binary.


## 2026-10-27 R81 exact original EXE context provenance and negative aliases

Original Win64 EXE sha256 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496: **85/85** whole instruction bytes and llvm-objdump start sites, **5/5** direct E8, **9/9** PE unwind functions, **33/33** local unittest including original EXE and re-disassembly. Public GitHub evidence contains 68 focus pins/5 calls/9 owner intervals; licensed game EXE case SKIP. No actual Shift same-generation instance or game Hook proof. Full R81 ZIP and nested R80 history delivered separately; never distribute licensed EXE.
