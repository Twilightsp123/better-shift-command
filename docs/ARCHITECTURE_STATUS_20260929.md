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

## 3. Current gameplay limitations after T1.5

### 3.1 Strict Move→Attack boundary remains current behavior

T1 deliberately preserves the pre-T2 rule: ordinary Move→Attack remains blocked until current Move `semantic_done` (`ATTACK_REQUIRES_ROUTE_COMPLETE`). A 2026-10-05 direct T2-B experiment demonstrated that bounded terminal handoff can remove the visible pause in WH3 9.0.2, but that experiment is **not current T1.5 runtime**. T2-B must be reintroduced through the shared evaluator.

### 3.2 SC6 immediate-MOVE asymmetry remains current behavior

T1 also deliberately preserves the legacy SC6 result for exact immediate future MOVE: it remains a hard rollback in current runtime so structural equivalence can be proven. T2-A is the staged behavior change that will evaluate the same MOVE→MOVE policy for Native reconciliation.

### 3.3 2026-10-05 direct T2 experiments are historical evidence

The direct T2-A adoption candidate caused early fold-back/self-compression in WH3. A stricter hairpin patch then produced repeated rollback/reassert and stepwise movement. A later native-Move-passthrough diagnostic isolated destructive rollback as part of the symptom chain, but passthrough contradicts BSC's product goal and D1's approved SC1–SC4 preservation. These experiments are archived as evidence and must not be promoted as current architecture.

### 3.4 T1.5 execution-lineage separation is implemented behavior-neutrally

The canonical action now carries an explicit `capture_identity` for the player's original Native order. If BSC later submits that same canonical action, the accepted command is recorded separately as `issued_identity`. `R1.action_execution_identity()` preserves the exact pre-T1.5 precedence rules while also returning the lineage (`PLAYER_NATIVE` or `BSC_ISSUED`). State tracks the current `execution_lane` for diagnostics and later T2 reconciliation.

This stage does **not** authorize any new handoff. The shared TransitionPolicy logic, route geometry, CFG thresholds, immediate-MOVE rollback behavior and strict Move→Attack behavior remain byte/semantics-equivalent to T1.

## 4. Approved architecture — T1 + T1.5 implemented, T2 pending

`BSC-TPOL-D1` introduces one Transition Policy Plane between canonical semantics and execution coordination. T1 implements the shared evaluator structure, and T1.5 makes command-execution lineage explicit while preserving the same decisions.

Key properties:

- one evaluator for proactive dispatch, SC6 reconciliation and scheduler preview;
- hard invariants separated from soft timing/precision policy;
- Smooth is the default profile;
- current T1.5 zones preserve legacy decisions and do **not** activate `ADOPT_ONLY`;
- T2 will add immediate future MOVE policy, bounded Move→Attack terminal handoff, then issue/adopt hysteresis;
- MCT configures only soft policy through an immutable per-battle `PolicyProfile`.

Full design: `docs/design/BSC_TRANSITION_POLICY_ARCHITECTURE_D1.md`.

## 5. Lifecycle is a separate stream

Battle-complete / desktop / main-menu hang investigation is **not** part of Transition Policy D1. Current safe-stop and UI-listener observations remain tracked separately in `OPEN_ISSUES.md`. Do not combine lifecycle and smoothness changes in one patch.

## 6. TPOL-T1H + TPOL-T1 + TPOL-T1.5 implementation status

The hidden profile scaffold and shared behavior-neutral TransitionPolicy evaluator are now implemented.

- no visible MCT UI exists;
- no MCT dependency is required;
- built-in hidden source is authoritative;
- `engagement_hold_seconds=3.0` remains behavior-equivalent to the legacy 3000 ms Attack hold;
- `R1.TransitionPolicy.evaluate()` is consumed by proactive `advance()`, SC6 reconciliation, and scheduler urgency;
- T1 old/new deterministic transition probes are equivalent;
- T1.5 separates `capture_identity` from BSC `issued_identity`, with explicit `execution_lane` tracking;
- T1.5 semantic-equivalence checks prove the shared policy/geometry/CFG are unchanged and the new identity adapter preserves the old identity result;
- existing SC1–SC6 gameplay regressions remain unchanged;
- `ADOPT_ONLY`, immediate-MOVE T2-A, Move→Attack terminal T2-B, and T2-C hysteresis are **not active in current source**;
- movement policy profile values remain reserved until their staged T2/T3 promotions.
