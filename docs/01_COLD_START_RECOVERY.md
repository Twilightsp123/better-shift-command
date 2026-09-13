# Cold-Start Recovery — Return to Real-Game Testing Without Re-Reversing

Purpose: somebody who has not touched the project for months should be able to resume battle testing from this document alone.

## A. Identify the authoritative artifacts

Use:

```text
Controller: P2B-HF5 / 0.2.5
queue_probe.lua SHA256:
94b503ba1d64b9d97b9c667d1639dacdfd93342db35658474db4583230782d15

zzz_queue_probe.pack SHA256:
3d393fc37172b86aa6fc208f7df6ade89ecb308c55a347c2ad38aa4e93c434dd

Bridge: 0.5.0-attack-native-token
Bridge runtime archive:
WH3_Native_Bridge_v0_5_0_Runtime_Validated_Archive.zip
```

Do not start from v6.6, v7.1.0, P1C, P1D or intermediate P2A/HF3/HF4 sources unless reproducing history.

## B. First decision: did CA change the executable contract?

Run the Bridge's existing EXE/byte-guard preflight against the installed `Warhammer3.exe`.

- **All 16 guards match:** do not reverse engineer anything. Use the frozen DLL/Bridge path and go to section C.
- **Any guard fails:** stop before game injection/command issue. Follow `ADDRESS_RELOCATION_PLAYBOOK.md`.

The historical validated executable SHA256 was:

```text
b7315fa718fd84e2e018e2c4df06600e9df0076156b474f148d9d558c939aa55
```

A different whole-file hash does not by itself prove every address changed; the guarded native entry points are the operational criterion. Never bypass a mismatched guard just to make the DLL load.

## C. Minimal battle smoke test

Use one ground melee unit and one valid enemy target. Run at 1x for diagnosis.

### Case 1 — Move-first full chain

```text
Shift P1
→ Shift P2
→ Shift Attack T
→ Shift pN
```

Expected behavior:

- Move handoffs occur before full stop where geometry allows;
- Attack is not skipped;
- eligible melee with T accumulates ~3000 model ms;
- Controller issues one pN Move;
- pN native command receives matching ACK;
- unit begins separating from T.

### Case 2 — Attack-first

```text
ordinary right-click Attack T
→ Shift pN
```

Expected:

- native player Attack is **adopted, not reissued**;
- engagement history starts immediately;
- after eligible hold, one pN Move is dispatched.

### Case 3 — player override safety

During `ATTACK_APPROACH` or `ATTACK_HOLD`, issue an ordinary non-Shift RMB to D.

Expected:

- old generation cancels immediately;
- no later Lua dispatch from that generation;
- old pN never revives.

## D. Debugging mode

Production build suppresses high-frequency telemetry. If any case fails, replace only the active pack with `release/debug/zzz_queue_probe.pack` and reproduce once.

Useful debug markers include:

```text
ORDER
ACTION_CAPTURE
PLAN_APPENDED
ATTACK_TARGET_OBSERVED
ATTACK_TRANSITION_WAIT
ATTACK_POST_SAMPLE
P2_EXIT_OBSERVED
HEARTBEAT
```

Do not permanently ship Debug mode.

## E. Do not reinterpret these facts

- `ATTACK` is a hard **execution barrier**, not a generation terminator.
- queued Shift input may arrive in the Journal later than the player's physical input; the shadow timeline therefore remains appendable.
- engagement time is sampled unit-level `is_in_melee + current_target`, not exact first-hit timing.
- ordinary RMB is replacement authority; it must kill stale Lua work.
- accepted Move proves command acceptance, not by itself physical disengagement.

## F. When to call for native reverse engineering

Only when one of these occurs:

1. Bridge byte guard(s) fail after a CA update;
2. a frozen Bridge runtime fact is contradicted by a controlled trace;
3. public engagement APIs are visibly contradicted by physical contact and repeatable telemetry;
4. a required provenance/queued/recipient fact is no longer obtainable from the current Bridge Journal.

Otherwise treat bugs as Controller/release-layer bugs first.
