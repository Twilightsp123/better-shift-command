# Project Status — v1.0.1 Runtime-Validated Release Baseline

Date: 2026-09-15

## 1. Authoritative status

**Better Shift Command v1.0.1 is the current release baseline.**

Current components:

```text
Controller:    P2B-HF5 derivative / 0.2.6
Native Bridge: 0.5.1-per-kind-calibration
Steam build:   Windows x64 self-contained PFH5 pack
Build family:  VS2019/v142, or VS2022 generator with v142 toolset
```

v1.0.0/HF5 remains the immutable historical feature-validation baseline for Move->Move, Move->Attack, Attack hold/disengage, Attack-first adoption, APPEND, and player RMB cancellation. v1.0.1 does not redesign those state-machine features; it fixes two release blockers discovered after the self-contained Steam deployment was exercised in broader real-game routes.

## 2. v1.0.1 release blockers fixed

### 2.1 Per-kind calibration

v0.5.0's experimental issue gate required both an accepted natural MOVE and an accepted natural ATTACK before **any** scripted issue could arm. This meant a player could enter the first battle, draw a pure Shift movement route, and see no improvement until an ATTACK had also been naturally observed.

v0.5.1 changes readiness to a two-level rule:

```text
Global experimental readiness:
  accepted MOVE OR accepted ATTACK + handler evidence + zero faults

Per-issued-kind readiness:
  scripted MOVE   requires accepted_move_seen
  scripted ATTACK requires accepted_attack_seen
```

Real-game validation on 2026-09-15 confirmed `BRIDGE_ARMED kind=MOVE` while `accepted_attack=false`, followed immediately by Controller `DISPATCH_MOVE` / `OWN_MOVE_ACK` chains.

### 2.2 Native Move canonicalization

v1.0.0 treated any Controller Move ACK whose accepted native XYZ differed from the queued source point by more than 0.05 m on any axis as fatal `OWN_MOVE_PAYLOAD_MISMATCH`.

That rule was stronger than the proven identity contract. CA may canonicalize/rebuild the destination when a queued waypoint is re-issued as a nonqueued native Move.

v1.0.1 now uses strong identity first:

```text
OUR_CONTROLLER source
+ issue id
+ recipient uid
+ order type
+ expected revision -> accepted next revision
```

After that identity closes, finite native destination XYZ is accepted as authoritative. A difference larger than 0.05 m is diagnostic (`OWN_MOVE_CANONICALIZED`) rather than a global stop. NaN/Inf still fails closed as `OWN_MOVE_PAYLOAD_INVALID`.

Real-game validation exercised long/multi-unit routes and continued through more than fifty scripted issues without the old payload mismatch stop.

## 3. Self-contained Steam distribution

The Steam Workshop `.pack` now embeds:

```text
wh3_native_bridge.dll
minhook.x64.dll
MinHook license / third-party notice
```

At battle script load the Controller:

1. reads the embedded Lua binary payload;
2. compares it byte-for-byte with the file next to `Warhammer3.exe`;
3. keeps identical files without rewriting them;
4. writes and verifies only missing/different native files;
5. loads `wh3_native_bridge.dll` in the same battle.

Therefore the **first battle already uses the Bridge**, and later Workshop updates can automatically replace an older Bridge payload on the next clean game launch/battle load.

## 4. v142 toolchain is part of the release contract

TESTFIX A mixed a native logic change with a compiler-family change to VS2022/v143. That DLL loaded through Lua but failed at runtime Hook creation with `OBSERVER_MINHOOK_CREATE_FAILED`.

TESTFIX B returned to the v142-family toolchain used by the earlier validated Bridge. The same v0.5.1 logic then installed hooks and ran correctly in game.

The v1.0.1 release builder therefore **refuses v143-only builds**. This does not prove every future v143 binary is intrinsically invalid; it freezes the known-good release environment and avoids changing toolchain and native semantics simultaneously.

## 5. Runtime-confirmed behavior retained from HF5/v1.0.0

- Move->Move predictive handoff.
- Move->Attack predictive transition; Attack remains an execution barrier.
- Active generation stays appendable after takeover.
- `Shift Move* -> Shift Attack -> Shift Move` engagement-hold/disengage behavior.
- ordinary native `Attack T -> Shift Move` adoption without reissuing the Attack.
- eligible hold credit requires `is_in_melee()==true` and `current_target()==intended target`.
- ordinary RMB replaces/cancels old Controller generation.
- Controller self ACK is not re-admitted as player input.

## 6. Production logging

Release build uses `DEBUG_TELEMETRY=false`.

High-volume success traces such as per-order DISPATCH/ACK, PLAN_ACTIVATED, GEN_CANCEL, ATTACK_HOLD transitions and normal `NATIVE_EMBED_KEEP` are debug-only in the formal v1.0.1 source. Fatal Controller/Bridge errors, native component writes/verification, Bridge version success and refusal/degradation diagnostics remain available.

## 7. Permanently revoked directions

Do not reintroduce:

- `ordered_position()` as physical execution authority;
- Move callback count/serial as one-player-gesture identity;
- `+0x98` alone as Shift/RMB semantics;
- `RMB_OVERRIDE_LOCK` / destination-settle release;
- `NATIVE_OVERRIDE_FENCE`;
- Attack as generation terminator;
- fixed approach timeout that cancels long Attack travel;
- repeated escape Move spam;
- the v1.0.0 5 cm XYZ equality rule as a source/ownership authority;
- a global MOVE+ATTACK prerequisite for every scripted command kind.

## 8. Current next steps

Release engineering is now straightforward:

1. build the formal self-contained pack with `tools/release_v1.0.1/BUILD_RELEASE_V1.0.1.ps1` on the validated Windows v142 machine;
2. upload that PFH5 pack to Steam Workshop;
3. keep this repository as source/technical truth;
4. on future CA updates, run guard preflight first and use the native relocation playbook only if guarded addresses fail.
