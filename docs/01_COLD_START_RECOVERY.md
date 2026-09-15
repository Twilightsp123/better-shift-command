# Cold-Start Recovery — v1.0.1

Purpose: resume real-game testing after months away without repeating reverse engineering.

## A. Authoritative components

```text
Controller: 0.2.6 (P2B-HF5 derivative)
Bridge:     0.5.1-per-kind-calibration
Steam:      self-contained Windows x64 PFH5
Builder:    tools/release_v1.0.1/BUILD_RELEASE_V1.0.1.ps1
```

Keep the original HF5/v1.0.0 validation files as historical evidence; do not replace them with v1.0.1 release traces.

## B. First decision: did CA change the executable contract?

Run the Bridge's existing EXE/byte-guard preflight against installed `Warhammer3.exe`.

- **All 16 guards match:** do not reverse engineer. Use current Bridge source/build path.
- **Any guard fails:** stop before unsafe issue and follow `native/ADDRESS_RELOCATION_PLAYBOOK.md`.

A different whole-file executable hash alone does not prove every guarded entry changed.

## C. Build contract

Build v1.0.1 using VS2019/v142, or VS2022 with the v142 toolset. The release script intentionally refuses v143-only builds because TESTFIX A introduced a runtime `MH_CreateHook` failure while TESTFIX B on v142 restored success.

Do not change compiler family and native hook logic in the same recovery step.

## D. Minimal battle smoke tests

### Case 0 — pure Move first, no Attack calibration

Fresh battle. Do **not** attack first.

```text
Shift P1 -> Shift P2 -> Shift P3 -> several more Move points
```

Expected in debug telemetry:

```text
BRIDGE_ARMED kind=MOVE ... accepted_move=true accepted_attack=false
DISPATCH_MOVE
OWN_MOVE_ACK
```

This is the v1.0.1-specific regression test.

### Case 1 — long Move route

Draw 10-20 points including sharp turns.

Expected:

- repeated Move dispatch/ACK continues;
- CA destination canonicalization may produce `OWN_MOVE_CANONICALIZED` in debug mode;
- no `CONTROLLER_FAIL reason=OWN_MOVE_PAYLOAD_MISMATCH`.

### Case 2 — Move -> Attack -> Move

```text
Shift P1 -> Shift P2 -> Shift Attack T -> Shift pN
```

Expected:

- Attack is not skipped;
- eligible melee with T accumulates about 3000 model ms;
- one pN Move is issued after hold completion.

### Case 3 — Attack-first

```text
ordinary Attack T -> Shift pN
```

Expected:

- player Attack is adopted, not reissued;
- engagement history starts immediately;
- pN is dispatched after eligible hold.

### Case 4 — player override

During Attack approach/hold or Controller movement, issue an ordinary non-Shift replacement order.

Expected: old generation dies and never revives.

## E. Self-contained deployment troubleshooting

At first battle after a new embedded Bridge version:

```text
NATIVE_EMBED_WRITE wh3_native_bridge.dll
NATIVE_EMBED_OK ... exact_bytes=true
BRIDGE_OK version=...
```

When files already match, the release build normally suppresses `NATIVE_EMBED_KEEP`; debug builds may show it.

The native component is materialized and loaded in that same battle. There is no "install on first battle, work on second battle" requirement.

## F. When to reverse engineer again

Only when:

1. native byte guard(s) fail after a CA update;
2. a frozen runtime fact is contradicted by a controlled trace;
3. required queued/source/recipient/revision facts disappear from the Bridge Journal;
4. the current native entry/packet contract is no longer recoverable with the documented relocation clues.

Otherwise treat defects as Controller, deployment, build-toolchain, or release-layer issues first.
