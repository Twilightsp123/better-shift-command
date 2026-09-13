# Expected Debug Log Markers

Production suppresses many high-frequency lines. Switch to the Debug pack for diagnosis.

Useful markers:

```text
ORDER
ACTION_CAPTURE
PLAN_APPENDED
DISPATCH_MOVE
OWN_MOVE_ACK
DISPATCH_ATTACK
OWN_ATTACK_ACK
PLAYER_ATTACK_ADOPTED
ATTACK_TARGET_OBSERVED
ATTACK_HOLD_BEGIN
ATTACK_HOLD_SUSPEND
ATTACK_HOLD_DONE
P2_MOVE_AFTER_ATTACK_ACK
P2_EXIT_OBSERVED
GEN_CANCEL
CASE_CANCEL_PASS
CONTROLLER_FAIL
```

Do not equate command ACK alone with physical disengagement. Exit telemetry is separate evidence.
