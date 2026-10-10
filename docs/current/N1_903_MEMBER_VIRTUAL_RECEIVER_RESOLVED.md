# N1 WH3 9.0.3 — Native group-member virtual +0x368 RESOLVED

**STATIC machine-code finding, 2026-10-10 — NOT yet a gameplay patch.** Original user EXE SHA256 `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`, PE image base `0x140000000`. Independent VERSIONINFO check not performed.

## Original route-to-member dispatch is now followed through the VTable

Prior exact-file chain: original MOVE issuer `0x030323C8` -> `0x0302DB44` native route update -> `0x0301B8E4` build group from root A members -> `0x0301287C` configure original unit route -> `0x030D5490` generate indexed 0x30-byte records and issue per-member payload (type byte `0x26`) via virtual **+0x368** at `0x030D550F`.

**New actual receiver proof:** The same member's group-association virtual **+0x3F8** (used twice at `0x030E047E/0x030E048F`, with associated `member+0x300` cleanup at `0x030E0495`) resolves, on an original constructor-backed VTable family, to **`0x008F37B0`: `mov rax,[rcx+0x300]; ret`**.

The read-only resolver independently scans exact-original `.xdata` for entries `vtable+0x3F8 -> 0x008F37B0` and `vtable+0x368` member handling, **then** checks real executable x64 RIP-relative `lea` references to each candidate VTable. All **38/38** matching VTable bases have at least one such original executable reference.

| Virtual +0x368 original function RVA | Constructor-referenced VTables | Function role |
|---|---:|---|
| **`0x0306B9F0`** | **36** | Full member-specific native payload handler |
| `0x0306B9CC` | 1 | Delegates to object at `member+0xD08` when non-null, otherwise common handler |
| `0x03117CE0` | 1 | Specialized preprocessing and calls common handler |

**These are code-address/vtable relationships, not proof that all 38 types are playable soldier models.** Constructor-like LEAs establish that tables are used in original code; precise runtime type membership still needs tracing.

## Native per-member action and coordinate updates

`0x0306B9F0` takes member in RCX and the per-member original payload in RDX, checks nested native context and flags (including `payload+0x50 & 0x20`, `payload+0x51 & 2`), may reinitialize local subobjects `member+0x490/+0x4A8`, and uses `member+0x104` to dispatch either:

- **member VTable +0x100** at `0x0306BB0E`;
- **member VTable +0xE8** at `0x0306BB44`.

Actual method targets observed in the 38 original VTables include:

- **`+0xE8 -> 0x03073224`**: calls `0x0315EC98` at `0x0307328B` and subsequently native `0x03078B1C` / `0x03056ED4`;
- **`+0x100 -> 0x03073568`**: calls **`0x0315F4E0`** at `0x03073571`, then native `0x03078B1C` / `0x03056ED4`.

In `0x0315F4E0`, original instructions **write member-specific coordinate/angle fields**: values from incoming data to `member+0x88` and `member+0x90` (RVA `0x0315F52C/0x0315F53E`), a 16-bit orientation-like value to `member+0xB0` (`0x0315F54C`), and update `+0x108/+0x155` flags before dispatching another native virtual +0xE0. Separate `0x03056ED4` reconstructs cached local route data at `member+0x910` and may set `member+0x930` using `0x0312D088`.

**Important type/semantics limit:** `+0x88/+0x90` are also read by the original unit member aggregator as position-like values. They are NOT proved to be “desired next waypoint” rather than current/initialized pose. `+0xB0` is orientation-like, not a proven per-model next-leg index. Avoid falsely claiming completion logic is found.

## Remaining N1 causal blocker

The original virtual dispatch and its concrete member coordinate writers are now identified. Still **not** verified: which original state tells each model it has reached the active waypoint, whether member A and B can progress to different *leg indices* on one shared order, whether group route phase is already atomic, and the safety of altering the engine's formation policy. This must be proved before Native Patch or unit-wide arrival tuning.

**Repro:** exact-SHA, read-only `n1_903_member_dispatch_vtables_verify.py` in [downloadable local bundle](sandbox:/mnt/data/BSC_N1_903_MEMBER_RECEIVER_RESOLVED_20261010.zip) checks **16 exact opcode sites**, locates all 38 VTables and constructor-like xrefs, and exports method mappings as JSON. Local tests **7/7 PASS** including real SHA-matched EXE. Bundled LLVM disassembly and SHA manifest; EXE excluded. No gameplay DLL or PACK, no in-game verification.

Full local report in bundle: `N1_903_MEMBER_VTABLE_RECEIVER_RESOLVED.md`.
