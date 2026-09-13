# Controller Action Timeline

## Generation rules

- nonqueued external Move/Attack starts/replaces a generation;
- queued player action appends to the same generation, including after takeover;
- Controller self ACK confirms execution but never becomes player input;
- an old generation can never revive after replacement.

## Execution cursor

Appending to the future suffix never resets the current execution origin/cursor. The executed prefix is immutable.

## Attack barrier

Move lookahead may never skip over Attack. Attack is an execution barrier only; it does not seal the generation.

## Late tail

If pN arrives after Attack has already started, it is appended. Engagement history already earned is preserved. If eligible time is already >=3000ms, pN can be dispatched on the next safe execution update.
