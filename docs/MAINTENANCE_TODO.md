# Maintenance TODO — current operational queue

This file is the **current actionable maintenance queue**. It complements `OPEN_ISSUES.md`: Open Issues records unresolved problems and promotion blockers; this file records what a maintainer should actually do next, what is blocked, and what must not be done while blocked.

Last updated: **2026-10-09**

## P0 — T2-B G1.1 WH3 runtime promotion gate

Status: **BLOCKED / DEFERRED — WH3 runtime testing is not currently available.**

Current candidate:

- branch: `maintenance/t2b-terminal-attack`
- documentation/source seal: `49c9c005d8c39cf8b5eb92cea829e50e0727f665`
- controller SHA256: `1170ecda86806a077ccbf9913e31750a0066ee968fd87db1f4f418990c7c3b41`
- offline validation: **46/46 maintenance PASS**
- core mutation harness: **44/44 CAUGHT**
- dedicated G1.1/T2-B/cache mutations: **13/13 CAUGHT**
- T2-B runtime fixtures: **4/4 PASS**

Prepared WH3 candidate artifact:

- Actions run: `37561431695`
- artifact id: `11456927365`
- artifact name: `t2b-g11-rt-tp-02-03-candidate`
- exact pack SHA256: `9e0e42bbc3f7434fc8a06fcc9d602b0a445d8f901c1e7383d5e539abd7ba6ac0`
- debug pack SHA256: `dc7f793a613325f5984a4c84f47fb99089690ff02b31ca9c6f247f6cdcf34007`

### When WH3 runtime testing becomes available

Run only the defined promotion checks:

1. **RT-TP-02 — straight Move → Attack**
   - no visible full stop before Attack;
   - no early long-distance route cut;
   - exact queued target preserved.
2. **RT-TP-03 — angled / route-fidelity Move → Attack**
   - roughly 45–90° target geometry;
   - no premature diagonal cut that erases waypoint intent;
   - no stop-then-Attack when a legal handoff exists;
   - no rollback/reassert oscillation.
3. **Route-fidelity safety check**
   - use a waypoint whose route meaning is obvious (for example, routing around an obstacle);
   - the candidate must preserve the waypoint rather than trading route fidelity for smoothness.
4. Use the debug candidate when collecting evidence and retain the resulting `script_log_*.txt`.

### While this item is blocked

Do **not**:

- mark T2-B as WH3 runtime PASS or promote it to production;
- tune new meter/fraction constants to make the offline model “look safer”;
- weaken route-debt, exact-target, `i+1`, Exit, ACK, or commit invariants;
- treat the prepared pack as release evidence merely because offline CI passed.

Allowed work while blocked:

- documentation/archival maintenance;
- analysis or offline design for later T2-MOVE;
- test-harness hardening that does not change gameplay permission;
- separate lifecycle/teardown investigation.

## P1 — T2-MOVE immediate-successor MOVE + hysteresis

Status: **OFFLINE SHADOW DESIGN ACTIVE; GAMEPLAY PROMOTION PENDING AFTER T2-B RUNTIME CLOSURE.**

T2-MOVE-A shadow work is isolated on `maintenance/t2move-a-shadow`, based on `2c2187edae771e8a5bf9b56f29b65d34786eb119`. It audits the exact `i+1 MOVE` SC6 rollback asymmetry and proves a non-authoritative pre-promotion decision-cache model. Pure Lua evidence: **20/20 fixture PASS**, **12/12 mutants caught**. The live controller and MOVE adopt permission remain unchanged. Full spec: `docs/design/T2_MOVE_A_SHADOW_20261008.md`.

T2-MOVE-B mode-specific one-poll adopt-only shadow has now been added on this isolated branch. Its model widens **only the temporal issue frontier** using one actually observed pre-promotion poll; PATH_SAFE, SC1/SC2/SC4 corridors, short adjacent legs, and SC3 debt limits are never widened. Pure Lua local evidence: **28/28 fixtures PASS, 20/20 mutants caught**. See `docs/design/T2_MOVE_B_SHADOW_20261008.md`. The shadow is non-authoritative: live SC6 still rolls back immediate future MOVE.

T2-MOVE-C transaction protocol shadow is now implemented **offline only** in `maintenance/t2move-c-shadow`. It exercises the same T1.6 `AUTHORIZED → OBSERVED → COMMITTED` call pattern with a mock Core, including STEERING_CORNER credit, PATH_SAFE route-debt creation, existing SC3 debt preservation, generation/revision/identity validation and rejection without cursor credit. **GitHub Actions run 37718568414 SUCCESS**: C fixtures **25/25 PASS**, C mutations **14/14 CAUGHT**, A/B suites, documentation contract and existing maintenance suite all PASS. The snapshot static audit reports six missing production fields; this is an explicit integration blocker, not gameplay success.

**Critical blocker before controller integration:** actual `transition_geometry_snapshot()` omits `leg`, `progress`, `route_min_progress`, `threshold`, `stall`, `cut_safe_limit` and other MOVE-specific proof fields required by A/B. A dedicated exact-current MOVE snapshot and a stable prior-debt signature are required before any MOVE adoption is activated. See `docs/design/T2_MOVE_C_SHADOW_20261008.md`.

T2-MOVE-D now supplies an **isolated controller evidence-only candidate** on `maintenance/t2move-d-evidence`. It adds the six previously missing MOVE snapshot fields, preserves SC4 escape state, captures deterministic current-block route-debt identity (debt action IDs/tolerance/waypoint/semantic_done sorted), and observes only while the Native order still exactly matches current MOVE. The snapshot is not used for permission; `adopt_window` stays hard-closed for MOVE. **D offline validation COMPLETE**: GitHub Actions run `37720282921` SUCCESS; D pure Lua **23/23 PASS**, D mutations **10/10 CAUGHT**, real-controller shadow fixtures **3/3 PASS**, A/B/C gates and existing full maintenance **46/46 PASS**. This is **observation-only**, not a MOVE adopt promotion. See `docs/design/T2_MOVE_D_EVIDENCE_20261008.md`.

**T2-MOVE-E ISOLATED OFFLINE VALIDATION COMPLETE — NOT WH3-PROMOTED.** Branch `maintenance/t2move-e-integration` now allows exact `i+1 MOVE` adoption **only in that experimental branch** after frozen D proof, A/B policy, generation/revision/lifetime/action-table identity and SC3 debt signature checks; successful adoption still requires the original T1.6 `OBSERVED → COMMITTED` transaction. GitHub Actions run `37733220962` **SUCCESS**: E real-controller cases **11/11 PASS**, E controller mutation tests **8/8 CAUGHT**, A/B/C/D regressions PASS, original maintenance **46/46 PASS**, documentation contract PASS. See `docs/design/T2_MOVE_E_INTEGRATION_20261008.md`. The T2-B branch `maintenance/t2b-terminal-attack` remains unchanged and does **not** include this MOVE permission. **No WH3 runtime evidence exists**: RT-TP-04/05 is BLOCKED/DEFERRED, just like T2-B RT-TP-02/03. Do not merge or publish this integration solely because CI passed. Next: package exact E branch source/tests as a reproducible offline archive; when WH3 is available, validate the Move→Move straight, corner, hairpin, short-leg, and route-debt cases separately before any promotion.

**T2-MOVE-F OFFLINE SAFETY HARDENING VERIFIED — NOT WH3-PROMOTED.** Follow-on isolated branch `maintenance/t2move-f-audit-hardening` (E HEAD `21417a8` parent) adds explicit V3-only provider and fresh Native unit-revision checks to exact `i+1 MOVE` adoption. CI `37819203083` reproduced two E defects (V2 acceptance and unobserved Native revision drift); subsequent CI `37820591847` SUCCESS: F real-controller **5/5 PASS**, new F mutations **3/3 CAUGHT**, existing E controller **11/11 PASS** and E mutations **8/8 CAUGHT** including a dynamic SC3 debt-signature change, A/B/C/D and original **46/46 maintenance PASS**. No movement geometry constants, Native addresses, T2-B attack policy, T1.6 commit authority or official pack changed. F is a separate offline candidate; WH3 RT-TP-02/03/04/05 remain BLOCKED/DEFERRED. See `docs/design/T2_MOVE_F_HARDENING_20261009.md`. **Next:** preserve exact F source/artifact manifest; add broader hairpin, multi-debt and concurrency fixtures if deterministically provable; defer WH3 release decisions until runtime evidence.

**T2-MOVE-G NATIVE TURNBACK ADOPTION HARDENING — ISOLATED OFFLINE SUCCESS / WH3 NOT TESTED.** G branch `maintenance/t2move-g-adversarial` starts at sealed F `206221bc`. Unmodified F fails 3/7 new real-controller adversarial tests on 180°/135° turnback and dense short-leg reversal; four control cases pass (straight chaining, 90° steering, multiple SC3 debts, two units). The accepted G repair freezes incoming-leg backtrack and existing waypoint-reach tolerance while the Native order still matches current MOVE, then denies exact Native `i+1 MOVE` adoption credit if backward steering would leave the waypoint unpaid. An initial wider change to `route_handoff_ready()` was rejected because it broke the original SC1 U-turn regression and T2-B frozen contract. The retained G revision leaves proactive SC1–SC4 untouched. GitHub Actions `37822771962` **SUCCESS**: G controller **7/7 PASS**, G mutations **3/3 CAUGHT**, all E/F and 46-job maintenance tests PASS. See `docs/design/T2_MOVE_G_NATIVE_TURNBACK_20261009.md`. **Outstanding: SC1 proactive U-turn route-fidelity policy is unresolved; do not infer it was fixed by G.** WH3 RT-TP-02/03/04/05 remain BLOCKED/DEFERRED. Next: seal exact G source/artifact, then separately review whether the proactive U-turn route credit should become a debt-preserving transition without reintroducing full stops.

**T2-MOVE-H1 READ-ONLY ROUTE-OBLIGATION SHADOW — OFFLINE VALIDATED, NOT GAMEPLAY-PROMOTED.** Isolated branch `maintenance/t2move-h1-route-obligation-shadow` starts at sealed G `5802522`. The pure `H1RouteObligation` model separates `SATISFIED`, `DEBT_PRESERVED` (necessary geometric opportunity only), and `BLOCKED`, using already-existing waypoint reach tolerance, fresh observed motion, direct successor chord, and unresolved SC3 debt geometry. H1 observes the legacy proactive ISSUE decision and caches only a diagnostic pre-promotion Native verdict; it does **not** alter dispatch, adoption, T1.6 commit, debt registration, CFG or Native. Initial CI [`37825312679`](https://github.com/Twilightsp123/better-shift-command/actions/runs/37825312679) passed pure H1 **14/14**, real controller H1 **5/5**, H1 mutants **5/5 CAUGHT**. Provenance-hardening then added H1-14 and a sixth mutation so `STEERING_CORNER_HANDOFF` alone can never count as verified arrival: CI [`37825955358`](https://github.com/Twilightsp123/better-shift-command/actions/runs/37825955358) passed expanded pure H1 **15/15**, Controller **5/5**, H1 mutations **6/6 CAUGHT**, G/E/F regressions and original full 46-job maintenance. H1 reports early 90°/180° `STEERING_CORNER` credit as a route-fidelity conflict rather than silently changing the original SC1 U-turn test. Frozen T2-B route evaluator and Core commit remain byte-identical. See `docs/design/T2_MOVE_H1_ROUTE_OBLIGATION_20261009.md`. **Next: H2 design/transaction audit, NOT immediate gameplay promotion**; prove debt lifetime across ISSUE ACK and Native adoption, devise safe behavior on chord-unpayable edges, and separately resolve legacy early U-turn semantics. WH3 RT-TP-02/03/04/05 remain BLOCKED/DEFERRED.

**T2-MOVE-H2-A PROACTIVE ISSUE→ACK FALSE-CREDIT COUNTEREXAMPLE — CONFIRMED RED, NOT FIXED.** Separate test-only branch `maintenance/t2move-h2-ack-route-credit` is based on H1 `b5020d9`. Unmodified H1 Controller real-ACK test `37827397901`: **H2-A01 180°** and **H2-A02 90°** FAIL as expected: at x=60, old P=100 still **40m away**, but ACK/T1.6 `COMMITTED` writes `ACTION_COMPLETE reason=STEERING_CORNER_HANDOFF`. Four controls PASS: near-waypoint, collinear route-debt, pending/no ACK, rejected Native ACK. H2-A intentionally keeps tests red; a separate expected-red harness validates exactly those two failures. The existing E/F/G/H1 + 46 maintenance tests remain valid. H2-B is a *separate design/implementation gate*, not covered by H2-A success. No Native/CFG/controller behavior changed; WH3 NOT TESTED. See `docs/design/T2_MOVE_H2A_ACK_ROUTE_CREDIT_20261009.md`.

**T2-MOVE-H2-B/C/D + H3 ISOLATED BEHAVIOR CANDIDATE — OFFLINE PASS, WH3 NOT TESTED.** The isolated branch `maintenance/t2move-h2bcd-h3-route-integrity` continues from frozen H2-A `a74df147`. H2-B decouples Native ACK/T1.6 execution commit from previous waypoint completion. H2-C uses H1's existing reach/chord/SC3 evidence to block unpayable proactive Move→Move issues, both in advance and after Journal drain. H2-D makes Native exact i+1 adopt consume the same frozen credit proof; issue and adopt timing envelopes remain distinct. Historical early 90°/180° SC1 steering tests are deliberately superseded only on this branch, with behavior differences documented in `docs/design/T2_MOVE_H2BCD_H3_20261009.md`. H3 adds multi-unit, 10-node, zigzag, stacked-debt, ACK rejection, revision drift, REPLACE and Native race stress. Offline CI `37830565468` SUCCESS before final packaging: H2 controller 7/7, H3 stress 9/9, H3 Native 4/4 and H2 mutants 5/5 CAUGHT; original maintenance suite 46/46 PASS. Next: seal complete source, build separate ordinary/diagnostic WH3 test PACK, and collect real WH3 logs/video. **Do not merge/publish yet.** RT-TP-02/03/04/05 remain NOT TESTED / BLOCKED.

Do not promote a standalone permissive T2-A state. Immediate successor MOVE adoption and its issue/adopt hysteresis must be implemented and promoted together. Existing SC1–SC4 Move→Move route semantics remain authoritative. T2-B G1.1 runtime RT-TP-02/03 is still **BLOCKED / DEFERRED** (P0) and must remain a separate promotion gate.

## P2 — Lifecycle / teardown stream

Status: **OPEN / SEPARATE STREAM.**

Track O-11/O-12 separately from transition-policy work. Do not mix a battle-exit/main-menu/desktop lifecycle fix into T2-B or T2-MOVE.

## P3 — Integrity / archive housekeeping

Status: **PENDING FINAL ARCHIVE SEAL.**

The root `SHA256SUMS.txt` was intentionally **not refreshed** during the T2-B documentation seal. Regenerate it only at the final archive/package-seal step, after all intended files for that seal are stable. Do not treat the older root checksum list as current T2-B evidence.

## Maintenance rule

Whenever an item changes from BLOCKED/PENDING to ACTIVE/PASS/FAILED:

1. update this file first;
2. update the corresponding entry in `OPEN_ISSUES.md`;
3. update `TEST_MATRIX.md` if a gate ran;
4. record a meaningful architecture decision/result in `DECISION_LOG.md` or `DEVELOPMENT_HISTORY.md` when appropriate;
5. run `maintenance_tools/check_documentation_contract.py`.


## P0.5 — WH3 9.0.2 H2/H3 Native test handoff

**Status: WINDOWS NATIVE COMPILE + CTEST PASS / WH3 RUNTIME NOT TESTED.** The 2026-10-09 BSC logs confirmed `OBSERVER_HOST_EXE_SHA256_MISMATCH` because the prior H2/H3 PACK embedded a 9.0.1 DLL. The completed 9.0.2 address work already existed at `maintenance/wh3-9.0.2-map-candidate`; no relocation rerun or guessed RVA was necessary. Independent integration `maintenance/t2move-h2h3-wh3-902-integration` preserves `native_maps/CURRENT` as 9.0.1 while compiling a 9.0.2 overlay with the documented 16 core hooks and Full Move/Attack VTables. GitHub Actions `37877024598`: Linux H2/H3 regression PASS, MSVC v142 + MASM Windows build PASS, Windows Native CTest **14/14 PASS**, binary 9.0.2 version/hash check PASS, and Windows-built DLL/plain/DEBUG PACK/full-source SHA256 seal PASS. **Next action is WH3 9.0.2 startup smoke**: exact target EXE hash, enable one diagnostic BSC candidate, confirm `OBSERVER_READY`/`START`/`READY`, run a normal Move/Attack capture and Quit-to-Windows clean stop. Only then rerun H2/H3 route smoothness + fidelity RT-TP-04/05 and T2-B RT-TP-02/03. Do not change gameplay movement parameters to hide a startup failure. Details in `docs/design/T2MOVE_H2H3_WH3_902_INTEGRATION_20261009.md`.


## H4S — Speed-first soft-waypoint user requirement (2026-10-09)

**Offline PASS / WH3 H4S NOT TESTED.** The real 9.0.2 H2/H3 run succeeded in starting Bridge/Observer but exhibited stop-and-go: 259 `H2_ROUTE_ISSUE_BLOCKED` and 14/20 MOVE issues after previous node completion. The user clarified that intermediate waypoints are APPROXIMATE guides and maintaining unit speed is primary; exact waypoint reach is not mandatory. On independent `maintenance/t2move-h4-soft-corner-speed`, H4S restores SC1/SC2/SC4 bounded early corner ISSUE with separate `CORNER_SOFT_ACCEPTED` semantic credit on ACK, keeping hard protections for unpaid prior SC3 debt, short next legs, Move→Attack, revision, T1.6, stale Native and i+2. G Native exact i+1 may adopt only its frozen bounded soft certificate. H4 Controller 6/6 PASS, Native 4/4 PASS, mutations 4/4 CAUGHT, original maintenance PASS; WinX64 plain/DEBUG packs use the **unchanged** 9.0.2 Native 1.0.18 DLL from v142 CTest 14/14 run `37877413553`. **Next: real WH3 speed, corner trajectory and Native rollback/reassert evidence.** No Steam release or branch merge. See `docs/design/T2_MOVE_H4_SPEED_SOFT_20261009.md`.

## H5 WH3 9.0.2 real-log audit — 2026-10-09

Evidence: `script_log_091026_1144.txt` (H4S). Bridge/Observer PASS; 4 soft corners ISSUE/ACK in 300–400 model-ms; 11 predictive MOVEs; no CONTROLLER_FAIL, MOVE_AFTER_NODE_COMPLETE or NATIVE_IDLE_ROUTE_FINISH. All 80 H2 veto observations preceded the corresponding SC issue-open window (0 late-window vetoes). Three initial Native rollback races remain: one i+1 without frozen prepromotion proof, two i+2 canonical overruns. One separate 900ms-contact-stall Exit reassert. Smoothness remains UNASSESSED without same-route video. H5 isolated branch `maintenance/t2move-h5-runtime-reconcile-audit` adds logging and two negative Native Controller fixtures without loosening policies or changing 9.0.2 Native DLL. See `docs/design/T2_MOVE_H5_RUNTIME_RECONCILE_AUDIT_20261009.md`. No release promotion.

## H6 candidate — bounded route-guide near-pass
- [x] Add per-step forward-plane near-pass retirement after Native ACK; six positive/negative fixture gates.
- [ ] Real WH3 replay of uid1006 12:10 9-node route and video confirmation, especially no step loss/stalls.
- [ ] Address independent Native i+1/i+2/i+3 pre-promotion separately; H6 does not fix it.


## P0 — H7 observed WH3 Shift Attack near-terminal regression (2026-10-09)

User `script_log_091026_1253.txt` from WH3 9.0.2 / H6 controller shows Shift ATTACK input accepted but repeated `ATTACK_ARRIVAL_BRAKE_UNPROVEN` during the near-terminal MOVE, a `NATIVE_SUCCESSOR_ROLLBACK` at model_ms=69800 after native ATTACK advanced, and BSC only dispatched at 75700 after Native idle route-finish. A separate later Attack did dispatch. **Gameplay regression: CONFIRMED severe delay/rollback; not total input loss.**

Isolated fix candidate on `maintenance/t2b-h7-attack-stall-recovery` based on H6 `d10d9bd55c1199e705c20fb458a7472371cd2fd1`: strict current MOVE real-progress + bounded stationary terminal envelope alternate to G1.1 monotone deceleration, with exact-target, i+1, prior-debt, EXIT and T1.6 ACK intact. **NOT WH3 VALIDATED / NOT RELEASED.** One coordinated Lua/static/full controller test and WH3 RT-TP-02/03 + H6 MOVE regression check are required. Do not patch Steam pack or release on GitHub source checks alone. Evidence and risk: `docs/fixes/H7_SHIFT_ATTACK_TERMINAL_STALL_REGRESSION_20261009.md`.
