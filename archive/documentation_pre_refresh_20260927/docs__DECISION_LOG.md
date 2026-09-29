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
