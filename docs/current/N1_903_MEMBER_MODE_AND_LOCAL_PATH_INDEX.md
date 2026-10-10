# N1 — Same native MOVE; member-local action modes and local spline-segment progress (9.0.3)

**2026-10-10 | EXACT EXE STATIC result; gameplay repair NOT achieved.**
User-supplied EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, image base `0x140000000`. Build described by user as 9.0.3. Primary bug remains within-unit crowding and divergent headings at queued Shift turns; old Lua MOVE→ATTACK pause is a distinct regression.

## Original single-group dispatch and real member divergence

Original native unit MOVE → `0x0302DB44` → `0x030D5490` first invokes a **group strategy's virtual+0x48 once per fanout call** (`0x030D54CA`), then enumerates members and invokes each native member's virtual+0x368 (`0x030D550F`). Task callbacks can invoke another whole-group fanout, so this is **not** a claim that MOVE only generates targets once across its lifetime. This proves shared order/route generation with member-specific payloads, **not different high-level Shift orders**.

An exact-EXE census of the previously identified **38 relevant constructor-backed member VTables** shows **all 38 share virtual +0xE0 -> `0x0307897C`**. This is a concrete **per-member action-mode setter**: reads `member+0x104` (`0x03078980`), compares EDX, writes EDX into `member+0x104` (`0x030789A1`), then calls native member action-state processor `0x03078B1C`. Under certain prior mode transitions it also clears member-local fields `+0x23C/+0x1C8`.

Native shared receiver `0x0306B9F0` reads that member's mode at `0x0306BAD7`; for values 1 or 2 it dispatches to member virtual **+0x100** (`0x0306BB0E`), otherwise virtual **+0xE8** (`0x0306BB44`). The +0x100 path reaches `0x0315F4E0`, which sets mode 1 or 2 through +0xE0 (`0x0315F5C0 / 0x0315F5B9`); the +0xE8 path reaches `0x0315EC98`, which can set mode 0 (`0x0315F333 / 0x0315F35F`). **Thus native member responses to one common group packet can take genuinely different internal action paths without separate high-level orders.**

Crucial limit: `member+0x104` is **NOT** proved to be the local Shift waypoint-arrival Boolean or route leg number; its concrete setter clearly treats it as an actor mode with other side effects. Do **not** overwrite it en masse to 'synchronize' models.

## A real independent path-segment index exists, but in a *local controller*

In a member update routine, original `0x0306098B` loads controller **`member+0x2E0`**. It invokes this controller's virtual+0x628 at `0x0306099B`, checks controller status and may clear the member's +0x2E0 pointer at `0x030609F0`. One possible native virtual implementation is `0x0306F438`, which calls `0x0315BF14` at `0x0306F448`. The latter reads a distinct path object at its input `+0x80`, invokes path virtual+0x48 and +0x50 for count/segment, measures segment length and independently increments **local controller+0x18** (`0x0315C098`, `0x0315C0C3`) while updating local fraction +0x1C. This is an **actual local trajectory-segment traversal**, not a speculative spatial scalar.

**Object-identity check:** among the 38 relevant member VTables only **3** place `0x0306F438` in checked vtable slots (+0x628, +0x678 or +0xE48). The caller invokes +0x628 on a **separate member-associated `+0x2E0` pointer**, not on UnitRoot's original Shift queue. There is no verified dataflow equating controller+0x18 to the user's original queued `root+0x270` route/next click waypoint. Therefore **do not patch this index or force all member indices equal**. Different local physical trajectories can legitimately have different segment lengths.

## Causal conclusion and NO-GO for guessed fix

- **VERIFIED:** common native MOVE/group target fanout; independent member action-mode branching; a local controller can advance a lower-level path segment.
- **UNPROVED:** original Shift waypoint completion is model-local rather than group-local; whether the action modes or controller interpolation cause visible model crowding; concrete safe ABI/detour in the original formation/steering path.
- **NO-GO:** `member+0x104` forced modes, `controller+0x18` synchronized segment indices, task+0xB8 (already disproved to be arrival), OrderHead, native state4/flag hacks or a new Lua/C++ scheduler.

This is a **falsifiable static architecture result**, NOT a working mod. A causally identified original formation-policy predicate and real runtime model-heading evidence are still necessary before any controlled native patch can be justified.

**Exact read-only evidence packaged in conversation:** `BSC_903_DEFINITIVE_LOCAL_AGENT_AUDIT_20261010.zip` (Python verifier, JSON original-EXE result, **31/31 instruction guards**, **4/4 E8 calls**, **38/38 member VTables**, **11/11 local tests**, 8 bounded disassembly excerpts, SHA256SUMS and Chinese report). No EXE, DLL, PACK, Windows Hook or WH3 test.
