# Maintenance TODO — current operational queue

This file is the **current actionable maintenance queue**. It complements `OPEN_ISSUES.md`: Open Issues records unresolved problems and promotion blockers; this file records what a maintainer should actually do next, what is blocked, and what must not be done while blocked.

Last updated: **2026-10-08**

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
