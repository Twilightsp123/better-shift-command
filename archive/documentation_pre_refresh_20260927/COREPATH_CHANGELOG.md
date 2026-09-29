# CorePath RC8 Change Log

## Controller

- Candidate identity changed from upstream v1.2.2 to `1.2.2-corepath-rc8`; upstream source is frozen under `archive/upstream_v1.2.2/`.
- Added explicit `PHYSICAL_EVIDENCE_MODE = "QUARANTINED"`.
- Physical bind/snapshot/contact refresh is skipped in production controller mode.
- Physical capability bits are forced false even when an older/synthetic provider advertises them.
- SC5 uses exact current Exit MOVE identity plus positive contact/proximity, low speed and bounded stall when physical evidence is quarantined.
- Boot no longer hard-requires physical APIs.
- Added native `stop_observer` requirement and Quit-to-Windows UI listener. Safe stop is **not** run on normal battle Complete/Victory because the same WH3 process may enter another battle.

## Native Bridge

- Current WH3 SHA/RVAs remain the re-audited 6c104 map.
- Mandatory hook set reduced from 17 to 16 by removing ContactPair from core authorization.
- ContactPair guard retained separately and staged disabled.
- Smart Guard remains separately mapped and staged disabled.
- Command issue readiness no longer depends on Component/Alive diagnostic gates.
- Production physical V3 APIs fail closed with `PHYSICAL_EVIDENCE_QUARANTINED_COREPATH_RC8`.
- V3 capability table exposes execution identity from the verified core observer but all physical capabilities false.
- RC7 safe-stop implementation retained: queue-disable + apply; no hook removal, MinHook unload, trampoline free or bridge unload.

## Tests / maintenance

- Pre-CorePath physical tests are archived unchanged.
- Active SC5/v109 tests now assert non-gating physical evidence and CorePath fallback invariants.
- Mutation suite remains 40/40 caught.
- Maintenance entrypoints renamed/replaced with CorePath RC8 tools; stale v1.2.1 scripts archived.
- `inspect_exe.py` now reports 16 mandatory core sites and two optional sites separately.

Exact diffs are under `docs/patches/`.
