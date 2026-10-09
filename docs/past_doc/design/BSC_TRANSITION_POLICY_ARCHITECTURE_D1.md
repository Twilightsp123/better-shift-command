# BSC Transition Policy Architecture D1

Status: **APPROVED DESIGN — T1H + T1 + T1.5 + T1.6 + T1.7 IMPLEMENTED STRUCTURALLY; T2 GAMEPLAY POLICY NOT ACTIVE**  
Design stream: `BSC-TPOL-D1`  
Runtime baseline: `BSC v1.2.2 / 1.2.2-corepath-rc8` + Native `1.0.17-corepath-wh3-6c104-movevtfix`

> This document defines the next gameplay architecture. It does **not** describe code that is already live. Current runtime truth remains the existing source plus `ARCHITECTURE_STATUS_20260929.md`.

## 1. Why this design exists

The Move-VTable repair closed the Native outcome failure. After that repair, runtime logs exposed two gameplay-level sources of visible stopping:

1. **Move → Attack is intentionally strict in the current code.** `route_handoff_ready()` blocks every Move→Attack transition until the current Move is already `semantic_done`, which gives CA time to enter arrival braking before Attack is issued.
2. **SC6 only adopts an immediate future ATTACK.** If Native is already executing an immediate future MOVE, current SC6 treats it as `NATIVE_FUTURE_OVERRUN` and rolls back to the current Move. This can create an avoidable direction reset / braking cycle even though Native is already executing the next canonical Move.

These are not address/EXE failures. They are policy decisions in Lua and can be redesigned without new reverse engineering.

## 2. Product goal

Default BSC behavior should be:

> **Preserve canonical command meaning, but choose the smoothest legal transition whenever more than one legal execution timing exists.**

The default profile is therefore **Smooth**. Precision-oriented players may choose Balanced, Precise, or Custom through MCT.

The architecture must avoid two historical failure patterns:

- making gameplay behavior depend on unproven Native/physical semantics;
- changing many unrelated systems in one convergence step, making regressions impossible to attribute.

## 3. Layer model

```text
Player input / Native journal
        │
        ▼
[1] Canonical Action Plane
    - immutable action order
    - blocks: MOVE_ROUTE / ATTACK / EXIT_ROUTE
    - target identity
    - route debt
        │
        ▼
[2] Hard Invariant Plane
    - manual REPLACE/RMB authority
    - no skipped canonical action
    - exact Attack target identity
    - no unbounded recovery
    - no MCT override of Native proof requirements
        │
        ▼
[3] Transition Policy Plane  ← NEW
    - one evaluator for proactive dispatch and SC6 reconciliation
    - transition class + profile + live geometry
    - strict-ready / smooth-ready / adopt-only / hard-block zones
        │
        ▼
[4] Execution Coordinator
    - dispatch successor
    - adopt Native successor
    - soft-adopt inside hysteresis band
    - rollback only clear violations
        │
        ▼
[5] Recovery Plane
    - SC6 execution-identity recovery first
    - SC5 physical Exit recovery second
        │
        ▼
CA locomotion / combat execution
```

MCT only configures Layer 3. It may not weaken Layers 1–2.

## 4. Hard invariants — not configurable

These rules remain absolute for every preset and every custom setting.

### H1 — Manual player REPLACE is authoritative

An ordinary RMB/nonqueued player command cancels BSC ownership of the previous canonical chain. No MCT setting may delay or veto it.

### H2 — Canonical indices cannot be skipped

If current index is `i`, Native execution at `i+2` or later is never adopted merely for smoothness. Intermediate canonical actions remain owed.

### H3 — Attack identity is exact

Attack adoption/dispatch must match the canonical target identity. Spatial proximity or `current_target()` is never enough.

### H4 — Prior route debt cannot cross a semantic boundary

Existing unresolved debt from an earlier waypoint may use SC3 soft continuation only across Move→Move when the successor chord still preserves the debt corridor. Move→Attack and Exit→Attack may not carry old unresolved waypoint debt across the boundary.

### H5 — Recovery is bounded

SC5 reassert and SC6 rollback share bounded accounting. MCT may tune timing inside safe ranges but can never create unlimited retries.

### H6 — Native proof contracts are not gameplay settings

Journal provenance, ACK identity, engine sequence, revision, lifetime, V3 active-execution identity, hook authorization and fail-closed behavior are outside MCT.

### H7 — Quarantined physical evidence remains quarantined

Transition Policy D1 introduces no new dependency on Entity/MovementComponent/ContactPair/Smart Guard.

## 5. Transition classes

The policy evaluator classifies only the immediate canonical edge.

| Transition | Current behavior | D1 target behavior |
|---|---|---|
| MOVE → MOVE | SC1–SC4 early steering | preserve; expose bounded smoothness tuning |
| MOVE → ATTACK | strict `semantic_done` | bounded terminal Attack handoff |
| ATTACK → EXIT MOVE | FEG completion then Move | preserve semantics; later expose bounded commitment/exit tuning |
| EXIT MOVE → MOVE | same Move steering machinery | preserve, with Exit block constraints |
| EXIT MOVE → ATTACK | final Exit must satisfy Exit semantics | separate stricter terminal handoff class |
| Native current → immediate future MOVE | currently rollback | adopt when policy permits; soft-adopt in hysteresis band |
| Native current → immediate future ATTACK | adopt/rollback | same shared policy as proactive dispatch |
| Native current → future index > i+1 | rollback | unchanged hard rollback |

## 6. One policy evaluator, two consumers

Current code lets proactive dispatch and SC6 reconciliation reach transition decisions through related but asymmetric paths. D1 replaces this with one pure evaluator:

```lua
TransitionPolicy.evaluate(st, current, successor, geometry, profile, context)
```

It returns a structured decision, never performs a command itself:

```text
transition_kind
zone
reason
hard_violation
route_debt_mode
current_credit
issue_window
adopt_window
metrics
profile_id
```

Recommended `zone` values:

```text
HARD_BLOCK
WAIT
ADOPT_ONLY
ISSUE_READY
```

The coordinator maps the same decision differently depending on context:

### Proactive dispatch context

- `ISSUE_READY` → dispatch successor.
- `ADOPT_ONLY` / `WAIT` → keep current action; do not proactively issue early.
- `HARD_BLOCK` → never dispatch.

### Native reconciliation context

If Native is already executing the **immediate** successor:

- `ISSUE_READY` → adopt.
- `ADOPT_ONLY` → soft-adopt; do not rollback a near-boundary legal successor.
- `WAIT` → rollback only when outside the bounded adoption envelope.
- `HARD_BLOCK` → rollback/fail closed.

If Native is executing `i+2` or later, H2 overrides policy and forces rollback.


## 6.1 T1.5 execution-lineage input

Before T2 changes any decision zone, exact execution identity is represented with two explicit sources: the original player `capture_identity` and any later BSC `issued_identity`. The evaluator/reconciler may observe the selected lineage as `PLAYER_NATIVE` or `BSC_ISSUED`. T1.5 does not use this value to change permission; it only removes ambiguity so later T2 logic can reason about the source of an exact match without redefining canonical semantics.

## 6.2 T1.6 committed-edge transaction

Before any T2 permission change, execution commitment is transactional. `dispatch()` may authorize/submit an edge but may not mark the prior action committed. A verified BSC ACK or exact Native successor observation calls the same `Core.commit_transition_edge()` path; that path owns MOVE handoff credit / route-debt transfer, cursor advance, execution-lane update and successor entry. Rejection/timeout aborts the transaction. This removes the ACK-vs-SC6 commit split while leaving all T1.5 zones unchanged.

T1.7 now makes issue/adopt envelope calculation consumer-neutral before T2 changes any permission.

## 6.3 T1.7 consumer-neutral envelopes

T1.7 is the final permission-neutral structural step before T2. `TransitionPolicy.evaluate()` no longer receives a consumer identity that changes permission. It emits a single decision with separate `issue_window` and `adopt_window` envelopes. Advance interprets the issue envelope, SC6 interprets the adopt envelope, and scheduler urgency consumes the same route decision.

The T1.7 mapping is deliberately legacy-equivalent: immediate future MOVE adopt remains closed, while proactive Move issue uses the existing SC1–SC4 window; strict Move→Attack remains unchanged. T2 is the first stage allowed to widen either envelope.

## 7. Hysteresis: the anti-thrashing rule

D1 deliberately separates **issue timing** from **adoption tolerance**.

```text
far from legal transition      adoption-only band        issue-ready band
───────────────────────────────┬──────────────────────────┬──────────────► destination
rollback Native if it advances  Native may be adopted     Lua may issue successor
                                Lua itself still waits
```

This acts like a Schmitt trigger. It prevents oscillation where CA advances a fraction earlier than Lua, Lua rolls back, CA brakes, then Lua immediately advances again.

`native_successor_tolerance` controls the width of the bounded adoption-only band. It does not allow skipping actions.

## 7.1 Arrival-brake observation and G1.1 policy evidence

WH3 units do not behave like fixed-turn-radius vehicles under ordinary right-click movement; they can redirect very quickly. D1 therefore models the hidden problem as **arrival braking**, not turn radius.

The separation is:

1. **semantic legality:** canonical edge, route debt, current waypoint corridor, target identity and Exit semantics;
2. **motion evidence:** whether the observed slowdown predicts stopping at the current waypoint;
3. **execution synchronization:** how far Native may advance between two Lua observations.

Behavior-neutral `ARRIVAL_BRAKE_G1` records ground speed, radial approach speed, observed deceleration, stopping distance and one-poll travel. It grants no permission.

T2-B adds **G1.1**. Using four post-entry position samples, it requires both ground speed and radial approach speed to decrease over three consecutive intervals, then projects a stopping point. It produces two coherence bounds:

`issue_coherent := abs(remaining - d_stop) <= move_reach_tolerance`

`adopt_coherent := abs(remaining - d_stop) <= move_reach_tolerance + one_poll_travel`

The one-poll term is measured from actual approach speed and actual model-time interval. It is not a configurable gameplay distance and may never widen proactive issue.

This distinction prevents an arbitrary terrain/congestion slowdown from becoming sufficient merely because `d_stop` is numerically large.

## 8. MOVE → MOVE policy

SC1–SC4 remain the baseline implementation and are migrated behind the evaluator with no behavior change in the first refactor stage.

Legal modes remain:

- `PATH_SAFE`
- `STEERING_CORNER`
- `TURN_CORRIDOR_STALL_ESCAPE`
- `SOFT_PRESERVED` route debt

D1 adds one important reconciliation rule:

> If exact Native active execution already matches the **immediate next MOVE**, evaluate the same Move→Move policy instead of automatically treating every future MOVE as overrun.

When adopted:

- if the existing steering corridor is sufficient, credit the current waypoint exactly as normal SC1/SC2 would after an accepted successor;
- if the transition relies on SC3 debt preservation, transfer/retain the debt with the same corridor proof;
- if it is outside the maximum adoption envelope, rollback remains valid.

## 9. MOVE → ATTACK policy

T2-B G1.1 is the first intentional D1 gameplay candidate and is offline validated, but not yet WH3-promoted.

### 9.1 Hard prerequisites

Early ordinary Move→Attack requires:

- successor exactly `i+1`;
- exact canonical target identity;
- no confirmed terminal target end;
- all prior route debt clear;
- ordinary MOVE semantics (not unfinished Exit);
- T1.6 transaction commitment after submission/observation.

No historical `attack_lead_*`, angle or execution-cap value authorizes permission.

### 9.2 Separate issue and adopt envelopes

The policy exposes independent envelopes rather than a single `ready` boolean.

**ATTACK_PATH_SAFE**

The live current-position→exact-target chord passes within the current waypoint's existing Move reach tolerance.

- proactive issue requires G1.1 **issue coherence**;
- exact Native adopt may use G1.1 **adopt coherence**;
- if only adopt coherence is true, the route mode is `ATTACK_PATH_SAFE_HYSTERESIS` and issue remains closed.

**ATTACK_TERMINAL_CORRIDOR**

If the target chord does not preserve the waypoint corridor:

- proactive issue additionally requires `remaining <= move_reach_tolerance`;
- exact Native adopt may tolerate `remaining <= move_reach_tolerance + one_poll_travel`;
- an adopt-only result is `ATTACK_TERMINAL_HYSTERESIS`.

Thus the one-poll synchronization margin can compensate Native/Lua sampling skew but cannot proactively swallow a waypoint.

### 9.3 Pre-promotion Native decision cache

When exact active execution still matches the current MOVE, SC6 computes the same shared TransitionPolicy decision and caches it with generation, current action identity, immediate successor identity, model timestamp, actual observed poll interval, and a frozen scalar geometry snapshot.

If the next observation shows exact active execution already equals the immediate ATTACK, reconciliation may consume that cached **adopt** envelope only if the cache is no older than one actual observed poll. It must not use post-Attack steering motion to decide whether the previous MOVE had been braking coherently.

### 9.4 Commit semantics

Permission is not completion.

BSC issue: `AUTHORIZED -> SUBMITTED -> ACK -> COMMITTED`

Exact Native successor: `AUTHORIZED/CACHED -> OBSERVED -> COMMITTED`

Only the shared `Core.commit_transition_edge()` grants `ATTACK_TERMINAL_HANDOFF`. Reject, stale generation, timeout or closed adopt envelope leaves the previous Move uncommitted. No unresolved route debt crosses the Attack boundary.

Offline result: **46/46 maintenance PASS**, core **44/44 mutations**, dedicated G1.1/T2-B/cache **13/13 mutations**, runtime fixtures **4/4**. WH3 RT-TP-02/03 remains the promotion gate.

## 10. EXIT MOVE → ATTACK policy

Exit→Attack remains a distinct class from ordinary Move→Attack.

Default design:

- exact immediate successor only;
- prior debt clear;
- required Exit displacement/route intent satisfied;
- fresh-engagement proof remains **post-ACK** through FEG as in current RC8;
- no Entity/ContactPair physical gate is restored;
- terminal early handoff window is narrower than ordinary Move→Attack.

This allows smooth re-engagement without turning “Exit” into a meaningless one-frame order.

## 11. ATTACK → EXIT MOVE policy

FEG remains authoritative for the Attack semantic episode. D1 does not replace FEG with a priority score.

A later MCT stage may tune bounded policy parameters such as engagement commitment / exit urgency, but only inside safe ranges. Target-invalid aborts and exact command identity remain unchanged.

## 12. SC6 becomes a coordinator, not a second policy engine

Current SC6 has special-case logic:

```text
immediate ATTACK → maybe adopt
any MOVE future → rollback
later future → rollback
```

D1 changes SC6 to:

```text
read exact active execution once
        ↓
current exact match? → keep current
        ↓
which canonical future index matches?
        ↓
index > current+1 → hard rollback
        ↓
index == current+1
        ↓
consume the shared TransitionPolicy decision (or the one-poll cached pre-promotion decision for an already-active immediate ATTACK)
        ↓
ISSUE_READY / ADOPT_ONLY → adopt
WAIT/HARD_BLOCK outside bounded envelope → rollback
```

This preserves SC6's exact identity role while removing transition-specific duplication.

## 13. MCT architecture

MCT does not mutate individual CFG globals throughout the battle. Instead:

1. Read MCT once during battle initialization.
2. Compile values into an immutable `PolicyProfile` snapshot.
3. All transition evaluations for that battle use the same snapshot.
4. Changing MCT takes effect next battle, avoiding mid-generation rule changes.
5. If MCT is missing/unavailable, load the built-in **Smooth** profile.

The profile contains normalized policy values, not raw Native semantics.

Recommended public controls:

- Behavior Preset
- Movement Cornering
- Attack Handoff
- Route Fidelity
- Native Successor Tolerance
- Minimum Engagement Time (direct seconds; default 3.0)
- Disengage Priority

See `MCT_POLICY_SCHEMA_D1.md`.

## 14. Observability

Every transition decision should expose a stable reason code. Release builds do not need high-frequency geometry spam, but they should retain bounded fault/summary counters:

```text
transition_issue_move_move
transition_issue_move_attack
native_adopt_move
native_adopt_attack
native_soft_adopt_move
native_soft_adopt_attack
native_hard_rollback
native_future_overrun
manual_cancel
```

Session-end summary should make a regression visible without requiring debug telemetry.

## 15. Non-goals

Transition Policy D1 does **not** redesign:

- Native hook addresses or outcome decoding;
- Journal/ACK provenance;
- Entity/MovementComponent/ContactPair research;
- Smart Guard;
- UI teardown / observer lifecycle hang;
- target viability semantics;
- FEG internals in the first implementation stage.

Those are separate maintenance streams.

## 16. Promotion rule

T1–T1.7 and G1 are validated structural/observation layers. T2-B G1.1 is offline validated on the construction branch but becomes production behavior only after WH3 RT-TP-02/03. T2-MOVE, T3 and T4 remain gated separately; the Attack candidate does not authorize immediate future MOVE adoption.


## 14. T1H hidden-profile implementation note

`BSC-TPOL-T1H` implements the policy schema/profile compiler and the future MCT adapter boundary without registering an MCT UI. Only `engagement_hold_seconds` is wired, at the behavior-equivalent default 3.0 seconds. The movement-transition fields remain reserved until T2. See `HIDDEN_MCT_INTERFACE_T1H.md`.
