# READ THIS FIRST — BSC CorePath RC8 PREBUILD

This archive is a **maintenance/prebuild candidate**, not a Steam/GitHub release and not an install-ready pack.

The purpose of RC8 is to remove an unverified historical physical-evidence model from the release-critical path without deleting its research history. The current WH3 build is locked to SHA256:

`6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297`

## What changed

- 16 command/packet hooks remain mandatory for BSC core behavior.
- ContactPair is no longer a mandatory hook; its current site is retained as an **optional static research map** and is staged disabled.
- Smart Guard remains an independent optional static map and is staged disabled.
- EntitySnapshot / MovementComponent / Entity Alive / ContactPair physical evidence is **QUARANTINED** in production APIs.
- SC1–SC6 route/command behavior remains based on command identity, ACK/journal facts, exact active-order identity, route semantics, FEG, and bounded SC5 recovery.
- SC5 can recover a stalled exact Exit MOVE using positive live contact/proximity + near-zero speed + bounded stall, without Entity data.
- RC7 native safe-stop is retained. Production only disables process-wide hooks on an explicit **Quit to Windows** click; normal battle completion does not stop the observer, so later battles in the same WH3 process remain possible.

## Why this exists

The old physical model used names such as `Entity`, `MovementComponent`, and `Entity::is_alive`. One key claimed proof was retracted: the old `Entity +0x18 = MovementComponent*` attribution was actually a `ResultRecord +0x18 = Controller*` access. RC7 runtime also found a 60-member physical candidate but found zero valid Entity→Component back-reference pairs. Those facts do not prove the physical data is useless; they prove it is not safe to make it a release prerequisite.

## Current validation

Portable/offline status in this archive:

- Controller source jobs: **19/19 PASS**
- Mutation gate: **40/40 CAUGHT**
- Portable Native CTest: **13/13 PASS**
- ASan/UBSan Native CTest: **13/13 PASS**
- Prebuild source contract: **PASS (16 core + 2 optional sites)**

Still required before any install/test pack:

1. Windows VS2019 v142 x64 + MASM BuildOnly.
2. Pre/post-build current EXE inspection: SHA match + **16/16 mandatory core guards**. Optional ContactPair/Smart Guard sites are reported separately.
3. Windows CTest including backend/module/mid-function smoke.
4. PE toolchain verification.
5. Deterministic candidate pack build and embedded DLL/MinHook SHA verification.
6. WH3 runtime core-path smoke: Move→Move, Move→Attack, Attack→Exit Move, Exit→Attack, RMB cancel, SC5 fallback, SC6 rollback/adopt, multi-unit, and Quit-to-Windows safe stop.

Do not ask a build agent to redesign or “fix” the source during BuildOnly. Use `ANTIGRAVITY_BUILD_ONLY.txt` exactly.
