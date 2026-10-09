# Transition Policy Test Plan D1

Status: **DESIGN GATE**

## 0. T1 structural gate status

T1 behavior-neutral shared-evaluator gate: **PASS (2026-10-05)**. Existing gameplay suite is unchanged, deterministic pre-T1/current transition probe is equivalent, and mutation catches bypass of the evaluator in proactive dispatch, SC6 and scheduler urgency. The tests below remain T2/T3 promotion requirements.


## 0.5 T1.5 execution-lineage gate

T1.5 is behavior-neutral and must prove:

- original player order identity is retained as `capture_identity`;
- accepted BSC issue identity is stored separately as `issued_identity`;
- the authoritative matcher returns the same seq/receipt/lifetime result as T1;
- `TransitionPolicy.evaluate()`, route/attack geometry and CFG thresholds are unchanged;
- Native reconciliation receives lineage metadata but does not use it to alter T1 zones;
- lineage mutation tests catch dropped capture identity, ignored/unstored issued identity, lost lane snapshot/restore, and missing reconcile lineage.

## 0.6 T1.6 transition-transaction gate

T1.6 permission-neutral gate: **PASS (2026-10-05 local consolidated validation)**. It proves BSC submission is not canonical commitment, ACK commits through the shared edge path, rejection aborts without commit, and exact Native successor adoption uses the same commit function. Deterministic T1 transition output and all scalar CFG values remain unchanged. T1.6 transaction mutations are 7/7 caught; runtime transaction cases are 3/3 PASS.

## 0.7 T1.7 consumer-neutral envelope gate

T1.7 is permission-neutral and must prove:

- no evaluator permission branch reads a consumer identity;
- proactive dispatch, SC6 and scheduler retain all shared evaluator call sites;
- the decision carries separate issue and adopt envelopes;
- legacy immediate-MOVE adoption remains closed while proactive Move issue remains unchanged;
- deterministic T1.6 transition output and all scalar CFG values remain unchanged;
- envelope-specific mutation tests catch consumer reintroduction, missing envelopes, widened legacy MOVE adoption, Native adopt-envelope bypass and future-index skipping.

Validation result: **PASS**. GitHub Actions full maintenance is **37/37 PASS**; the T1.7 contract/equivalence gates pass and all **7/7** envelope mutations are caught.

## 0.8 ARRIVAL_BRAKE_G1 observation gate

G1 is behavior-neutral and must prove:

- no new gameplay CFG scalar is introduced;
- the observer uses post-entry position history only;
- ground speed and radial waypoint-approach speed must both show sustained deceleration before `braking=true`;
- irregular model-time spacing is handled from actual timestamps rather than an assumed 100 ms poll;
- the derived synchronization margin is exactly one last observed poll of waypoint approach, not a tunable meter constant;
- `TransitionPolicy.evaluate()` does not read G1 fields;
- deterministic T1.7 permission output is identical to the pre-G1 controller.

This is a model-validation stage, not a gameplay-success claim.

## 0.9 G1.1 / T2-B dual-envelope offline gate

Validation result: **PASS (2026-10-07)**.

The construction candidate proves offline that:

- generic sustained slowing is not enough; G1.1 projects a stopping point and checks waypoint coherence;
- issue coherence uses only the existing Move reach tolerance;
- adopt coherence may add exactly one observed poll of approach travel;
- proactive issue never consumes the one-poll margin;
- issue permission is always a subset of adopt permission;
- prior route debt and Exit semantics remain blocking;
- exact Native early Attack adoption requires a generation/current/successor-scoped pre-promotion decision cache no older than one actual poll;
- cache geometry is frozen rather than aliased;
- BSC submission cannot grant `ATTACK_TERMINAL_HANDOFF` before ACK;
- reject/timeout cannot retain credit;
- exact Native adoption commits through the same T1.6 edge transaction;
- immediate future MOVE adoption remains closed.

Evidence: **46/46 maintenance PASS**, core **44/44 mutations CAUGHT**, dedicated G1.1/T2-B/cache **13/13 mutations CAUGHT**, T2-B transaction/runtime fixtures **4/4 PASS**.

This is **not** WH3 runtime promotion. RT-TP-02/03 remain mandatory.

## 1. Offline policy tests

Every test should assert both decision `zone` and stable `reason`.

### Move→Move

- straight medium leg: current SC2 early handoff preserved;
- 90° turn: steering corridor preserved;
- short zig-zag: no node swallowing;
- SC3 debt chord preserved: continue;
- SC3 debt chord deviates: block;
- SC4 stalled just outside corridor: bounded escape;
- immediate Native next MOVE inside issue window: adopt;
- immediate Native next MOVE only inside adopt band: soft-adopt;
- immediate Native next MOVE far outside band: rollback;
- Native future MOVE at `i+2`: rollback.

### Move→Attack

- straight/path-safe approach: `ATTACK_PATH_SAFE` issue requires **issue coherence**; adopt may use the wider one-poll **adopt coherence**;
- off-corridor proactive Attack: `ATTACK_TERMINAL_CORRIDOR` requires `remaining <= existing move_reach_tolerance`; one-poll distance must not widen issue;
- exact Native immediate Attack may enter `ATTACK_PATH_SAFE_HYSTERESIS` or `ATTACK_TERMINAL_HYSTERESIS` only from a fresh pre-promotion cached decision;
- cached decision identity must match generation/current action/successor action and be no older than one actual observed poll;
- generic deceleration whose projected stopping point is not waypoint-coherent must remain WAIT;
- no historical Attack lead/angle/execution-cap scalar participates in permission;
- prior debt unresolved: block;
- Exit route unfinished: block;
- wrong canonical target / `i+2` future: hard block;
- confirmed target dead/left: no early credit;
- BSC issue rejection/timeout: no `ATTACK_TERMINAL_HANDOFF`;
- ACK and exact Native adoption: both commit through `Core.commit_transition_edge()`.

### Exit→Attack

- Exit minimum route intent not satisfied: block;
- Exit prerequisites satisfied near terminal corridor: adopt/issue according to profile;
- post-ACK fresh FEG episode still required;
- no physical Entity/ContactPair gate.

## 2. MCT/profile tests

- Smooth/Balanced/Precise compile deterministically.
- Custom 0 and 100 remain inside hard safety caps.
- changing one advanced option cannot change hard invariants.
- missing MCT loads built-in Smooth.
- battle profile is immutable after initialization.

## 3. Mutation tests

Required mutations must be caught:

1. allow `future_index > i+1` adoption;
2. allow Attack target mismatch;
3. bypass TransitionPolicy in proactive advance;
4. bypass TransitionPolicy in SC6 pre-promotion cache;
5. bypass TransitionPolicy in SC6 fallback reconciliation;
6. bypass TransitionPolicy in scheduler preview;
7. allow Move→Attack with prior route debt pending;
8. ignore Exit strictness;
9. remove sustained ground-speed deceleration evidence;
10. remove sustained radial-approach deceleration evidence;
11. add one-poll sync margin to proactive issue coherence;
12. remove the one-poll margin from adopt coherence;
13. remove cache edge identity or one-poll freshness;
14. restore strict `semantic_done` as the only Move→Attack path;
15. classify every future MOVE as permissive passthrough.

Current offline candidate catches the dedicated G1.1/T2-B/cache set **13/13** plus the consolidated core mutation harness **44/44**.

## 4. WH3 runtime matrix

Use one controlled scenario per semantic question rather than random long battles.

### RT-TP-01 — Move→Move continuity

`P1 → P2 → P3`, medium legs, visible turns. Expect no stop at P1/P2 and no rollback spam.

### RT-TP-02 — Move→Attack straight

`Move P → Attack A`. Expect Attack issued before full arrival stop under Smooth.

### RT-TP-03 — Move→Attack high-angle

Same with a large turn. Expect bounded turn, no early long-distance cut.

### RT-TP-04 — Native immediate MOVE advance

Capture exact active execution becoming `i+1 MOVE`. Expect `NATIVE_SUCCESSOR_ADOPTED_MOVE` or soft-adopt, not `NATIVE_FUTURE_OVERRUN`.

### RT-TP-05 — True future overrun

Force/capture Native at `i+2`. Expect rollback remains.

### RT-TP-06 — Attack→Exit→Attack

Ensure FEG, Exit route semantics, fresh post-ACK Attack episode and SC5/SC6 ordering remain intact.

### RT-TP-07 — Preset comparison

Run the same route under Smooth/Balanced/Precise. Differences should be timing/precision only, never action order/target identity.

## 5. Release telemetry

Keep low-volume counters even with `debug_telemetry=false`:

```text
TP_SUMMARY move_move_issue=N move_attack_issue=N soft_adopt_move=N soft_adopt_attack=N hard_rollback=N future_overrun=N
```

This is intended to make future regressions attributable without requiring another broad probe campaign.
