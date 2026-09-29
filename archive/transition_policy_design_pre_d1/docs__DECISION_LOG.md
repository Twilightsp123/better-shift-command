# Decision Log

## D-20260927-01 — Quarantine physical Entity evidence

**Decision:** EntitySnapshot, Component layout, Alive virtual call, and ContactPair owner mapping are not release prerequisites for BSC CorePath RC8.

**Reason:** the BSC behavior audit showed command/ACK/SC6 identity is the authoritative transition source; Center-A2 route semantics already prevent physical evidence from vetoing route completion. The physical layer was inherited from Evidence V3 and had acquired release importance without equivalent provenance. A key `Entity+0x18` proof was retracted, and RC7 runtime could not find the presumed component/backref pair.

**Consequence:** production capability bits for physical evidence are false; production physical APIs fail closed; explicit diagnostic APIs/research source remain available for future reverse work.

## D-20260927-02 — ContactPair is optional, not core

**Decision:** mandatory hook count is 16. ContactPair is a separate optional static site and is staged disabled.

**Reason:** current SC1–SC6 command path and SC5 CorePath fallback do not require the mid-function ContactPair hook. Removing it from authorization lowers update/ABI risk without deleting research.

## D-20260927-03 — Safe stop only on desktop quit

**Decision:** keep hooks resident across normal battle completion. Disable all bridge-owned MinHook detours only when `button_windows` is clicked.

**Reason:** RC7 showed successful disable, and leaving allocator/free hooks live into process teardown was a plausible exit-hang source. However, a one-shot `platform_stop_observer()` cannot be used on every battle Complete because subsequent battles in the same WH3 process must still work.

**Trade-off:** cancelling the desktop-quit confirmation after the click can leave BSC stopped until WH3 restart. This is intentionally safer than carrying hooks into process teardown.


## D-20260927-04 — Current-state docs outrank historical narrative

**Decision:** maintenance handoffs use an explicit document authority/read order. `DEVELOPMENT_HISTORY.md`, Native changelogs, and archives preserve history but cannot override current Architecture/Issues/Assumption/Test/Build-Map documents. Bare `RCx` labels are prohibited in new cross-stream maintenance notes.

**Reason:** this package contains multiple independent RC number lines and historical sections whose terminology (`validated Entity`, old Native ABI, ContactPair production role) was later superseded. Reading only a portion of the history can therefore produce a technically plausible but current-state-wrong conclusion.

**Consequence:** `MAINTAINER_INDEX.md`, `VERSION_LINEAGE.md`, `OPEN_ISSUES.md`, `HISTORY_COVERAGE.md`, and `MAINTENANCE_PROTOCOL.md` are part of the required handoff surface. Historical text is preserved rather than rewritten as if it never happened.


## D-20260929-01 — Correct Full Move VTable; reject historical sole-VTable assumption

**Decision:** the CorePath top-level Move outcome and active-execution identity use Full Move VTable `0x03910AA8`. `0x0390E248` is retained only as the documented sibling Simple/Intercept Move VTable and must not authorize a top-level BSC Move outcome.

**Evidence:** direct disassembly of the locked EXE SHA `6c104a63...3297` proves allocator `0x02F5248C` returns `slot_base`, top-level Move `0x030344D4` passes `slot_base+0x18` to Full Move constructor `0x0300B094`, and that constructor installs `0x03910AA8`. Attack remains `0x03910228`. The prior current-state docs conflated `0x0300B038` / `0x0390E248` (Simple/Intercept Move) with the hooked top-level Move path.

**Consequence:** R1 allocator-index, R2 container-scan, and R3 constructor-witness experimental branches are withdrawn; the allocator ABI itself was not the fault. Core fixtures are corrected so portable PASS can no longer be obtained by modeling the wrong Move VTable. Per-kind native calibration is also hardened so a partial/no-sequence outcome cannot count as successful calibration.
