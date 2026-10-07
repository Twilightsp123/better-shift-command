# Architecture Status — 2026-09-29

Formal maintained Mod version: **v1.3.0**. Internal labels such as CorePath RC8 / TPOL-T1H describe implementation lineage, not the release version.

## 1. Current production/runtime architecture

Current v1.3.0 runtime retains the CorePath RC8 architecture with the Move-VTable correction:

`player command → Native capture/journal → canonical Lua action/block → SC1–SC4 route logic → verified Native issue/ACK → V3 exact active execution → SC6 reconcile → CA locomotion`

Attack observation/hold remains FEG-based. SC5 still runs only after exact current Exit-MOVE execution is confirmed. Physical Entity/Component/ContactPair evidence remains quarantined/staged-disabled.

Native identity:

- Bridge `1.0.17-corepath-wh3-6c104-movevtfix`;
- 16 mandatory hooks;
- Full top-level Move VTable `0x03910AA8`;
- Attack VTable `0x03910228`.

## 2. Runtime closure achieved on 2026-09-29

The corrected bridge runs in WH3 without the old `OWNED_OUTCOME_INDETERMINATE` failure caused by the wrong top-level Move VTable. This closes the address/outcome blocker sufficiently to expose remaining gameplay policy behavior.

## 3. Current gameplay status after T2-B G1.1 offline validation

### 3.1 Move→Attack T2-B G1.1 candidate is offline validated on the construction branch

The release baseline remains T1.7/SC1–SC6, but `maintenance/t2b-terminal-attack` intentionally changes ordinary Move→Attack. It does **not** authorize handoff from historical `attack_lead_*`, angle or execution-cap tuning.

G1.1 uses four post-entry position samples to require sustained loss of both total ground speed and radial approach speed. It projects the observed stopping point and separates two coherence envelopes:

- **issue coherence:** stopping-point error ≤ the existing Move semantic reach tolerance;
- **adopt coherence:** stopping-point error ≤ that same tolerance + exactly one observed poll of approach travel.

The T2-B policy then applies route semantics:

- `ATTACK_PATH_SAFE`: the live position→exact-target chord still passes through the current waypoint semantic corridor;
- `ATTACK_TERMINAL_CORRIDOR`: off-corridor proactive issue is allowed only after remaining distance itself is within the existing Move reach tolerance;
- `ATTACK_PATH_SAFE_HYSTERESIS` / `ATTACK_TERMINAL_HYSTERESIS`: **ADOPT_ONLY** bands for an exact immediate Native Attack. The one-poll margin never widens proactive issue.

SC6 caches the same decision only while exact current MOVE execution is still proven and may reuse it for at most one actual observed poll after Native promotes the exact `i+1 ATTACK`. Exit→Attack remains strict. All successful early handoffs still require the T1.6 transaction commit before `ATTACK_TERMINAL_HANDOFF` credit.

Offline result: GitHub Actions **46/46 PASS** with G1.1/T2-B runtime fixtures **4/4 PASS**, dedicated G1.1/T2-B/cache mutations **13/13 CAUGHT**, and core mutation harness **44/44 CAUGHT**. WH3 RT-TP-02/03 is still required before promotion.

### 3.2 SC6 immediate-MOVE asymmetry remains current behavior

T1 also deliberately preserves the legacy SC6 result for exact immediate future MOVE: it remains a hard rollback in current runtime so structural equivalence can be proven. T2-A is the staged behavior change that will evaluate the same MOVE→MOVE policy for Native reconciliation.

### 3.3 2026-10-05 direct T2 experiments are historical evidence

The direct T2-A adoption candidate caused early fold-back/self-compression in WH3. A stricter hairpin patch then produced repeated rollback/reassert and stepwise movement. A later native-Move-passthrough diagnostic isolated destructive rollback as part of the symptom chain, but passthrough contradicts BSC's product goal and D1's approved SC1–SC4 preservation. These experiments are archived as evidence and must not be promoted as current architecture.

### 3.4 T1.5 execution-lineage separation is implemented behavior-neutrally

The canonical action now carries an explicit `capture_identity` for the player's original Native order. If BSC later submits that same canonical action, the accepted command is recorded separately as `issued_identity`. `R1.action_execution_identity()` preserves the exact pre-T1.5 precedence rules while also returning the lineage (`PLAYER_NATIVE` or `BSC_ISSUED`). State tracks the current `execution_lane` for diagnostics and later T2 reconciliation.

This stage does **not** authorize any new handoff. The shared TransitionPolicy logic, route geometry, CFG thresholds, immediate-MOVE rollback behavior and strict Move→Attack behavior remain byte/semantics-equivalent to T1.


### 3.5 T1.6 committed-edge transaction is implemented permission-neutrally

T1.6 removes the remaining ACK-vs-SC6 execution-protocol split without changing policy permission. BSC successor submission creates an `AUTHORIZED/SUBMITTED` edge transaction but does **not** commit the current handoff. Verified Native ACK and exact Native successor adoption both call the same `Core.commit_transition_edge()` path, which applies MOVE handoff credit / route-debt transfer, advances the canonical cursor, updates execution lineage and enters the successor action. Rejection / timeout aborts the transaction without committing the previous edge.

This specifically closes the pre-T2 hazard where `ACTION_HANDOFF_COMMITTED` could be set while the Native command was only pending. Immediate future MOVE remains legacy rollback, Move→Attack remains strict, and no hysteresis band is active.

### 3.7 ARRIVAL_BRAKE_G1 remains behavior-neutral; G1.1 is T2-B policy evidence

`ARRIVAL_BRAKE_G1` remains the frozen behavior-neutral observer. It records ground/radial speed, observed deceleration, stopping distance and one-poll travel without granting permission.

T2-B adds `ARRIVAL_BRAKE_G1_1` beside it rather than rewriting the validated G1 stage. G1.1 asks whether the **predicted stopping point** is coherent with the current waypoint semantic reach. It produces separate issue/adopt coherence rather than one `braking=true` bit. This distinguishes generic slowing from motion geometrically consistent with waypoint arrival braking.

No new gameplay CFG scalar is introduced. Formation width remains part of the already-existing Move semantic reach tolerance; the one-poll term comes only from actual observed approach speed × actual observed model-time interval.

## 4. Approved architecture — T1–T1.7 + G1 validated; T2-B G1.1 offline validated; T2-MOVE pending

`BSC-TPOL-D1` introduces one Transition Policy Plane between canonical semantics and execution coordination. T1 implements the shared evaluator structure, T1.5 makes command-execution lineage explicit, T1.6 unifies edge commitment after ACK / exact Native adoption, and T1.7 moves issue/adopt permission into consumer-neutral envelopes while preserving the same transition outcomes.

Key properties:

- one evaluator for proactive dispatch, SC6 reconciliation and scheduler preview;
- hard invariants separated from soft timing/precision policy;
- Smooth is the default profile;
- the frozen T1.7 baseline preserves legacy permission, while the current T2-B candidate intentionally makes `ADOPT_ONLY` reachable for **ATTACK only** through G1.1 and a one-poll pre-promotion decision cache;
- T2-B ordinary Move→Attack is now offline validated; T2-MOVE must still add immediate future MOVE policy and MOVE hysteresis without reusing the Attack candidate as permission;
- MCT configures only soft policy through an immutable per-battle `PolicyProfile`.

Full design: `docs/design/BSC_TRANSITION_POLICY_ARCHITECTURE_D1.md`.

## 5. Lifecycle is a separate stream

Battle-complete / desktop / main-menu hang investigation is **not** part of Transition Policy D1. Current safe-stop and UI-listener observations remain tracked separately in `OPEN_ISSUES.md`. Do not combine lifecycle and smoothness changes in one patch.

## 6. TPOL-T1H + TPOL-T1 + TPOL-T1.5 + TPOL-T1.6 + TPOL-T1.7 implementation status

The hidden profile scaffold and shared behavior-neutral TransitionPolicy evaluator are now implemented.

- no visible MCT UI exists;
- no MCT dependency is required;
- built-in hidden source is authoritative;
- `engagement_hold_seconds=3.0` remains behavior-equivalent to the legacy 3000 ms Attack hold;
- `R1.TransitionPolicy.evaluate()` is consumed by proactive `advance()`, SC6 reconciliation, and scheduler urgency;
- T1 old/new deterministic transition probes are equivalent;
- T1.5 separates `capture_identity` from BSC `issued_identity`, with explicit `execution_lane` tracking;
- T1.5 semantic-equivalence checks prove the shared policy/geometry/CFG are unchanged and the new identity adapter preserves the old identity result;
- current T2-B G1.1 GitHub Actions maintenance is **46/46 PASS**, with core mutation harness **44/44**, T1.5 lineage mutations **7/7**, T1.6 transaction mutations **7/7**, T1.7 envelope mutations **7/7**, dedicated G1.1/T2-B/cache mutations **13/13**, T1.6 runtime transaction gates **3/3**, and T2-B runtime fixtures **4/4**;
- T1.6 permission equivalence preserves the deterministic T1 transition probe and all CFG scalars;
- existing SC1–SC6 gameplay regressions remain unchanged;
- `ADOPT_ONLY` is active only for the offline-validated **T2-B ATTACK candidate**; immediate-MOVE T2-MOVE remains closed and is **not active**;
- movement policy profile values remain reserved until their staged T2/T3 promotions.


### 3.6 T1.7 consumer-neutral policy envelopes are implemented permission-neutrally

T1.7 removes the last permission calculation keyed by evaluator consumer. The evaluator now computes a single immediate-edge decision containing separate `issue_window` and `adopt_window` envelopes. Proactive dispatch reads the issue envelope; SC6 reads the adopt envelope; scheduler urgency consumes the same route decision without changing permission.

To preserve T1.6 behavior, the legacy immediate-MOVE adopt envelope is explicitly closed while the Move issue envelope keeps the existing SC1–SC4 timing rules. Move→Attack remains strict and no Native tolerance/hysteresis is active. T1.7 GitHub Actions full validation is **37/37 PASS**; core mutations are **43/43 CAUGHT**, and T1.5/T1.6/T1.7 stage mutations are **7/7 CAUGHT** each.
