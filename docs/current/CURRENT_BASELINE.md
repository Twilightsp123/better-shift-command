# Baseline and Evidence — what is proven

Date: 2026-10-09. Baseline: maintenance/t2move-h8-terminal-liveness-static @ e711e716f2411599d75184618fc1ee5cb85bcd54. New NQTR docs branch is not a gameplay branch.

## Program sources
- source/better_shift_command.lua and src/better_shift_command.lua: mirrored Lua Controller; src/better_shift_command_selfcontained.template.lua must agree for constrained functions.
- src/native_bridge/src/platform_windows.cpp: 16 mandatory, guarded Windows x64 MinHook detours and lifecycle.
- src/native_bridge/src/bridge_host.cpp: native order capture, identity gates, journal, native issue and command publishing.
- src/native_bridge/src/evidence_probe.cpp: read-only exact current Native order view, NOT a proven queue advancement API.
- native_maps/candidates/wh3_9.0.2_fec656f4.json: 9.0.2 static candidate, target EXE SHA fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785. native_maps/CURRENT still points to 9.0.1.
- 9.0.2 unchanged tested Native DLL SHA256 6abf064f2655b4c94f7791476643b0752654732a530ea9d6ad1aa3ffd80327e9. Source/CI provenance: H8 Actions run 37889300096; artifacts not Steam production.
- Legacy maintainer metadata may still say 9.0.1 or T2-B current; its historical accuracy does not mean it describes the H8 construction baseline.

## Known runtime evidence
- 2026-10-09 12:53 WH3, uid1010 gen13: queued Shift ATTACK was captured; G11 arrival brake permission did not open; Native exact ATTACK subsequently observed and rolled back to a nonqueued MOVE. The captured action list survived in Lua; real native queue-tail preservation was NOT proven.
- 2026-10-09 13:18 WH3: MinHook first MOVE hook failed with status=9 MH_ERROR_MEMORY_ALLOC on retry; Controller never reached Observer READY. Exact cause of allocation failure not yet proven; do not equate with low system RAM.
- 2026-10-09 12:10 WH3, uid1006: unpaid route guide debt blocked a later MOVE. H6 near-pass fix was a conditional hypothesis; real crossing coordinates are incomplete in the log.
- Native future i+1 can become active before Lua caches a pre-promotion proof, and i+2 may race ahead within one sample; earlier reconciliation applies nonqueued MOVE reassert.

## What H4–H8 actually demonstrate
- H4 soft corner, H6 near-pass, H7 exact Native ATTACK adopt and H8 stationary terminal liveness have synthetic controller/CI passes, not complete WH3 smoothness proof.
- H8 introduced an additional proactive ATTACK lane for physically stable, exact-current Native MOVE near its bounded endpoint, preserving G11 and hard guards.
- All H4–H8 changes are *interim candidates*, not reasons to preserve the dual-controller architecture when NQTR replaces it.

## Fixed compatibility and safety
- 16 mandatory core hooks; physical evidence remains QUARANTINED and optional hook pathways disabled.
- C++ host and Lua currently share authority to issue commands; correct long-term responsibility split is NOT established.
- Actual 9.0.2 Native dll/build map has been used in earlier WH3 runs, but status9 shows bootstrap is not 100% reliable across sessions.
- Old development journal, SC/T1/H* policy tuning tables and D1 MCT design were frozen in docs/past_doc; inspect them only for a cited failed assumption or fixture origin.
