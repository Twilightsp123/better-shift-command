# Transition Policy Test Plan D1

Status: **DESIGN GATE**

## 0. T1 structural gate status

T1 behavior-neutral shared-evaluator gate: **PASS (2026-10-05)**. Existing gameplay suite is unchanged, deterministic pre-T1/current transition probe is equivalent, and mutation catches bypass of the evaluator in proactive dispatch, SC6 and scheduler urgency. The tests below remain T2/T3 promotion requirements.

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

- straight approach, terminal corridor: issue before full stop;
- 45° / 90° / high-angle approach: bounded by dynamic caps;
- very short leg: no whole-leg swallow;
- prior debt unresolved: hard block;
- wrong/dead target: hard block/skip according to existing target rules;
- Native immediate Attack inside issue window: adopt;
- Native immediate Attack inside adopt-only band: soft-adopt;
- Native immediate Attack far early: rollback;
- Native Attack at `i+2`: rollback.

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

Add mutations that must be caught:

1. allow `future_index > i+1` adoption;
2. allow Attack target mismatch;
3. let MCT disable RMB cancel;
4. let MCT increase recovery retry count without bound;
5. bypass TransitionPolicy in `advance()`;
6. bypass TransitionPolicy in SC6 reconciliation;
7. make adopt window smaller than issue window;
8. allow Move→Attack with prior debt pending;
9. classify every future MOVE as overrun (regression to current SC6 limitation);
10. restore strict `semantic_done` as the only Move→Attack path in Smooth.

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