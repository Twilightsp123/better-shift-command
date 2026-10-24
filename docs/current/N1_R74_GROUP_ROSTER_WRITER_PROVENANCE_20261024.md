# BSC R74 — Group roster writers and previous-group detach (2026-10-24)

**Grade:** original matching EXE static reverse engineering, offline synthetic negatives. No process Hook, no gameplay patch, no proved Shift crowding causality.

Matching Warhammer3.exe SHA256: 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496; 232531920 bytes; ImageBase 0x140000000. All sites below are RVA.

## Exact producer and consumer chain

1. Original Group vtable 0x03914450 has +0x00 = 0x030CC50C and +0x08 = 0x030E2480. Constructor 0x030C7CB8 installs this table and its 0x030C7DBC initializer zeros Group+0x20 (capacity/count) and Group+0x28 (array pointer).
2. A native Group/route-configuration path at 0x03032C92 calls 0x030209EC to build a Group, later entering route configuration 0x030179B0 at 0x03032CC8. This does NOT by itself prove a player's specific queued Shift instance uses the path.
3. The root Group builder enumerates Root+0x184/+0x188 and calls 0x030E54EC at 0x03020A4E for each member. Ordinary and derived member vtables share virtual +0x3F8 = 0x008F41E0, a concrete getter of member+0x300 (previous Group). When non-null, member transfer clears member+0x300 and calls old Group vtable+0x08 at 0x030E5532 before attaching to the new Group.
4. Group remove 0x030E2480 reads old Group+0x24/+0x28 and can do strategy-gated swap-last (0x030E24F5) and decrement count (0x030E24F9); alternative policy invokes strategy +0x70 and 0x0154CE4C. It is NOT unconditional swap-last.
5. Member transfer tail-jumps 0x030CC4AC. That routine passes newGroup+0x20 to generic 8-byte vector append 0x01325DA4. Its count is header+4, pointer header+8; on capacity growth, 0x01325DE5 replaces the pointer before copying old elements, then 0x01325E2C increments count. Generic helper cannot be labelled Group-only without its typed callsite.
6. The newly built Group is assigned to Root+0x32F8 at 0x03020A75 only after the member-transfer loop and subsequent Group postprocessing. Building a new Group does not mean a partially populated new Group is automatically public through Root+0x32F8; however the same build can already mutate the previous Group via member detach.
7. R73 B2 sender 0x0326A994 retains its Group pointer but reloads Group+0x28 at 0x0326AA44, dispatches member vtable+0x368 at 0x0326ABAF and re-reads Group+0x24 at 0x0326ABBD. These are matching Group roster field types, not a proven concurrent same-instance race.

## Conditional counterexample and negative evidence

Suppose a B2 sender holds old Group [A,B,C] and has already dispatched A; if another actor were concurrently transferring B to a new Group under swap-last, old Group would become [A,C], and B2's next read could dispatch C. **This is a synthetic hypothetical schedule only; no WH3 overlapping threads or skipped member event has been captured.** The bounded sender/producer code has no locally demonstrated immutable roster snapshot, but external engine task serialization/locks have not been excluded.

## Verification

Local exact game EXE: **88/88 opcode and GNU objdump instruction-start guards, 12/12 direct E8, 9/9 PE unwind functions, 2 Group and 2 member virtual method entries, 24/24 unittest PASS including the original EXE**. GitHub receives a 45-pin focused subset, all 12 E8, type-method guards, a SHA verifier and public synthetic tests. The complete 88-pin verifier, 11 bounded disassemblies, tests and R73 archive are in separately delivered BSC_R74_GROUP_ROSTER_MUTATION_PROVENANCE_20261024.zip; the commercial executable is not redistributed.

## Next bounded R75 decision

Inspect only whether an old B2 sender and a concurrent Group rebuild/member-detach can overlap in actual native job scheduling and ownership. If same-instance overlap cannot be established, mark ROSTER_RACE_CAUSAL_LINK as BLOCKED/DEPRIORITIZED and return to original per-model world-goal/steering/integrator coherence. **Never patch Group count/pointer, invent a global lock, or install an unproven game Hook.**

root_cause_proven=false; concurrent_roster_mutation_observed=false; live_hook_authorized=false; gameplay_patch_authorized=false; main_unchanged=true.