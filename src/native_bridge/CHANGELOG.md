# v0.5.1 — Per-Kind Calibration — 2026-09-15

- Experimental/global readiness now accepts either natural accepted MOVE or ATTACK evidence plus handler/fault guards, rather than requiring both kinds before any issue can arm.
- `begin_issue(MOVE)` still refuses until `accepted_move_seen`; `begin_issue(ATTACK)` still refuses until `accepted_attack_seen`.
- Lua module version is `0.5.1-per-kind-calibration`.
- Real-game TESTFIX B built with the validated v142-family toolchain passed hook installation and MOVE arming with `accepted_attack=false`.
- TESTFIX A built with a v143 toolchain loaded but failed runtime Hook creation (`OBSERVER_MINHOOK_CREATE_FAILED`); v1.0.1 release tooling therefore freezes v142-family builds rather than silently switching compiler families.
- No hook RVA/guard-table redesign was introduced by v0.5.1.

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
