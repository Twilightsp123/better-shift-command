# Verification — Direct Patch of WH3's Original Shift Functions

This program must prefer **deterministic offline and isolated Windows evidence**. No 'try ten games and tune until it seems okay' methodology.

## Evidence tiers
- STATIC: source / EXE disassembly + guard/callgraph / semantic claims; may show a candidate, cannot prove runtime.
- MODEL: differential fixture built from *proven original WH3* movement/completion/attack decision paths; cannot substitute an invented new BSC order scheduler.
- WINDOWS: controlled Win64 fixture using actual v142/MASM Native Bridge/hook backend; proves ABI, atomic lifecycle, rollback/teardown under injected faults.
- WH3: one bounded smoke and acceptance matrix once architecture is coherent and Windows gates all pass. Required for real geometry, speed and compatibility claims.

## Deterministic queue fixtures (minimum)
1. Original Shift queue append/REPLACE unchanged; no alternate queue in Lua/C++. Validate that only original engine decisions are patched.
2. First/last MOVE, exact i+1 and i+2 promotions; duplicate callbacks; ACK reject/timeout; engine seq wrap; missing/mismatched unit lifetime/revision.
3. Original native MOVE desired speed/brake decision, arrival state and next-order activation vs patched branch: straight, 90, 135, 180, U-turn, zig-zag, 5m legs. Native queued tail and engine order identities unchanged.
4. Original native MOVE→ATTACK handoff when target lives, dies or changes; patch cannot rely on Lua G11, ACK/reassert or independent MOVE/ATTACK issuing. Test non-Shift RMB unchanged.
5. ATTACK→EXIT MOVE→ATTACK: 3s minimum engagement, exit proof, cancellation, target no longer viable, no phantom re-engagement.
6. Concurrent units and mixed native/controller origin; queue append while transaction pending; interrupted battle; restart.
7. Memory allocation failure before any hook, partial create fail at each of 16 sites, partial apply fail, stop/resume and process-restart-required policy; 9.0.2 guards still intact.
8. Native queue contents **before and after** a transition, not only canonical Lua-plan array; no silent tail destruction.
9. Replay actual observed 12:53 Attack rollback and 12:10 debt deadlock as minimized modeled counterexamples; annotate missing coordinates rather than invent them.
10. Native original-code pass-through oracle: when patch disabled, unsupported or unsafe, engine original behavior and order objects must match baseline. No Lua reissue/rollback, no second Native dispatcher.

## Promotion sequencing
1. No changed source/Native until a tested model names the exact queue authority.
2. All new unit tests and frozen H4–H8/old CorePath contract tests PASS; archived D1 tests are historical compatibility, not current design acceptance.
3. Windows v142 + MASM binary, guarded Hook install with 14/14 existing CTest minimum and new fault-injection suite, deterministic pack manifest/hash, no changes to 9.0.2 map without proof.
4. WH3 once at final integration: Observer READY; repeat core route, Shift ATTACK and EXIT with known units; check Native queue/visual result; Quit-to-Windows teardown.
5. Release only on explicit approval; CI does not equal gameplay acceptance.

## Failure reporting
Use PASS / FAIL / INCONCLUSIVE / BLOCKED separately for (1) program correctness, (2) Native hook initialization, (3) actual in-game physical motion, (4) queue preservation. Never report 'preserved_tail' without specifying Lua or Native.
