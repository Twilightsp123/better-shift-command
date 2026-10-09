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

## D-20261005-04 — Insert a committed-edge transaction layer before T2

**Decision:** T2 behavior work is paused until transition execution is routed through one explicit edge transaction. `TransitionPolicy` continues to decide permission, but BSC issue submission, Native ACK, exact Native successor adoption, handoff credit, route-debt transfer and cursor movement must converge on one commit path. A command being submitted to Native is not itself a committed canonical handoff.

**Reason:** the post-T1.5 audit found a remaining execution-protocol asymmetry. `dispatch()` marked a MOVE handoff committed immediately after `issue_verified_command()` returned `PENDING_NATIVE_ACCEPTANCE`, while waypoint credit / route-debt transfer happened later on ACK and SC6 exact-Native adoption advanced the cursor through a separate path. That split is tolerable while T1.5 keeps immediate MOVE adoption blocked, but it becomes unsafe once T2-A/T2-C allows Native MOVE adoption or T2-B allows terminal Attack handoff. The direct T2 experiments already showed the practical failure mode of policy/execution paths fighting each other.

**Consequence:** add **T1.6 Transition Transaction** as a permission-neutral stage. The lifecycle is `AUTHORIZED -> SUBMITTED/OBSERVED -> COMMITTED` or `ABORTED`. `ACTION_HANDOFF_COMMITTED`, waypoint completion/debt transfer, cursor advance and execution-lane switch occur only in the shared commit path after a verified ACK or an already-exact Native adoption. Rejected or timed-out submissions abort without committing the previous edge. T1.5 transition permissions remain unchanged: immediate future MOVE is still legacy rollback, Move->Attack is still strict, and `ADOPT_ONLY` is still inactive.

**Migration update:** after T1.6, add a consumer-neutral policy-envelope stage before gameplay promotion. T2-B terminal Attack may then validate the new commit protocol first; immediate MOVE reconciliation and hysteresis are promoted together rather than exposing a standalone permissive T2-A state.



## D-20261006-01 — Remove policy consumer identity before T2

**Decision:** T1.7 makes `R1.TransitionPolicy.evaluate()` consumer-neutral. The evaluator emits one immediate-edge decision with separate issue and adopt envelopes. Proactive dispatch, SC6 Native reconciliation and scheduler urgency may interpret the same decision differently, but none may alter permission inside the evaluator by passing a consumer identity.

**Reason:** T1.6 fixed execution commitment but still encoded the old SC6 asymmetry with `consumer=="NATIVE_RECONCILE"`. Promoting T2 on top of that would keep two permission models hidden inside one function and make hysteresis difficult to prove.

**Consequence:** T1.7 remains permission-neutral. Legacy immediate-MOVE adoption stays closed in the adopt envelope while the issue envelope preserves existing SC1–SC4 timing. Strict Move→Attack remains unchanged. T2-B and T2-MOVE may now widen only the appropriate envelope through one shared policy calculation.


## D-20261006-02 — Observe CA arrival braking before tuning another transition threshold

**Decision:** insert ARRIVAL_BRAKE_G1 as an observation-only stage before T2 gameplay promotion. Do not model a WH3 unit turn radius: ordinary right-click movement can redirect almost immediately, so the relevant hidden engine behavior is arrival/braking at the current waypoint rather than a vehicle-like minimum turning radius.

**Reason:** SC1/SC2/SC4 and the historical T2-B experiments accumulated several distance/fraction constants while trying to beat CA's arrival controller. The next architecture should separate route legality from timing. Route/debt geometry answers whether changing command preserves player intent; G1 answers whether CA is actually slowing for the current waypoint. The observer requires simultaneous sustained decrease in ground speed and radial waypoint-approach speed, derives stopping distance from observed deceleration, and derives the future Native-adopt synchronization margin from one actual poll of travel instead of a hand-tuned meter tolerance.

**Consequence:** G1 changes no `CFG` scalar, no issue/adopt permission, no cursor rule, and no transition commit rule. T1.7 remains the permission authority. T2-B and T2-MOVE may later consume G1 only behind the existing hard invariants and T1.6 transaction protocol.


## D-20261006-03 — T2-B uses semantic corridor + observed arrival braking, not tuned Attack lead distance

**Decision:** reimplement ordinary Move→Attack as the first intentional T2 gameplay change using the existing semantic route corridor plus ARRIVAL_BRAKE_G1 timing evidence. Historical `attack_lead_*`, angle caps and predictive threshold values remain telemetry only and do not authorize T2-B.

**Reason:** WH3 units can redirect quickly under ordinary right click; the visible pause is caused by CA entering the current waypoint's arrival/braking behavior, not by a vehicle-like minimum turning radius. A new fixed lead distance would merely restart parameter tuning. The model should answer two separate questions: (1) would changing to Attack still preserve the current waypoint semantics, and (2) has CA actually entered the arrival-braking boundary we intend to pre-empt?

**Policy:** prior route debt must be clear; Exit→Attack remains strict; exact immediate successor/target identity remains mandatory. Before current Move semantic completion, G1 must report sustained braking and boundary crossing. If the current-position→target chord passes within the existing Move reach tolerance of the waypoint, the mode is `ATTACK_PATH_SAFE`. Otherwise the unit must already be within `move_reach_tolerance + one observed poll of approach travel`, producing `ATTACK_TERMINAL_CORRIDOR`. Both modes grant `ATTACK_TERMINAL_HANDOFF` credit only after T1.6 transaction commit.

**Consequence:** no new gameplay CFG scalar is introduced. MOVE→MOVE SC1–SC4 is unchanged. T2-MOVE/hysteresis remains inactive. The construction candidate requires offline and WH3 runtime promotion gates.


## D-20261007-01 — Split T2-B issue/adopt evidence and cache only the pre-promotion decision

**Decision:** replace the first T2-B `ready` candidate with G1.1 + explicit dual issue/adopt envelopes. The one-poll synchronization margin may widen Native Attack adoption only; it may not widen proactive Attack issue. When Native promotes the exact immediate Attack between Lua observations, SC6 consumes a generation/current/successor-scoped decision cached while exact current MOVE execution was still proven, valid for at most one actual observed poll.

**Reason:** three flaws remained in the first arrival-brake candidate. Generic deceleration could be misclassified as waypoint braking; a single `ready` boolean collapsed the T1.7 issue/adopt split; and `move_reach_tolerance + one_poll_distance` was being used for proactive terminal permission even though the one-poll term exists only to compensate asynchronous observation.

**Policy:** G1.1 projects the stopping point. Proactive issue requires stopping-point error within existing Move reach tolerance; adopt may add one observed poll of travel. `ATTACK_PATH_SAFE` preserves the waypoint chord; off-corridor proactive issue requires actual entry into the existing Move reach envelope. Exit→Attack and prior route debt remain strict. No new gameplay CFG scalar is added.

**Execution:** `ATTACK_TERMINAL_HANDOFF` remains commit-only through T1.6. BSC submission cannot credit the Move before ACK; exact Native adoption uses `OBSERVED -> COMMITTED`; reject/stale/timeout aborts without credit.

**Validation:** GitHub Actions T2-B G1.1 offline run passes **46/46 maintenance jobs**. Core mutations are **44/44 caught**; T1.5/T1.6/T1.7 stage mutations remain **7/7** each; dedicated G1.1/T2-B/cache mutations are **13/13 caught**; T2-B runtime fixtures are **4/4 PASS**. WH3 RT-TP-02/03 remains pending.

## D-20261009-01 — Native MOVE adoption must not inherit an unpaid turnback waypoint completion

**Decision:** for isolated T2-MOVE-G, require one-poll *frozen pre-promotion* backtrack/reach geometry before allowing exact immediate Native MOVE adoption through a STEERING_CORNER transition. If the successor endpoint projects back beyond the current waypoint's existing Move reach tolerance and current remaining is still outside that tolerance, reject Native adoption credit. Route legality, timing hysteresis, Native identity and T1.6 commit checks remain independently mandatory.

**Reason:** on the sealed F controller, synthetic 180° and 135° backtracking cases were Native-adopted with the waypoint 30m away even though the route tolerance was 5m; a dense short-leg reversal also adopted early. A proposed direct `route_handoff_ready()` change made those tests pass, but failed existing SC1 U-turn behavior and the T2-B static frozen contract. Those existing tests deliberately allow proactive U-turn steering before a waypoint. G therefore restricts only **Native observation→commit credit**, not the pre-existing proactive SC1 command policy.

**Evidence:** the unmodified F baseline had G controller 4/7 PASS, 3/7 FAIL in GitHub Actions `37822137891`. The isolated G correction passed G 7/7, G active mutants 3/3, E/F controller and mutations, T2-B contract and 46/46 maintenance in `37822771962`.

**Consequence / open decision:** proactive SC1 U-turn route-fidelity remains unresolved and may still trade off early smooth turning versus actual waypoint visitation. Never claim G fixes WH3 hairpin compression or early proactive U-turns. Any future semantic redesign must explicitly reconcile or supersede the old SC1 U-turn test, preserve bounded recovery, and provide new independent runtime/route tests; it must not be hidden inside G or merged to T2-B by offline CI alone.

## D-20261009-02 — H1 separates prospective route obligation from execution handoff without changing permissions

**Decision:** add a **read-only** `RouteObligation` shadow on isolated H1. Its verdicts are `SATISFIED`, `DEBT_PRESERVED`, and `BLOCKED`. A geometric debt-preservation chord is at most a necessary opportunity for the engine to visit the waypoint, never proof that it did. Legacy proactive Move→Move ISSUE and exact Native MOVE ADOPT retain identical G permissions; the same H1 pure observer logs the legacy issue decision and frozen pre-promotion evidence, but has no cursor, commit, dispatch, or Native bridge authority.

**Reason:** G's Frozen Native turnback guard closes one unsafe adoption path but does not address proactive SC1 `STEERING_CORNER`. The legacy SC1 U-turn test explicitly expects early handoff and the T1.6 commit marks the old waypoint complete on steering credit. H1 therefore preserves the legacy test while documenting that early 90° and 180° routes can differ from strict waypoint arrival obligations.

**Evidence:** Initial H1 CI `37825312679` succeeded; expanded `37825955358` also caught the circular `STEERING_CORNER_HANDOFF` completion-provenance mutant, with 15/15 pure, 5/5 real-controller shadow and 6/6 mutations, alongside original G/E/F and 46/46 maintenance checks. `route_handoff_ready()`, the T1.6 `commit_transition_edge()` and gameplay CFG remain byte-for-byte identical to sealed G.

**Next decision (not yet made):** H2 must specify the lifecycle of unpaid waypoint obligations across proactive ISSUE ACK, Native ADOPT and subsequent Native motion. It must distinguish an early steering command from valid route-completion credit without inventing automatic waypoint arrival. Resolve legacy U-turn smoothness versus fidelity via explicit branch-level design and red/green tests; H1 is not proof of WH3 runtime smoothness or release readiness.

## D-20261009-03 — Proactive ACK is an execution fact, not proof of the prior waypoint

**Evidence:** baseline H1 `b5020d9` in H2-A real-controller run `37827397901` issues the 180° successor from x=60, then receives a Native ACK without changing x; the T1.6 edge commits and `ACTION_COMPLETE STEERING_CORNER_HANDOFF remaining=40.000000` is logged. A 90° corner reproduces the same bug. Four control tests prove near-route completion, forward debt, pending-before-ACK and rejected-ACK paths remain distinct.

**Decision:** freeze this as a deterministic expected-red H2-A proof before any H2-B gameplay change. Do **not** interpret the green expected-red CI wrapper as a repaired Controller. H2-B must independently reason about execution commit, current waypoint completion, and payable SC3 route debt. A transition already ACKed cannot be retroactively denied or automatically treated as arrival; any issue-time route-fidelity change requires explicit original-SC1 contract review and movement testing. T1.6 stays the single cursor authority.

**Scope:** test-only H2-A does not change BSC command issuance, Native hooks/addresses, gameplay CFG or T2-B/WH3 promotion gates.

## D-20261009-04 — H2 separates execution ACK from route credit and supersedes premature early-steering semantics on an isolated branch

**Decision:** T1.6's single cursor/edge commit remains the only authority proving that a successor is actually executing. MOVE waypoint completion is a separate obligation: `SATISFIED` requires H1's independent arrival evidence, `DEBT_PRESERVED` registers SC3 route debt without fake completion, and `BLOCKED` vetoes new ISSUE/ADOPT when existing reach/chord/debt geometry cannot certify route preservation. Both proactive ISSUE and frozen exact Native i+1 ADOPT consume equivalent route-credit semantics without merging their T1.7 timing windows.

**Reason:** H2-A proved a 40m-unpaid waypoint could be declared `STEERING_CORNER_HANDOFF` after a legitimate early BSC ACK. Merely deferring completion after an unsafe reverse command would retain the fact but make the waypoint unreachable; the direct successor chord must be payable **before** issue. This intentionally overrides the historic SC1 early U-turn/90-degree promotion requirement, which cannot coexist with strict waypoint fidelity for the 0→100→0 case.

**Validation:** CI `37830565468` offline PASS on H2 7/7 real-controller, H3 9/9 stress, 4/4 Native parity and 5/5 H2 mutants, original maintenance suite PASS. Replaced obsolete early-SC1/SC2/SC4 mutation expectations with active route-authority tests; frozen G/H1 source and historical CI remain available. No new tunable meter, speed, angle or timing parameter was introduced.

**Unresolved:** a strict waypoint proof can cause CA braking near corners; neither fixture nor archive proves smooth movement or absence of foldback collisions inside the actual game. Real WH3 RT-TP-02/03/04/05 and lifecycle risks remain pending. Do not promote until real-game evidence meets both fidelity and smoothness requirements.


## D-20261009-05 — Integrate already-derived 9.0.2 map by Windows build-local overlay, not hash bypass

**Incident:** a prior H2/H3 source+PACK seal embedded the old 9.0.1 Native DLL and produced a live WH3 `OBSERVER_HOST_EXE_SHA256_MISMATCH` before any route algorithm could execute. The maintained 9.0.2 addresses, guards, Full Move VTable `0x03913618`, Attack VTable `0x03912988`, and EXE SHA256 `fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785` were already present on `maintenance/wh3-9.0.2-map-candidate`.

**Decision:** preserve the H2/H3 Controller and its MASM-safe v142 CMake, copy the 9.0.2 canonical candidate map for provenance, cross-check every core RVA/guard and VTable with its existing staged candidate, then compile 9.0.2 only with `WH3_NATIVE_MAP_INCLUDE_DIR` instead of promoting the default `native_maps/CURRENT`. Update the Lua/Native/packer version identity to 1.0.18. The packaging job must depend on a successful Windows Native CTest, consume that exact newly built DLL, and reject the known 9.0.1 DLL and missing 9.0.2 EXE hash.

**Evidence:** GitHub Actions `37877024598` Windows v142/MASM PASS, CTest 14/14, Linux H2/H3/maintenance PASS, full-source and ordinary/DEBUG PACK seal PASS. This is build and packaging evidence only. **WH3 runtime has NOT been tested**, and neither H2/H3 smoothness nor observer initialization may be promoted from this result. Draft review only; no merge/Steam update.
