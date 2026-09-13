# v0.5.0 Real-game Validation — PASS

Status: **RUNTIME PASS**
Candidate: `0.5.0-attack-native-token`
Source digest: `51fc8e51dd4d4b22d2ae8d704f66a92b459f84e1aa735e8c740f1672f41ff11c`

## Required markers

All passed:

- ENTER
- CAL_MOVE_ACCEPTED
- CAL_ATTACK_ACCEPTED
- EXPERIMENTAL_ARM_PASS
- OWN_MOVE_PASS
- STALE_GATE_PASS
- PLAYER_RMB_PASS
- OWN_ATTACK_PASS
- VALIDATION_PASS

## Identity/revision proof

```text
rev=3 -> verified MOVE issue=1 -> OUR_CONTROLLER -> rev=4
old rev=3 -> REJECTED_STALE, callback_invoked=false
player RMB MOVE -> UNKNOWN issue=0 -> rev=5
verified ATTACK issue=2 -> OUR_CONTROLLER -> rev=6
```

This is the exact behavior required for the Controller development gate: owned commands are identifiable, stale controller work is rejected before side effects, and player replacement input is not misattributed as controller output.

## Candidate/rollback proof

The collected result records:

- ExperimentalIssue candidate manifest: true
- Windows build: PASS
- private-process smoke: PASS
- EXE fingerprint/guard preflight: PASS
- 16 guards
- validation fail lines: none
- rollback state: `ROLLED_BACK`

## Scope of claim

This validation closes the experimental Native Bridge integration gate. It does **not** set or imply global production flags `exact_source=true`, `verified_issue=true`, or `production_release_approved=true`.
