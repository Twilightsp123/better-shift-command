# Attack Transition and Timed Disengage

## Move -> Attack

Attack uses its own predictive transition window; it is not forced to wait until the previous Move reaches 8m/stall. This avoids CA braking before attack while preserving Attack as a hard barrier.

## Engagement credit

```text
eligible = unit:is_in_melee() == true
           AND unit:current_target() == intended target
```

Only adjacent eligible observations within the observation-gap rule add model time. Attack acceptance/approach does not count.

## Exit

When eligible time reaches ~3000ms and a queued future Move exists, Controller issues exactly one verified nonqueued Move to pN and releases control. Runtime HF5 evidence showed command ACK plus substantial separation from the target and a complete `melee=false` transition in at least one case.

## Attack-first

Ordinary native Attack is adopted, never re-issued. A later Shift pN uses the same engagement history and exit logic.
