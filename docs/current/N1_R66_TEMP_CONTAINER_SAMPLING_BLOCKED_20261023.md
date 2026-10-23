# BSC R66 — Temporary candidate-container lifetime, offline-only observation gate (2026-10-23)

**Status:** EXACT EXE STATIC ONLY; no live game run, no Hook, no gameplay patch.

## Version gate and independently verified original instructions
User original WH3 EXE: SHA256 `9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496`, size 232531920 bytes; ImageBase `0x140000000`. The local R66 offline verifier matched **21/21 whole instructions, 6/6 direct E8 destinations, 5/5 RIP-relative global identities** against the actual original EXE; **22/22 unittest PASS**, including one real-EXE case (the rest synthetic or offline protocol checks). No native game runtime validation.

## New original-code finding: temporary module-addressed candidate container is cleared
- `0x03102E14` references the same fixed module-relative container `0x04367228` passed as the candidate generator's sixth argument to `0x0312AAC4` at `0x03102E38`.
- The converter reads count at `0x0436722C` and the record pointer at `0x04367230`; indexing uses stride `0xD0` and invokes `0x030CC8E4` for each candidate at `0x03102F1A`.
- `0x03102F42` references the original container again, and `0x03102F49` calls `0x03107B34`.
- The callee loads count at `0x03107B43` and record pointer at `0x03107B49`, iterates by `0xD0`, calls a subobject cleanup at `0x03107B5D`, then clears `[container+4]` at `0x03107B6E`. It does not itself zero `container+8`.
- This verifies code-level cleanup on the traced branch, NOT proof of thread exclusivity, all-return cleanup, object destruction of the record pointer, or player Shift execution frequency.

**Consequence:** post-return Lua polling cannot recover a historical selected candidate from this count; unsynchronized reads while generation and cleanup occur do not establish atomicity. The container is addressed through a module-fixed RIP reference, not a `UnitRoot` field in these instructions. Thread-local gating/locks and per-invocation ownership remain unproved.

## No unsafe live capture
R49's roster double-read and timing budget, R50's monotonic clock, and R51's BattleManager phase/model-time gate do NOT constitute a native worker-thread barrier. R66 rejects turning them into a live candidate reader. No memreader Hook or DLL is installed, and users are not asked to run tests. Any future native read-only site first requires thread and member lifetime, ABI and unwind preservation, safe record identity and bounded publication/rollback proof.

## Artifacts and strict evidence labels
The separately delivered `BSC_R66_TEMP_CONTAINER_LIFETIME_OFFLINE_GATE_20261023.zip` contains `verify_r66_static.py`, `r66_trace_contract.py`, `test_r66.py`, disassembly and actual test output, plus R65. **This commit is documentation-only:** that separately delivered ZIP and scripts are not asserted to be uploaded in this GitHub commit. In the offline trace validator, even a structurally complete synthetic sequence is only `OFFLINE_SCHEMA_VALID` / `WORLD_GOAL_CLAIM_UNVERIFIED`, never actual native causality.

`root_cause_proven=false`; `selected_side_candidate_proven=false`; `worker_quiescence_proven=false`; `live_probe_authorized=false`; `native_gameplay_patch_authorized=false`; `main_unchanged=true`.

**Bounded next decision:** do not keep recursively wandering side-angle vtables. Check at most a single native call boundary if it can establish within-thread selected-record provenance; otherwise transfer priority to typed member world-goal versus steering/integrator coherence and retain blocked live-probe status.
