# 1.0.18-corepath-wh3-fec656f4-map902 — WH3 9.0.2 static map candidate

- Target EXE SHA256 `fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785`.
- Migrates Native address ownership to `native_maps/CURRENT` + generated `wh3/generated_native_map.hpp`; runtime C++ no longer owns a second manual RVA table.
- Seven-stage maintenance pipeline resolved all 16 mandatory hooks and both optional static sites.
- Normalized relocation was required for halt/free and structural relation resolution for Move/Lua Move/Move handler and publish sites.
- Re-derived current allocator `0x02F53128`, Full Move constructor `0x0300BDC0`, Attack constructor `0x0300B8C4`, Full Move VTable `0x03913618`, and Attack VTable `0x03912988`.
- Simple/Intercept sibling remains separate at constructor `0x0300BD64` / VTable `0x03910438`; it is not top-level Move outcome identity.
- Physical evidence and optional ContactPair/Smart Guard policy are unchanged: quarantined/staged disabled.
- Status: **STATIC VERIFIED BUILD CANDIDATE**. Windows v142/MASM, Windows Native CTest and WH3 runtime smoke remain pending.

---

> **NATIVE-BRIDGE HISTORY ONLY.** This changelog has its own Native version/RC stream and does not define the current BSC Controller release. For current package status and RC disambiguation, read `../../docs/MAINTAINER_INDEX.md` and `../../docs/VERSION_LINEAGE.md`. Historical entries may contain physical-evidence claims later quarantined by CorePath RC8.

# CorePath RC8 Move-VTable correction — 2026-09-29

- Direct current-EXE dataflow audit proves top-level `Order::issue_move` (`0x030344D4`) calls Full Move constructor `0x0300B094`, installing VTable `0x03910AA8`.
- Historical/current-map `0x0390E248` is the sibling Simple/Intercept Move constructor VTable and is retracted as the top-level Move outcome identity.
- `BridgeHost::outcome()` and CorePath active execution identity now use `0x03910AA8`; Attack remains `0x03910228`.
- Allocator ABI is explicitly vindicated: `0x02F5248C` returns exact `slot_base` in RAX; no allocator-index/container-scan/constructor-witness replacement is used.
- Per-kind accepted calibration now requires a complete slot-bearing native outcome so a partial decoder result cannot authorize the first owned issue.
- Core fixtures are corrected to use the full Move VTable and include a regression that the old Simple/Intercept VTable cannot calibrate the top-level Move path.
- `ACCEPTED_NO_SLOT` remains supported; the supplied static report contains an unresolved queue-full branch/return contradiction and does not justify deleting the historical no-slot contract.

# CorePath RC8 maintenance candidate — 2026-09-27

- Target build: WH3 SHA256 `6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297`.
- 16 mandatory command/packet hooks; ContactPair separated as optional staged-disabled physical research site.
- Smart Guard remains optional staged disabled.
- Production physical Evidence V3 APIs quarantined; command execution identity remains available.
- Command issue authorization no longer depends on Component/Alive diagnostic gates.
- RC7 safe observer disable retained.
- Status: PREBUILD; Windows v142/MASM and WH3 runtime smoke pending.

---

# RC7 Component Layout + Safe Stop Diagnostic

- RC6 runtime bound a unique 60-slot evidence root, then failed at the first soldier with `MOVEMENT_BACKREF_MISMATCH`; RC7 adds bounded read-only component-layout discovery instead of guessing offsets.
- Requires exactly one Entity->component / component->Entity backreference pair across independent soldiers and revalidates the result across the full soldier array.
- Movement-state fallback is fail-closed; zero-filled historical `+0x8B0` is not accepted as live evidence for a discovered pair.
- Validates Entity vtable and `vt+0x630` target as executable without calling it before Component Gate.
- Alive diagnostic revalidation uses the discovered offsets only after the Component Gate publishes them.
- Adds `stop_observer`: queues disable for all bridge hooks and applies it while keeping the pinned bridge, MinHook backend, and trampolines resident.
- Diagnostic shutdown calls `stop_observer`; Quit-to-Windows has a best-effort early stop listener to avoid carrying allocator/free detours into engine teardown.
- Hook/VTable map is unchanged; Smart Guard remains staged disabled. Production EvidenceProbe and ContactPair layouts are intentionally not auto-migrated from an unverified runtime scan.

# RC6 Root Discovery Diagnostic

- Added fail-closed evidence-root discovery after RC5 runtime proved the strict Lua userdata resolver no longer matches the current WH3 wrapper layout.
- Preserved command roots and physical/evidence roots as separate object identities.
- Added optional `lua_objlen`-bounded userdata graph scan and expected deployment soldier-count discriminator.
- Added native command-root observation fallback and bounded read-only pointer graph scan.
- Added `diagnostic_command_root_v3` and `diagnostic_bind_evidence_unit_v3` Lua diagnostics.
- Diagnostic harness now waits for one normal user MOVE if userdata-only discovery fails; it never issues commands itself.
- Removed duplicate diagnostic log emission.
- Hook/VTable map remains unchanged from Phase 6.2; Smart Guard remains staged disabled.

# v1.0.16 diagnostic RC4 — 2026-09-26

- Pre-gate evidence-root resolution no longer calls EntitySnapshot / Entity::is_alive; it uses read-only stable container + finite position validation.
- Component runtime gate is root-bound and revokes prior Alive proof whenever re-probed.
- Alive diagnostic requires the same component-verified root and keeps two-stage deployment/casualty proof.
- Begin-issue rechecks runtime gates so a stale armed state cannot outlive revoked physical evidence.
- Lua diagnostic alive-count input is finite/integer/range checked (0..300).
- Current EXE verifier dynamically parses 17 core guards plus the independent Smart Guard guard and verifies executable sections.
- Diagnostic harness retains the battle epoch until end_battle succeeds, requires pristine deployment, and uses exact UID handling.
- Smart Guard remains staged disabled for the first new-build runtime gate test.

# v1.0.14-r1-evidence-v2

- Controller-side second-charge semantic hotfix release; Native dual-root ABI retained with version lock bump.

# v1.0.13-r1-evidence-v2

> **Historical evidence semantics:** this section records the v1.0.13-era interpretation. CorePath RC8 later quarantined this physical model as release proof, and the specific `Entity+0x18 = MovementComponent*` attribution was retracted.

- Evidence V2 exposes raw order/entity/combat facts; Lua owns R1 semantic verdicts.
- Entity liveness used the then-current `Entity::is_alive` interpretation; RC8 does not treat that class/slot semantic as production-proven.
- **RETRACTED AS CURRENT PROOF:** the v1.0.13 line attributed MovementCollisionController provenance to `Entity+0x18`; RC8 found the cited proof was actually a different `ResultRecord+0x18 = Controller*` access. Historical `+0x74` / `+0x8B0` sampling remains research-only.
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
