# Decision Log

## D-20260927-01 — Quarantine physical Entity evidence

**Decision:** EntitySnapshot, Component layout, Alive virtual call, and ContactPair owner mapping are not release prerequisites for BSC CorePath RC8.

**Reason:** the BSC behavior audit showed command/ACK/SC6 identity is the authoritative transition source; Center-A2 route semantics already prevent physical evidence from vetoing route completion. The physical layer was inherited from Evidence V3 and had acquired release importance without equivalent provenance. A key `Entity+0x18` proof was retracted, and RC7 runtime could not find the presumed component/backref pair.

**Consequence:** production capability bits for physical evidence are false; production physical APIs fail closed; explicit diagnostic APIs/research source remain available for future reverse work.

## D-20260927-02 — ContactPair is optional, not core

**Decision:** mandatory hook count is 16. ContactPair is a separate optional static site and is staged disabled.

**Reason:** current SC1–SC6 command path and SC5 CorePath fallback do not require the mid-function ContactPair hook. Removing it from authorization lowers update/ABI risk without deleting research.

## D-20260927-03 — Safe stop only on desktop quit

**Decision:** keep hooks resident across normal battle completion. Disable all bridge-owned MinHook detours only when `button_windows` is clicked.

**Reason:** RC7 showed successful disable, and leaving allocator/free hooks live into process teardown was a plausible exit-hang source. However, a one-shot `platform_stop_observer()` cannot be used on every battle Complete because subsequent battles in the same WH3 process must still work.

**Trade-off:** cancelling the desktop-quit confirmation after the click can leave BSC stopped until WH3 restart. This is intentionally safer than carrying hooks into process teardown.


## D-20260927-04 — Current-state docs outrank historical narrative

**Decision:** maintenance handoffs use an explicit document authority/read order. `DEVELOPMENT_HISTORY.md`, Native changelogs, and archives preserve history but cannot override current Architecture/Issues/Assumption/Test/Build-Map documents. Bare `RCx` labels are prohibited in new cross-stream maintenance notes.

**Reason:** this package contains multiple independent RC number lines and historical sections whose terminology (`validated Entity`, old Native ABI, ContactPair production role) was later superseded. Reading only a portion of the history can therefore produce a technically plausible but current-state-wrong conclusion.

**Consequence:** `MAINTAINER_INDEX.md`, `VERSION_LINEAGE.md`, `OPEN_ISSUES.md`, `HISTORY_COVERAGE.md`, and `MAINTENANCE_PROTOCOL.md` are part of the required handoff surface. Historical text is preserved rather than rewritten as if it never happened.


## D-20260929-01 — Correct Full Move VTable; reject historical sole-VTable assumption

**Decision:** the CorePath top-level Move outcome and active-execution identity use Full Move VTable `0x03910AA8`. `0x0390E248` is retained only as the documented sibling Simple/Intercept Move VTable and must not authorize a top-level BSC Move outcome.

**Evidence:** direct disassembly of the locked EXE SHA `6c104a63...3297` proves allocator `0x02F5248C` returns `slot_base`, top-level Move `0x030344D4` passes `slot_base+0x18` to Full Move constructor `0x0300B094`, and that constructor installs `0x03910AA8`. Attack remains `0x03910228`. The prior current-state docs conflated `0x0300B038` / `0x0390E248` (Simple/Intercept Move) with the hooked top-level Move path.

**Consequence:** R1 allocator-index, R2 container-scan, and R3 constructor-witness experimental branches are withdrawn; the allocator ABI itself was not the fault. Core fixtures are corrected so portable PASS can no longer be obtained by modeling the wrong Move VTable. Per-kind native calibration is also hardened so a partial/no-sequence outcome cannot count as successful calibration.


## D-20260929-02 — Default product policy is Smooth, hard semantics remain fixed

**Decision:** the next gameplay architecture uses **Smooth** as the built-in/default profile. Route/target/canonical identity invariants remain non-configurable.

**Reason:** once the Native Move outcome bug was fixed, runtime logs showed remaining visible stops are caused by conservative transition timing and rollback policy, not by loss of command identity. The product's purpose is to remove avoidable stop/start behavior while preserving player intent.

**Consequence:** precision preferences become bounded policy choices; hard command meaning does not become a priority score.

## D-20260929-03 — Introduce one Transition Policy evaluator for dispatch and SC6

**Decision:** proactive `advance()` and exact-Native SC6 reconciliation must consume the same transition decision model.

**Reason:** current asymmetry allows Move→Move dispatch policy to coexist with SC6 logic that automatically rolls back every future MOVE. Separate policy engines can fight each other and create braking/rollback oscillation.

**Consequence:** SC6 remains the execution-identity authority, but it becomes a coordinator. Immediate `i+1` MOVE/ATTACK successors are evaluated by transition class; `i+2` or later remains hard rollback.

## D-20260929-04 — Use bounded hysteresis instead of boundary thrashing

**Decision:** every smooth transition may define an `issue_window` and a slightly wider `adopt_window`. Lua proactively issues only inside the issue window; exact Native `i+1` execution inside the adoption-only band may be soft-adopted instead of rolled back.

**Reason:** CA and Lua do not sample transition boundaries at the same instant. A single strict threshold can cause Native advance → Lua rollback → CA brake → immediate re-advance.

**Consequence:** `native_successor_tolerance` tunes only the bounded hysteresis band. It never authorizes action skipping or target mismatch.

## D-20260929-05 — MCT configures immutable soft policy profiles only

**Decision:** MCT values are read/compiled once per battle into an immutable `PolicyProfile`. Presets are Smooth/Balanced/Precise/Custom. MCT is optional; missing MCT falls back to built-in Smooth.

**Reason:** direct live mutation of scattered CFG values would make active generations non-reproducible and maintenance logs ambiguous.

**Consequence:** MCT cannot alter Native proof contracts, canonical ordering, manual RMB authority, target identity, quarantine policy or retry bounds.

## D-20260929-06 — Implement D1 in staged single-variable promotions

**Decision:** T1 structural refactor, T2 smooth behavior, T3 MCT, and T4 Attack/Exit tuning are separate maintenance stages.

**Reason:** the abandoned BSC-CONV branch demonstrated that broad simultaneous cleanup/gameplay changes destroy attribution.

**Consequence:** no all-at-once “new architecture” patch is acceptable. Each stage requires its own patch, tests, result and documentation promotion.

## 2026-09-29 — TPOL-T1H: hide MCT UI until default behavior is stable

**Decision:** Implement the PolicyProfile/MCT adapter boundary before exposing any MCT page.

**Reason:** Current access favors live battle observation over formal settings-matrix testing. A visible UI would create an unstable compatibility/support contract before T2 defaults are proven.

**Consequence:** T1H uses an immutable built-in hidden profile. Future MCT values must enter through the profile compiler rather than mutating CFG values directly.

## 2026-09-29 — Replace abstract Attack Commitment with direct Minimum Engagement Time

**Decision:** Public schema uses `engagement_hold_seconds` (0.5–10.0 s; default 3.0) instead of the earlier abstract `attack_commitment` score.

**Reason:** Players need to decide how long a unit must actually remain in verified engagement before a queued Exit Move can become eligible. This is different from how aggressively BSC should enforce disengagement after eligibility.

**Consequence:** `disengage_priority` remains a separate later-stage control. Minimum Engagement Time counts eligible engagement evidence, not time since Attack order/ACK.


## D-20261005-01 — Direct T2 experiments do not override the staged D1 migration

**Decision:** The 2026-10-05 direct T2-B, T2-A, hairpin, and native-Move-passthrough experiments are historical evidence only. Current runtime is re-anchored on pre-T2 behavior while T1 is implemented first.

**Reason:** T2-B demonstrated a useful smooth Attack handoff, but direct T2-A patches exposed the exact failure D-20260929-03/-04 predicted: separate proactive and SC6 policy paths fought each other. Permissive adoption caused fold-back compression; stricter rollback caused stepwise movement. Native passthrough isolated destructive rollback but contradicts the product goal of improving Move→Move steering and D1's requirement to preserve SC1–SC4.

**Consequence:** Preserve all experiment evidence, but do not treat those builds as current architecture. Reintroduce gameplay changes only after behavior-neutral T1 and through one shared evaluator.

## D-20261005-02 — Implement T1 shared evaluator with zero gameplay change

**Decision:** `R1.TransitionPolicy.evaluate()` is the single structural decision adapter consumed by proactive `advance()`, SC6 native reconciliation, and scheduler urgency. T1 preserves every pre-T2 transition outcome, including strict Move→Attack and legacy immediate-MOVE rollback.

**Evidence:** full existing maintenance suite PASS, deterministic old/new transition probe equivalent, and mutation coverage catches evaluator bypass in advance/SC6/scheduler plus H2 future-skip relaxation.

**Consequence:** T2-A/T2-B/T2-C may now change policy in one place. `ADOPT_ONLY` remains inactive until T2-C.


## D-20261005-03 — Separate captured and BSC-issued execution identity before T2

**Decision:** Before enabling T2-A/T2-C, each canonical action keeps the player's original Native capture identity separate from any later BSC-issued/ACK identity. Runtime state records an explicit execution lane (`PLAYER_NATIVE` / `BSC_ISSUED`). `R1.execution_matches_action()` consumes one lineage-aware adapter rather than implicitly folding both identities into `accepted_* or capture` fields.

**Reason:** The direct T2 experiments showed that Native future execution and BSC recovery can interact destructively. The old identity selector was semantically correct but encoded two different command lineages in one implicit fallback. T2 reconciliation needs to know not only *which canonical action* an exact Native order matches, but also *which command lineage* supplied that identity, without changing T1 decisions yet.

**Evidence:** T1.5 leaves `TransitionPolicy.evaluate()`, route/attack geometry and CFG thresholds unchanged; a modeled equivalence gate checks 15,625 capture/accepted identity states against the old selector; seven lineage-specific mutations are caught. Final GitHub Actions v4 validation passes the documentation contract and the consolidated maintenance runner **30/30**; the core mutation harness also passes **43/43**.

**Consequence:** T1.5 is behavior-neutral. Immediate future MOVE still follows the legacy T1 rollback rule, Move→Attack remains strict, and `ADOPT_ONLY` remains inactive. T2 may consume the lineage metadata later, but T1.5 itself may not use it to widen or narrow transition permission.
