# Transition Decision Table D1

Status: **DESIGN ONLY**

## Decision vocabulary

- `ISSUE_READY`: Lua may proactively submit the immediate successor.
- `ADOPT_ONLY`: Lua itself waits, but if exact Native execution already advanced to the immediate successor, adopt it to avoid rollback thrash.
- `WAIT`: successor is not yet legal enough to issue/adopt.
- `HARD_BLOCK`: invariant violation; never adopt.

## Matrix

| Current | Immediate successor | Hard prerequisites | ISSUE_READY | ADOPT_ONLY | HARD_BLOCK examples |
|---|---|---|---|---|---|
| MOVE | MOVE | exact `i+1`; route/debt proof | PATH_SAFE / STEERING / bounded stall escape | slightly wider bounded corridor controlled by Native tolerance | successor is not `i+1`; debt path deviates beyond cap |
| MOVE | ATTACK | exact `i+1`; exact viable target; prior debt clear | terminal Attack issue corridor | bounded terminal hysteresis corridor | prior debt unresolved; target mismatch; too early |
| EXIT MOVE | MOVE | exact `i+1`; Exit block preserved | Move steering policy | bounded Exit Move hysteresis | block/order skip |
| EXIT MOVE | ATTACK | exact `i+1`; prior debt clear; Exit route/displacement prerequisites | narrower Exit→Attack terminal corridor | bounded Exit hysteresis | Exit intent not satisfied; target mismatch |
| ATTACK | EXIT MOVE | FEG/abort semantics | current Attack completion policy | not an SC6 Move reconciliation case | manual/identity mismatch |

## Native reconciliation rule

```text
future_index > current_index + 1
    => HARD rollback (canonical actions would be skipped)

future_index == current_index + 1
    => evaluate immediate transition class
       ISSUE_READY => adopt
       ADOPT_ONLY  => soft-adopt
       WAIT/HARD   => rollback when outside maximum bounded envelope
```

The critical D1 correction is that an **immediate future MOVE is no longer automatically classified as overrun**. It is evaluated through the same Move→Move policy used by proactive dispatch.

## Completion/debt credit

| Transition mode | Current action credit |
|---|---|
| Move→Move `STEERING_CORNER` | complete on accepted/adopted successor, as current SC1 behavior |
| Move→Move `PATH_SAFE` with unresolved physical stamp | register/preserve route obligation as current SC3 requires |
| Move→Attack `ATTACK_TERMINAL_CORRIDOR` | mark current Move complete as `ATTACK_TERMINAL_HANDOFF`; no prior debt may cross |
| Exit→Attack terminal handoff | mark final Exit Move complete only after Exit-specific prerequisites pass |
| Future index > i+1 | no credit; rollback |
