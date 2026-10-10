# N1 — Slot-index binding under Shift turns: positive AND disconfirming evidence

**2026-10-10 — exact user WH3 EXE SHA256** `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`. User labels build 9.0.3. Base `0x140000000`. **STATIC/OFFLINE positive and negative results; actual Shift collision not yet demonstrated; no playable patch.**

See companion **BSC_N1_903_SLOT_IDENTITY_CROSSCHECK_20261010.zip** delivered in the chat. It has the complete Chinese report, standalone read-only exact-SHA verifier, 45 original x64 opcode byte guards, nine decoded original direct E8 edges, eight strategy vtable policy checks, one group vtable set, 15 passing tests, bounded original LLVM disassembly and SHA manifest, excluding the copyrighted EXE.

## Support: on this issuance path original member[i] receives target-record[i]

Original MOVE route updater `0x0302DB44` selects formation mode from `[[UnitRoot+0x3D48]+0x248]`; its direct `0x0302DB8E` calls `0x0301B8E4`, which iterates `root+0x184/+0x188` in pointer-array order, adding members through `0x030E0460` and append `0x01325434`. `0x0302DBDB` then calls original group fanout `0x030D5490`. Strategy virtual +0x48 generates 48-byte target records; dispatch loop `0x030D54D9/E6/F0` loads `record[i]` and `group_member[i]` by the **same index**, issuing member virtual +0x368 at `0x030D550F`. **There is no shortest-distance reassignment within that specific dispatch loop.** Previous mode3 study verified ordered target-record generation and grid index-to-record conversion without reordering the output vector.

**Conditional geometric mechanism:** If a 3×3 mode3 group retains member↔slot index between consecutive MOVE legs, the new slot frame is a 180° rigid rotation, and actors interpolate synchronously along straight paths without avoidance, every old `p_i` goes to `-p_i+T` and all nine coincide at half-progress `T/2`. This gives a clear collision *possibility* under one shared command. A bijection reassigning opposite-index slots preserves the goal position set but removes that one midpoint pile-up. This is **not a claim** about actual WH3 interpolation, ordinary Shift choosing mode3, or safe dynamic remapping.

## Real counterevidence: native group membership is not permanently index-invariant

`0x030E0460` obtains existing member group via virtual +0x3F8, clears `member+0x300`, calls old-group virtual +0x08 when present, then inserts into the new group via `0x030C7420`. Original group VTable `0x0390F5F0`: +0x00 = `0x030C7480` (write group back to member+0x300), +0x08 = `0x030DD3F4` (remove member), +0x20 = `0x030E0AA8` (post-fanout group processing).

In `0x030DD3F4` the *current strategy* virtual +0x60 decides the removal policy. For mode3 strategy VTable `0x0390F180`, +0x60 = `0x008D3330` (returns false). Then `0x030DD464/469` **copies the last member pointer into the removed index**, and `0x030DD46D` decrements group count. Example old group `[A,B,C,D]`, remove B -> `[A,D,C]`. Therefore group member index is **not immutable over member-removal events**. The eight constructor-referenced strategy vtables are split: four return false and use swap-last; four return true and use strategy +0x70 to choose a replacement index. **This is a substantive engine counterexample** to the claim that all units forever preserve identical group-member indices.

**But note the important limit:** the new group is rebuilt from UnitRoot's source array on this MOVE update path. If that **root source array remains in the same order**, old group's swap-last deletions do **not** automatically shuffle the *new* group. It is therefore **not a refutation of stable member-to-slot mapping during normal, no-casualty Shift turns**; it only shows there is no unconditional index-stability invariant.

## Separate counterevidence: engine does work after fanout

After emitting member tasks, the original fanout calls group virtual +0x20 at `0x030D5522` -> `0x030E0AA8`. The group method may call `0x030CCBDC` at `0x030E0B38` and `0x030E07C0` at `0x030E0BBA`, where record geometry/status is checked (`0x030E08DD` native call to `0x030E039C`; `0x030E08E2` comparison; `0x030E08EB` can set record +0x2C=1). **Therefore the original engine has additional group-level postprocessing, contrary to a blanket assertion of zero coordination.** There is as yet **no evidence that this remaps issued member targets or fully prevents physical collision**.

## Exactly what remains for causal verification and any patch

1. Which original strategy is used by the specific unit in an ordinary queued Shift 90°/180° turn? Mode3 is a **conditional** example, not demonstrated the default.
2. Does `UnitRoot+0x188` preserve the same identity order across these consecutive MOVE tasks? Root/member lifecycle and dead/blocked models matter.
3. How do the actual member-specific target vectors, controller trajectories and native avoidance update between orders? A facing code or a single assignment record does not prove an actual intersection.
4. Only if fixed-index assignment is established as the cause under ordinary Shift, consider a **one-shot constrained member↔record remapping BEFORE fanout**. Its orientation, neighbor graph, slot identity, contact geometry, stable mapping, native ABI and normal RMB/attack negative controls must all pass. **No raw member/slot writes, guessed Hook, controller reissue or performance claim yet.**

**Grades:** STATIC PASS for the specific byte-guarded issuance/removal/postprocessing paths; OFFLINE PASS for 15 tool/conditional geometry tests; WINDOWS NOT RUN; WH3 NOT RUN; SAFE PATCH/PLAYABLE MOD NOT YET ESTABLISHED.