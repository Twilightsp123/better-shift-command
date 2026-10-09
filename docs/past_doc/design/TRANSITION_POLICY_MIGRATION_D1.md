# Transition Policy Migration D1

Status: **APPROVED IMPLEMENTATION PLAN — T1–T1.7 + G1 VALIDATED; T2-B G1.1 OFFLINE VALIDATED / WH3 PENDING; T2-MOVE PENDING**

The migration deliberately avoids a broad convergence rewrite. Each stage must be independently testable and revertible.

## T0 — Freeze the corrected Native baseline

Baseline requirements before gameplay work:

- Native `1.0.17-corepath-wh3-6c104-movevtfix` remains unchanged.
- Full Move VTable `0x03910AA8` remains authoritative.
- No R1/R2/R3 experimental outcome resolver code is reintroduced.
- Current Windows delivery/candidate hashes are archived.

No EXE reverse engineering is needed for T1–T3 unless a new Native contradiction appears.

## T1 — Structural TransitionPolicy refactor, behavior-neutral

### T1H — Hidden policy/MCT scaffold (implemented)

- Add immutable PolicyProfile schema/presets and future adapter boundary.
- Register **no** MCT UI and make no `get_mct()` call.
- Route legacy `attack_hold_ms=3000` through `engagement_hold_seconds=3.0`.
- Reserve all movement policy values without applying them yet.

This is a substage of T1 and does not claim the shared transition evaluator is complete.


Goal: create the new policy plane without changing decisions.

Work:

1. Introduce `TransitionPolicy` namespace/module.
2. Move current Move→Move `route_handoff_ready()` decision into an evaluator adapter.
3. Preserve current strict Move→Attack result exactly.
4. Route proactive `advance()` and SC6 reconciliation through the same decision object where applicable.
5. Preserve current SC6 behavior in tests during this stage, including immediate-MOVE rollback, so refactor equivalence can be proven.

Gate:

- existing controller suite unchanged PASS;
- new equivalence tests compare old/new decisions over fixtures;
- mutation catches bypass of evaluator.

**T1 implementation result — 2026-10-05:** PASS. Shared evaluator is wired to `advance()`, SC6 and scheduler urgency; deterministic old/new probe is equivalent; full maintenance suite passes; mutation catches evaluator bypass. No T2 behavior is active.


### T1.5 — Execution lineage separation (implemented behavior-neutrally)

Before T2, split the identity of the player's captured Native command from the identity of any command later issued and ACKed by BSC. Add explicit execution-lane metadata, route exact matching through one lineage-aware adapter, and pass lineage into Native reconciliation context. Do not change TransitionPolicy zones, route geometry, CFG thresholds or rollback/adopt outcomes.

Gate:

- T1.5 structural contract PASS;
- old/new identity selector semantic equivalence;
- TransitionPolicy/geometry/CFG unchanged;
- lineage-specific mutation protection;
- Native/address source unchanged.

**T1.5 implementation result — 2026-10-05:** PASS. Structural/equivalence gates pass, final consolidated maintenance is 30/30 PASS, core mutation harness is 43/43 PASS, lineage mutations are 7/7 caught, and the Windows address/native workflow passes. No T2 behavior is active.

### T1.6 — Transition Transaction / commit protocol (permission-neutral)

Before T2 changes permission, make canonical edge commitment transactional:

1. evaluate the immediate canonical edge;
2. create one edge transaction;
3. BSC submission enters `SUBMITTED`, while an exact already-running Native successor enters `OBSERVED`;
4. only a verified Native ACK or exact Native adoption may call the shared edge commit;
5. the shared commit applies MOVE handoff credit / route-debt transfer, advances the cursor, updates execution lineage and enters the successor action;
6. rejection, stale cancellation or timeout aborts the transaction without committing the previous edge.

This stage changes no TransitionPolicy zone and does not enable `ADOPT_ONLY`, immediate MOVE adoption or terminal Attack handoff. It corrects execution protocol timing and removes the ACK-vs-SC6 commit split before those behaviors exist.

Gate:

- no `ACTION_HANDOFF_COMMITTED` before ACK for a BSC-issued successor;
- rejected issue leaves the edge uncommitted;
- exact Native successor adoption uses the same edge-commit function;
- T1/T1.5 permission/equivalence suites remain PASS;
- transaction-specific mutation protection;
- Native/address source unchanged.

**T1.6 implementation result — 2026-10-05:** PASS. Submission no longer commits a canonical edge before ACK; verified ACK and exact Native adoption share `Core.commit_transition_edge()`; rejection/timeout aborts the edge transaction. Deterministic T1 permission output and all scalar CFG values are unchanged. Local maintenance is 34/34 PASS; core mutations 43/43, T1.5 mutations 7/7, T1.6 mutations 7/7, and T1.6 runtime transaction cases 3/3. Native/address source remains unchanged.

### T1.7 — Consumer-neutral policy envelopes (permission-neutral)

After T1.6, remove `consumer` from the permission calculation itself. The evaluator emits one edge decision with explicit issue/adopt envelope data; proactive dispatch, Native reconcile and scheduler only interpret that same decision. Initially map the envelopes back to T1.6 outcomes so this stage remains permission-neutral.\n\n**T1.7 implementation result — 2026-10-06:** PASS. Consumer-specific permission branches are removed; issue/adopt envelopes preserve legacy immediate-MOVE rollback and strict Move→Attack. GitHub Actions full maintenance is 37/37 PASS; T1.7 envelope mutations are 7/7 caught.

## G1 — Arrival-brake observation, behavior-neutral construction stage

Before widening T2 permission, observe the engine behavior we are actually trying to pre-empt.

- Do **not** infer or tune a minimum turn radius. WH3 ordinary right-click movement can redirect nearly immediately.
- Retain route corridor/debt geometry as the semantic legality proof.
- Record consecutive position samples after current Move entry.
- Derive ground speed and radial waypoint-approach speed from the same intervals.
- Classify sustained arrival braking only when both decrease over three consecutive intervals.
- Derive stopping distance from observed radial deceleration.
- Derive the future hysteresis synchronization margin from the last observed one-poll approach distance.
- Add no gameplay CFG scalar and do not expose the observation to TransitionPolicy permission yet.

Gate:

- current T1.7 deterministic permission probe unchanged;
- all scalar CFG values unchanged;
- pure observer fixtures cover cruise, sustained deceleration, irregular poll spacing, warmup and moving-away cases;
- static contract proves TransitionPolicy does not read G1 observation fields;
- Native/address source unchanged.

**G1 implementation result — 2026-10-06:** PASS. The behavior-neutral G1 observer passed its focused gates and the consolidated 40-job maintenance suite. T2-B therefore consumes G1.1 as a separate policy-evidence layer without changing the frozen G1 contract.

## T2 — Smooth-default behavior correction

This is the first intentional gameplay change.

### T2-MOVE — Immediate future MOVE reconciliation + hysteresis

Change SC6 from:

```text
future.type ~= ATTACK => rollback
```

to:

```text
future_index == i+1
→ evaluate MOVE→MOVE or MOVE→ATTACK policy
```

Immediate Move successor may be adopted/soft-adopted if the current route semantics permit. `i+2` or later remains hard rollback. This promotion includes the separate `issue_window` / wider `adopt_window` hysteresis from the start; do not ship a standalone permissive immediate-MOVE stage.

### T2-B — MOVE→ATTACK terminal handoff

**Current construction result — offline validated, WH3 runtime pending.**

T2-B G1.1 intentionally changes only ordinary Move→Attack:

- successor must be the exact canonical `i+1 ATTACK`; later futures remain H2 hard violations;
- prior route debt must be clear;
- target identity must remain exact; proactive issue still uses existing `target_ready()`;
- Exit→Attack remains strict until existing Exit route semantics are satisfied;
- no `attack_lead_*`, angle cap, execution-cap or new gameplay scalar authorizes the handoff.

G1.1 derives the observed stopping point from four post-entry position samples. It exposes two evidence envelopes:

1. **issue coherence** — stopping-point error ≤ existing Move reach tolerance;
2. **adopt coherence** — stopping-point error ≤ existing Move reach tolerance + exactly one observed poll of approach travel.

Policy combines that evidence with route geometry:

- **ATTACK_PATH_SAFE**: current-position→exact-target chord passes within existing Move reach tolerance. Issue requires issue coherence; adopt may use adopt coherence.
- **ATTACK_TERMINAL_CORRIDOR**: off-corridor proactive issue additionally requires `remaining <= move_reach_tolerance`.
- **ATTACK_PATH_SAFE_HYSTERESIS / ATTACK_TERMINAL_HYSTERESIS**: ADOPT_ONLY cases. The one-poll synchronization margin may widen adopt, **never proactive issue**.

While exact current MOVE execution is still proven, SC6 caches the same policy decision with generation/current/successor identity. If Native promotes the exact immediate ATTACK before the next Lua observation, reconciliation may consume that cached decision for at most one actual observed poll; it does not recompute pre-Attack braking from post-Attack motion.

Every successful early transition remains transactional:

`AUTHORIZED -> SUBMITTED/OBSERVED -> COMMITTED`

Only `Core.commit_transition_edge()` may grant `ATTACK_TERMINAL_HANDOFF`; reject/stale/timeout aborts without credit.

**Offline gate result — 2026-10-07:** PASS. GitHub Actions maintenance **46/46**, core mutations **44/44**, dedicated G1.1/T2-B/cache mutations **13/13**, and T2-B runtime fixtures **4/4**. Native/address files are unchanged. Promotion still requires WH3 RT-TP-02/03.

## T3 — Presets and MCT

Only after T2 default Smooth behavior is stable:

1. Add immutable `PolicyProfile` snapshot.
2. Implement Smooth/Balanced/Precise presets.
3. Add Custom advanced controls.
4. Missing MCT falls back to built-in Smooth.
5. MCT values alter only soft policy bounds.

Do **not** use MCT to hide a bad default. Smooth must pass runtime regression before MCT is considered complete.

## T4 — Attack/Exit policy tuning

After Move transitions are stable, optionally expose:

- Minimum Engagement Time;
- Disengage Priority;
- narrower Exit→Attack terminal handoff.

FEG, exact execution identity and bounded recovery remain architectural authorities.

## Separate stream — lifecycle/teardown

Battle teardown / observer suspend-resume and third-party UI listener errors are not part of Transition Policy D1. Track them separately so a teardown fix cannot silently change movement behavior.
