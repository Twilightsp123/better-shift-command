# H8 — Native MOVE Terminal Liveness and Ownership Audit (2026-10-09)

Status: EXPERIMENTAL STATIC / OFFLINE VALIDATION ONLY. User in-game retesting is NOT required for this stage. Nothing promoted to Steam or main.

## Evidence is not a physical replay
- WH3 12:53, uid1010 generation13 captures queued ATTACK target1032 at 193000ms, records 16 ATTACK_TRANSITION_WAIT lines with ATTACK_ARRIVAL_BRAKE_UNPROVEN and no DISPATCH_ATTACK, then Native exact ATTACK is rolled back via REASSERT_MOVE at 207500ms when remaining=19.798845m. This establishes a liveness failure but does not provide every physical position.
- WH3 13:18 aborts before combat because MinHook first MOVE hook create fails on retry with MH_ERROR_MEMORY_ALLOC. The previously verified game hash and hook guards are not implicated by this error label. It is separate from Attack logic.
- WH3 12:10 route obligation deadlock is third, independent cause.

## P1 candidate: two independent ways to leave MOVE->ATTACK
1. Existing G11 coherent braking proof remains unchanged, including fast proactive timing and no new thresholds.
2. H8 physical native-MOVE terminal stall proof: only if *this exact poll* confirms the canonical current MOVE is active through Native V3, same generation, action and revision; the action is MOVE_ROUTE (never EXIT_ROUTE), its body has moved, and its physical position has remained within existing `CFG.move_idle_finish_drift_m` across at least four fresh model-time samples spanning existing `CFG.move_idle_finish_confirm_ms`. Current instantaneous observed speed must be <= existing `CFG.stall_speed`. Route progress >= existing `CFG.route_attack_min_progress`, remaining distance within same `Core.move_idle_finish_envelope` capped by the existing short-leg fraction. No prior debts and next ATTACK live/exact and immediate (policy hard gates).
3. Only then the existing T1.6 ACK transaction may issue ATTACK with reason `ATTACK_NATIVE_MOVE_STALL_TERMINAL` and terminal handoff credit; physical waypoint ARRIVAL is **not claimed**. The dispatch revalidates after draining Native journal.
4. No elapsed-time-only forgiveness. If the unit continues moving too fast or remains beyond existing bounded terminal envelope, H8 intentionally keeps the MOVE debt; different recovery design needed. Native-active i+1 H7 adoption remains available as independent positive path.

## P0 — hook initialization failure unresolved (no unsafe guess)
- Native Windows backend `platform_start_observer()` sets `attempted=true` before `MH_CreateHook`; on status9 first MOVE hook trampoline allocation failure it cleans created entries, retries 50ms, then remains attempted permanently if retry fails. No safe same-process re-init guaranteed.
- `MH_ERROR_MEMORY_ALLOC` does not identify system RAM pressure versus MinHook nearby executable allocation; byte-locked binary has not been reverse-verified at allocation site.
- Do NOT use partial Hook mode, bypass map guards, or silently retry after an unsafe trampoline/partial apply. Safe fix requires injectable Win64 MinHook backend, ownership proof, teardown audit, and Windows CI tests independent of real WH3.

## P2 — Native queue ownership contradiction unresolved (do not mislabel)
- `BridgeHost::order()` calls game's original Native order first then logs external order. Lua polls afterwards; queued Native i+1/i+2 may already execute while Lua canonical index stays on i.
- Existing rollback sends nonqueued MOVE via `issue_verified_command` and `goto_location`, hence **native tail cannot be assumed preserved**, although canonical Lua plan persists. Existing `preserved_tail=true` is a Lua-only assertion.
- H8 P1 avoids one class of eventual starvation after rollback when the actual current Native MOVE stops near endpoint. It does NOT make rollback preserve engine queue or repair early prepromotion races. Future ownership solution requires defined takeover at queue-ingestion boundary and engine-result parity tests; no ad-hoc Native suppression without that proof.

## Gates
- Source log fixture (private local, not committed): `12:53 uid1010 gen13`, `13:18 first hook`, `12:10 debt`.
- H8 pure policy: 9 independent cases (positive terminal, missing Native witness, out of envelope, progress, route debt, strict Exit, target, i+2, legacy G11 preserved).
- H8 shipped-controller synthetic Native V3 fixture: stationary terminal -> actual BSC ATTACK ISSUE + ACK, far negative, missing current Native proof, canonical i+2 negative.
- Existing H4/H5/H6/H7, old T2B early Native fail-closed, full maintenance regression, mutation, Native map+DLL byte-locked sealing.
- CI passing proves implementation consistency in synthetic fixture, NOT real WH3 behavior. No additional in-game requests until architecture phase finished.

## Runtime identity
Controller ENTER now includes additive `audit_stage=H8_P1_STATIONARY_NATIVE_MOVE_TERMINAL`; old `1.3.0` is an ABI/compatibility label, not sufficient source-commit identity. Use build Manifest source_head and controller_sha256 for exact artifact provenance.
