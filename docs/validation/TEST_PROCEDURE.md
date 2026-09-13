# Real-Game Validation Procedure

Use the validated Bridge and Debug Controller when diagnosing. Run at 1x with one ground melee/cavalry unit and one valid enemy.

## Smoke A — Move-first

```text
Shift P1 -> Shift P2 -> Shift Attack T -> Shift pN
```
Expected: predictive Move/Attack, intended-target melee credit reaches ~3000ms, one pN Move is ACKed, unit separates.

## Smoke B — Attack-first

```text
ordinary Attack T -> Shift pN
```
Expected: `PLAYER_ATTACK_ADOPTED`, no duplicate scripted Attack, same hold/exit behavior.

## Smoke C — override safety

During Attack approach/hold, issue ordinary RMB D. Expected: old generation cancels and no later pN dispatch from it.

## Required evidence for a release baseline

- exact build/version markers;
- Bridge preflight/guards PASS;
- native ACK for scripted orders;
- no failures/chronology errors;
- rollback/restore evidence for test installer;
- immutable result ZIP + log hash archived.
