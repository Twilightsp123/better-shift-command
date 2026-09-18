# v1.0.14-r1-evidence-v2

- Controller-side second-charge semantic hotfix release; Native dual-root ABI retained with version lock bump.

# v1.0.13-r1-evidence-v2

- Evidence V2 exposes raw order/entity/combat facts; Lua owns R1 semantic verdicts.
- Entity liveness uses the engine Entity::is_alive virtual method.
- MovementCollisionController provenance is Entity+0x18; +0x74 local state and +0x8B0 movement state are sampled separately.
- Post-exit Attacks use fresh Entity lock episodes tied to exact native order identity and intended CombatGroup target.
- Ordinary first Attacks keep the mature FEG path and do not globally depend on Entity V2 availability.

# v1.0.11-r1-evidence

- Version lock for Better Shift Command v1.0.11; native hook mechanics unchanged from v1.0.7.

# v1.0.7-blocks

- Version lock for Better Shift Command v1.0.7.
- Keeps all v1.0.5 command/identity semantics.
- Native observer startup now reports exact MinHook hook/index/RVA/status instead of a generic `MINHOOK_CREATE_FAILED`.
- One bounded 50ms retry is allowed only for transient allocation/protection or null-trampoline anomalies; structural hook failures remain fail-closed.

# v1.0.3-contact-input

- Read-only modifier-key metadata captured at Windows native order entry.
- Foreground validity, left/right Shift, Ctrl/Alt and exact uint64 sample timestamp exported to Lua.
- Queued flags, identity matching, native trampoline signatures and existing hook guards unchanged.
- Portable tests cover metadata transport/export and preservation of queue/source semantics.
- Windows v142 build and game runtime remain separate required checks.

# v0.5.0 Runtime Closeout — 2026-09-13

- Real-game one-shot validation passed every required marker: calibration, experimental arm, verified Move ownership, stale revision rejection, player RMB external attribution, verified Attack ownership, and final VALIDATION_PASS.
- Archived the exact PASS result ZIP, script log, validation result, install receipt, and rollback result under `evidence/runtime_v050_pass/`.
- Rollback completed successfully (`state=ROLLED_BACK`).
- Native Bridge experimental integration gate is CLOSED; Controller development may begin.
- Production release flags remain intentionally false.

# v0.5.0 — Attack Native Token

- Preserves the runtime-passed Move, stale-revision, and player-RMB behavior from v0.4.9.
- Adds an experimental-only Attack native pending-token binding when the Attack packet-handler candidate is bypassed.
- Captures exact Attack target root/UID from producer command+0x88 and requires recipient root + queued + target root + target UID to match at native entry.
- Stale expected revision is still rejected by IdentityGate before native side effects.
- Adds `native_attack_token_bindings` telemetry and v0.4.9 runtime failure evidence.
- Production exact_source / verified_issue remain false.

# CHANGELOG

## 0.4.9 / 2026-09-12 — Callback-scoped experimental publication

- Real v0.4.8 runtime passed experimental calibration but failed immediately at `ONE_NATIVE_COMMAND_REQUIRED`.
- Experimental issue ownership no longer requires the Lua binding hook to fire. During the synchronous `issue_verified_command()` callback, exactly one same-thread publish may inherit the already-validated issue token.
- If the real command descriptor cannot be decoded, experimental builds carry forward the validated `kind/queued/unit/revision` from `begin_issue`; production builds remain strict and unchanged.
- A second publish is rejected. Callback scope ends before player input can be processed by this token path.
- `finish_issue()` preserves earlier metadata errors and reports `bindings/published/depth` when the one-command contract itself fails.
- Added runtime telemetry fields `last_issue_bindings`, `last_issue_published`, `last_issue_depth`.

# Changelog

## 0.4.8 / 2026-09-12 — Accepted native calibration gate

- Fixes the v0.4.7 runtime gate bug where experimental readiness required both assumed packet-handler kinds even though real WH3 accepted MOVE/ATTACK while only one handler kind was observed.
- Adds independent accepted-MOVE and accepted-ATTACK evidence at the native order entry.
- Experimental arm now requires accepted MOVE + accepted ATTACK + at least one real handler hit + zero capture/gate fault.
- Keeps the old two-handler condition as diagnostic telemetry only.
- Adds per-kind handler counters plus accepted-kind, capture-error, and gate-fault telemetry.
- Does not add first-match/FIFO/direct-native pending-token attribution; player-priority safety remains unchanged.
- Archives the v0.4.7 runtime failure and rollback evidence.

## 0.4.7 / 2026-09-12 — Experimental handler calibration + pending-token scope

- Stops blocking the controlled validation build on the unresolved producer→reader physical-address lineage.
- Experimental arming now requires only real Move and Attack top-level BCQ handlers to have executed during calibration.
- Production flags remain closed: `exact_source=false`, `verified_issue=false`, `release_approved=false`.
- For an experimental owned issue only, a single already-committed `pending_` controller token may bind to the matching handler kind when exact physical reader mapping is absent.
- Native entry still verifies exact recipient root, queued bit, and expected revision before the native call.
- After the pending token is consumed, external/player orders cannot inherit it and remain `UNKNOWN`.
- Adds telemetry `handler_calibration_ready` and `handler_token_bindings`.
- Archives the v0.4.6 real-game failure (`lin=0/0`, `hdl=2/0/2`) as evidence rather than treating physical lineage as proven.

## 0.4.6 / 2026-09-12 — Exact physical byte-lineage propagation

- Archived the real v0.4.5 HandlerScope failure: true packet handlers fired (`hdl=2/0/2`), the live reader exposed `0+83@7->83`, but exact packet restoration still missed and no verified command was issued.
- Replaced whole-span-only copy propagation with exact byte-range lineage fragments carrying `packet_offset`.
- Partial/split copies now propagate only their witnessed overlap; overwrites split surviving lineage rather than discarding untouched bytes.
- Handler resolution remains strict: a reader interval is attributed only when one packet lineage covers the entire interval contiguously from packet offset 0 with no gap/conflict/mixed identity.
- Added diagnostic-only reader lineage telemetry `last_reader_lineage_bytes / last_reader_lineage_fragments`, rendered as `lin=B/F` in validation logs.
- Added regressions for split reconstruction, partial-overlap offset preservation, gaps, mixed packets, and diagnostic coverage that cannot grant identity.
- Kept the 16 guarded native hooks and HandlerScope authority introduced in v0.4.5; selection parsing remains telemetry-only.
- Preserved calibration Attack cleanup and immediate-pass semantics for the final verified Attack.
- Production issue remains locked by default; no coordinate/time/FIFO/payload-content fallback was introduced.

## 0.4.5 / 2026-09-12 — Real packet-handler provenance scope

- Added byte-locked hooks for the actual BCQ Move handler `0x142D95F8C` and Attack handler `0x142D95A50`.
- Moved consumer source authority from generic `0x142DCAF24` selection parsing to synchronous handler-entry `PhysicalSpan` resolution.
- Added thread-local `HandlerScope`; downstream native Move/Attack can consume provenance only during the exact active handler call.
- Selection hook is telemetry-only and may fail or be absent without blocking source attribution.
- Added handler/reader telemetry (`handler_seen/resolved/missed`, reader fields/end).
- Preserved the v0.4.4 runtime failure evidence and the fact that verified Move was never issued in that run.
- Hook guard profile increases from 14 to 16.
- Added regressions proving handler attribution works with selection disabled and after backing-span retirement during the handler call.

## 0.4.4 / 2026-09-12 — Consumer reader / lifetime fix

- Archived the second real-game v0.4.3 failure: Publish/Writer/Copy/Stage all fired, Selection was `2/0`, spans fell from 2 to 0, and native attribution remained `0/0`.
- Reworked consumer packet resolution to use only raw-byte-proven invariants: `start = data + cursor - 7`, `end = data + ([reader+0x18] + [reader+0x1C])`; no semantic guess for the two boundary fields.
- Changed PacketTracker reader resolution to require an exact unique physical interval.
- Removed broad arena invalidation from `writer_begin()`; replacement now invalidates only the exact finalized packet interval.
- Changed copy retirement so an old destination allocation is released only when the destination allocation pointer actually changes.
- Once a consumer packet is physically resolved, its provenance is retained only for the same thread and same active Windows unwind `FrameIdentity`, allowing backing staging storage to be reclaimed before downstream native order entry without losing exact provenance.
- Added regressions for swapped reader-bound orientation, exact 7-byte header alignment, exact packet end, backing-span reclamation after consumer resolution, and unrelated later writer begin.
- Updated one-game validation so calibration ATTACK is immediately cleared by a normal Move after native acceptance; final verified ATTACK passes as soon as its exact Journal acceptance is observed.
- Preserved production lock: `exact_source=false`, `verified_issue=false`, normal build issue path disabled.

## 0.4.3 / 2026-09-12 — Publication metadata path fix

- Fixed real WH3 command-selection layout in `single_recipient`: count `+0x10`, capacity `+0x14`, subject array `+0x18`.
- Fixed Move `is_queued` offset from `+0xA9` (fast) to `+0xA8`; Attack remains `+0x99` per constructor evidence.
- External calibration packets keep a physical publication scope even when optional descriptor metadata is unavailable; owned commands remain strict/fail-closed.
- Added path-stage runtime telemetry and bounded `PATH_WITNESS_TIMEOUT` diagnostics.

## 0.4.2 / 2026-09-12 — Game-validation kit

- Added separate one-game experimental validation lane; production installer remains locked.
- Added transactional prepare/finish/rollback tooling.
- Corrected validation criterion: global release flags remain false; experiment is proven by exact Journal issue/source records.

## 0.4.1 / 2026-09-12 — Integrated bridge

- Integrated Native Host + IdentityGate + PacketTracker and 14 guarded Windows hooks.
- Added controlled Lua callback issue path, packet lifecycle tracking, Journal metadata, Windows PE checks, transactional candidate install/rollback, and baseline regression suite.
- Production issuing remains compile-time locked by default.


## 0.5.4-pending-recipient-guard / 2026-09-16

- Treat handler-level pending fallback as speculative until exact native recipient root and queued bit match.
- An unrelated same-kind native handler no longer causes `OWNED_RECIPIENT_NOT_VERIFIED` and global disarm.
- Exact physical-lineage owned packets remain fail-closed on recipient/payload mismatch.
- Hook RVAs, guards, command field offsets, and single-pending provenance model are unchanged.

## 0.5.3-recoverable-partial / 2026-09-16
- Splits Bridge observer/capture anomalies into recoverable telemetry vs fatal safety faults.
- `IdentityGate::observe_external_partial()` now advances accepted external revision and publishes observed fields without latching a permanent gate fault solely because optional external payload was unavailable.
- Recoverable anomalies preserve issuing only when IdentityGate/PacketTracker are healthy and no owned command is in flight.
- Exposes `fatal_errors`, `last_recoverable_error`, `last_recoverable_uid`, and `last_fatal_error` to Lua.
- Owned provenance/recipient/kind/outcome failures, native exceptions, gate faults, and tracker faults remain fail-closed.
- This change does not modify native hook RVAs, byte guards, command offsets, or the v142 build requirement.

## 1.0.3-contact-input / RC6 candidate

Four pending recipients maximum, one per UID; callback production remains same-thread and non-reentrant. Fallback selection occurs at native entry by recipient/root/epoch/kind/queued; Attack binds target, Move binds caller-provided finite xyz. Physical lineage takes precedence. Added native pipeline and float32 C API cases. Hook guards/IdentityGate core unchanged. Windows and real-game approval remain unperformed here.
