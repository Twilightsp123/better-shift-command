# N1 9.0.3 — RMB/Shift shared member update, spatial contacts and pose-rate correction

**2026-10-10. Exact supplied EXE:** `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`. Read-only, original-machine-code verification. P0 native Shift progressive-turn crowding remains **accepted**; no further user gameplay tests requested.

## Concrete result: separate principal motion from accessory pose and contact records

- Census of 38 original constructor-referenced actor vtables at virtual `+0x18` finds nine entry functions; `0x02F854AC` forwards to `0x03081EB4`. Actor types differ, so no universal field offset can be patched on every soldier.
- `0x02F83F44` advances type-specific local spline (`+0xB60`, fraction `+0xBCC`) and calls pose-rate writer `0x0315C1E4` via a distinct pointer loaded from `actor+0xC18`. This does **not** establish primary soldier desired velocity. Another actor type writes an xform matrix through `+0xBC8`; do not set all `+0xBCC` values equally.
- Original shared actor update: `0x03081EB4 → 0x0308489C → 0x030C6788` (direct calls `0x030824A6 / 0x03084B2C`). `0x0308489C` compares the two actors' pointer at `+0x80` and skips a contact path when equal (`0x03084996–0x030849A4`), as does `0x030C6788` (`0x030C67C2–0x030C67D0`). The verified outputs at `0x030C68D9/0x030C691A` are bitsets, counters, not direct changed velocity or steering target.
- Original **consumer/lifecycle** closes that subgraph: `0x030E0AA8 → 0x030D3D7C` (call at `0x030E0C9F`) moves contact current counts `+0xC3B0/+0xC3B8` into previous counters and clears contact bitsets through `0x02DB09D4`, resets this tick counters. Treating same-pointer contact skip as a ready-made intra-unit locomotion avoidance switch is false.
- The original actor movement update family is shared by normal RMB and queued Shift; this audited local contact branch does not contain a proven discriminant that explains their differing **trajectories**. Absence of a discrimination in this branch does not mean the engine never processes queue context in indirect callbacks.

## Exact-build code delivered

- `maintenance_tools/native_shift_re/audit_903_member_motion_contact.py` — strict executable digest, 18 opcode guards, 17 direct calls, 38 member method vtables; fail-closed read-only.
- `tests/test_native_shift_re_member_motion_contact.py` — 10 local automated contracts; GitHub workflow `n1-native-shift-re-static.yml` on research branch passed.
- Independently validated downloadable local evidence bundle `BSC_N1_903_RMB_SHIFT_MEMBER_MOTION_CONTACT_20261010.zip` includes the expanded standalone verifier, precise original disassembly extracts, evidence JSON, Windows PowerShell offline runner, and **18/18 original EXE-backed/offline tests** (SHA manifest and zip re-extraction verified). EXE not distributed.

**Patch safety:** `PATCH_AUTHORIZED=FALSE`. Do not modify shared `+0x80` contact gates, `+0xE0` post-pose displacement rates or subtype-dependent `+0xBCC`. The next actual native repair prerequisite is a producer-to-consumer edge for **primary on-foot soldier desired displacement, turn and same-unit spacing response**, with real native MOVE fanout reachability, not a generic speed limiter.
