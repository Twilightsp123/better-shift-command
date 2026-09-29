# BSC Transition Policy Architecture D1

Status: **APPROVED DESIGN — NOT YET IMPLEMENTED**  
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

This is the primary new gameplay transition.

### 9.1 Hard prerequisites

Move→Attack may never hand off early unless:

- successor is exactly `i+1`;
- target is viable and exact;
- all **prior** route debt is clear;
- current action has made the minimum progress required by the profile;
- no Exit-specific gate applies, or the Exit-specific policy also passes.

### 9.2 Terminal Attack corridor

The existing code already computes bounded Attack geometry (`attack_geometry`): angle, speed, formation width, current leg length, dynamic target position, and capped threshold. D1 promotes that geometry into an explicit policy input instead of leaving it telemetry-only.

Two safe modes are allowed:

1. **ATTACK_PATH_SAFE** — the current-position → target chord still respects the current waypoint corridor.
2. **ATTACK_TERMINAL_CORRIDOR** — the unit is already inside a bounded terminal window near the final Move waypoint, with sufficient route progress, so the waypoint can be treated as approach guidance rather than a mandatory stop point.

On accepted Attack handoff, the current Move receives explicit completion credit:

```text
ATTACK_TERMINAL_HANDOFF
```

No unresolved prior debt is transferred across the Attack boundary.

### 9.3 Default Smooth intent

Smooth should issue Attack **before CA has fully entered arrival braking**, while preserving the caps already present in `attack_geometry` and the hard prerequisites above.

Precise shrinks or disables the terminal corridor and approaches the existing `semantic_done` behavior.

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
call TransitionPolicy.evaluate(..., context=NATIVE_RECONCILE)
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
- Attack Commitment
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

This design becomes production architecture only after the staged migration in `TRANSITION_POLICY_MIGRATION_D1.md` passes its own offline and WH3 gates. Until then, current SC1–SC6 source remains runtime authority.
