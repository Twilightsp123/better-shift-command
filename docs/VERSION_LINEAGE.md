# Version Lineage — disambiguation map

The project has several independent numbering systems. A bare label such as `RC2` is therefore ambiguous and must not be used in new maintenance notes without a stream prefix.

## 1. Version streams

**Current formal Mod version: `v1.3.0`.** All RC/D1/T1H labels below are engineering lineage labels unless explicitly listed as a public release.

| Stream | Examples | Meaning | Current status |
|---|---|---|---|
| BSC behavior/research | R1, R3, R3.1, R3.2, R4 | Controller/evidence research milestones | historical; R3/R4 contain superseded physical assumptions |
| BSC convergence experiment | RC1, RC2 | broad cleanup/convergence branch | **abandoned**, not a baseline |
| Steering / command behavior | SC1–SC6 | single-problem gameplay fixes | SC1–SC6 behavior forms the modern gameplay lineage |
| Public/formal BSC releases | v1.2.0, v1.2.1, v1.2.2, **v1.3.0** | formal Mod version line | current formal maintained version = **v1.3.0**; v1.2.2 remains upstream behavior ancestry |
| Native Bridge versions | 0.1.1, 0.4.x, 0.5.x, 1.0.x | native observer/identity/issuing/evidence evolution | current candidate = `1.0.17-corepath-wh3-6c104-movevtfix` |
| WH3 current-build remap/diagnostic | RC4, RC5, RC6, RC7, RC8 | native map/runtime-gate work for WH3 9.0.1 current EXE | current = **CorePath RC8** |
| Transition-policy architecture | BSC-TPOL-D1 / T1H / T1 / T1.5 / T1.6 / T1.7 / G1 / G1.1 / T2-B | staged gameplay/MCT architecture; no new Native RE | **T1–T1.7 + G1 validated; T2-B G1.1 offline validated / WH3 pending; T2-MOVE pending** |
| Smart Guard diagnostics | its own RC labels | separate optional Smart Guard investigation | staged disabled; never identify by bare `RCx` in shared docs |

### Naming rule for new docs

Use explicit prefixes:

- `BSC-CONV-RC2`
- `BSC-SC5`
- `BSC-v1.2.2`
- `NATIVE-v0.5.0`
- `NATIVE-MAP-RC7`
- `COREPATH-RC8`
- `SMARTGUARD-RC2`

## 2. BSC Controller / gameplay chronology

### R1 / R2 — early lineage, incomplete archive

The current package still contains `R1.xxx` code/test naming (`r1_v3_*`, R1 helpers), proving this lineage predates R3. However, there is no complete R1/R2 maintenance narrative or original handoff bundle in this package. Treat details beyond surviving code/tests as **unknown**, not as something to reconstruct from names.

### R3 → R3.2

- R3: second-Attack / Exit-body-cohort problem; Frozen ExitBodyCohort solution under the then-current physical-evidence architecture.
- R3.1: emergency Lua 5.1 `>200 locals` load fix.
- R3.2: structural namespace/closure fix to keep long-lived top-level locals under control.

### R4 — historical Evidence V3 production architecture

R4 introduced/strengthened the physical-evidence architecture and pending-lane changes. Some R4 semantic claims were later weakened or retracted during RC5–RC8. R4 is a historical milestone, **not** current proof that the physical model is valid.

### BSC-CONV-RC1 / BSC-CONV-RC2 — abandoned branch

A broad convergence/cleanup attempt modified too many runtime/maintenance surfaces at once and produced regressions that could not be cleanly attributed. RC2 diagnostics also hit model-time/timer/callback failures. This branch was abandoned; it is not a release baseline.

### SC1 → SC6

- SC1: steering corner handoff.
- SC2: earlier steering window.
- SC3: soft route debt for Move→Move while preserving unresolved waypoint obligations.
- SC4: bounded stall escape before CA arrival braking fully stops the unit.
- SC5: bounded recovery when accepted Exit MOVE does not produce timely disengagement. The original v1.2.0 implementation depended on then-current physical evidence; CorePath RC8 keeps the bounded recovery concept but uses exact current Exit execution + positive live contact/proximity + low speed/no-progress instead of Entity gating.
- SC6: exact active-execution reconciliation; adopt legal immediate successor, rollback early/overrun execution, and do not authorize transitions from `current_target()` alone.

### v1.2.x release line

- v1.2.0: SC1–SC5 behavior closure and release telemetry cleanup.
- v1.2.1: SC6 V3 exact execution-identity reconciliation.
- v1.2.2: Lua `math.huge` compatibility update over v1.2.1 behavior.
- v1.3.0: formal maintained version; current maintenance tree includes the Move-VTable correction, T1–T1.7 architecture, validated G1 observation and an offline-validated T2-B G1.1 construction candidate. This internal candidate does not change the public version and still awaits WH3 runtime promotion.
- `1.2.2-corepath-rc8`: maintenance candidate, not a public release; changes production Native evidence wiring, not the upstream gameplay baseline.

## 3. Native Bridge chronology

The detailed implementation history is in `src/native_bridge/CHANGELOG.md`; this section only gives the navigation landmarks.

- `0.1.1-observer-floatabi`: early observer-only era; original Lua clients are preserved under `src/native_bridge/tests/original/`.
- v0.2.1 → v0.2.2: early observer client/environment correction lineage.
- 0.4.1 → 0.4.9: integrated Host/IdentityGate/PacketTracker, packet provenance, handler scope, byte lineage, calibration, and callback-scoped experimental publication.
- v0.5.0: Attack native token + documented real-game runtime closeout PASS for the experimental integration gate.
- 0.5.3 / 0.5.4: recoverable-partial and pending-recipient-guard hardening.
- v0.6.0: referenced by the preserved queue-probe client, but this package does not contain a full dedicated changelog narrative for that version.
- v1.0.3, v1.0.7, v1.0.11, v1.0.13, v1.0.14: later BSC/native version locks and evidence evolution; see Native changelog.
- `1.0.15-r4-evidence-v3-validated-userdata-root`: historical pre-CorePath ABI used by v1.2.0/v1.2.1-era documentation.
- `1.0.16` current-build diagnostics: WH3 9.0.1 remap/gating line.
- `1.0.17-corepath-wh3-6c104-movevtfix`: current PREBUILD candidate.

## 4. WH3 9.0.1 current-build map line

- **NATIVE-MAP-RC4:** current-build diagnostic hardening and 17-core-hook-era gate.
- **NATIVE-MAP-RC5:** current-build static map / first runtime-gate candidate. Patch evidence is preserved inside the RC7 original archive.
- **NATIVE-MAP-RC6:** command-root-anchored physical-root discovery; established that command root and physical candidate are distinct. Detailed RC6 summary/patch is nested inside the RC7 original archive.
- **NATIVE-MAP-RC7:** component-layout discovery attempt + safe observer stop. Runtime found the physical candidate (`slot_count=60`) but zero valid component back-reference pairs; safe-stop reported success.
- **COREPATH-RC8:** removes physical evidence from release-critical authorization, reduces mandatory hooks from 17 to 16, keeps optional ContactPair/Smart Guard static sites staged disabled, and preserves RC7 safe-stop for desktop quit only.

## 5. Disambiguation examples

`RC2 failed` is unacceptable in a new note. Write either:

- `BSC-CONV-RC2 failed because ...`, or
- `SMARTGUARD-RC2 ...`, etc.

Likewise, `RC7 passed` is incomplete. For this package the precise statement is: `NATIVE-MAP-RC7 safe-stop runtime logged PASS, while the Entity→Component pairing hypothesis failed (0 valid pairs); COREPATH-RC8 runtime is still pending.`


## 6. BSC-TPOL-D1 — approved next gameplay architecture

Opened after the Move-VTable correction made CorePath operational enough to expose remaining smoothness policy issues.

D1 is **not** a runtime version. It defines:

- shared transition evaluation for proactive dispatch and SC6;
- bounded Move→Attack terminal handoff;
- immediate future MOVE adoption when legal;
- adoption hysteresis;
- Smooth/Balanced/Precise/Custom MCT policy profiles.

Implementation promotion stages remain staged. T1–T1.7 and G1 are validated; T2-B G1.1 is offline validated but not WH3-promoted; T2-MOVE/T3/T4 remain pending. Do not write `D1 fixed` until all relevant runtime gates pass.

## 7. BSC-TPOL-T1H — hidden policy/MCT scaffold

First implemented substage of the D1 migration. It adds the internal immutable PolicyProfile schema and future MCT adapter boundary while preserving existing gameplay decisions. No MCT UI is registered. `engagement_hold_seconds=3.0` becomes the policy source for the existing 3000 ms attack hold; all movement transition settings remain reserved until T2.


## 8. BSC-TPOL-T1 — shared evaluator

Implemented 2026-10-05 from the pre-T2 CorePath/T1H behavior baseline. It centralizes Move transition decisions behind `R1.TransitionPolicy.evaluate()` for proactive dispatch, SC6 reconciliation, and scheduler urgency while intentionally preserving old decisions. T1 is structural, not a gameplay release.

## 9. 2026-10-05 direct T2 experiment line

- direct T2-B terminal Attack candidate: useful runtime evidence; no Attack pause observed; later reverted from current source pending proper T2 migration;
- direct T2-A immediate-MOVE adoption: not promoted; fold-back self-compression observed;
- T2-A hairpin restriction: not promoted; stepwise rollback/reassert observed;
- Native Move passthrough diagnostic: isolation experiment only; rejected as product architecture because BSC exists to improve Move→Move behavior rather than surrender it to vanilla Shift.


## 10. BSC-TPOL-T1.5 — execution lineage

Implemented 2026-10-05 on top of restored T1. It separates the player's captured Native order identity from any later BSC-issued/ACK identity while preserving the exact T1 transition decisions. Runtime exposes `PLAYER_NATIVE` versus `BSC_ISSUED` lineage to the shared reconciliation context. This is a structural prerequisite for T2-A/T2-C, not a gameplay release.

## 11. BSC-TPOL-T1.6 — committed-edge transaction

Implemented 2026-10-05 on top of T1.5. It introduces an explicit edge transaction lifecycle and moves canonical handoff commitment from Native submission time to verified ACK / exact Native adoption. Both paths use `Core.commit_transition_edge()`. Transition permission, SC1–SC6 geometry, CFG scalars, immediate-MOVE rollback, and strict Move→Attack remain unchanged. This is the execution-protocol prerequisite for T1.7/T2, not a gameplay promotion.


## 12. BSC-TPOL-T1.7 — consumer-neutral policy envelopes

Implemented as a permission-neutral structural stage on top of T1.6. The evaluator no longer branches transition permission by consumer identity. It emits separate issue/adopt envelopes; advance and SC6 interpret those envelopes while keeping T1.6 gameplay permission unchanged. Immediate future MOVE adoption remains closed and Move→Attack remains strict until T2.


## 13. BSC-TPOL-T2B-G11 — ordinary Move→Attack dual-envelope candidate

Implemented/offline-validated 2026-10-07 on the `maintenance/t2b-terminal-attack` stream. G1.1 adds stopping-point coherence on top of behavior-neutral G1. T2-B keeps issue and adopt permission distinct, reserves one-poll travel for adopt-only synchronization, caches exact-current pre-promotion decisions for SC6, and grants `ATTACK_TERMINAL_HANDOFF` only through the T1.6 commit transaction.

This is an internal construction label, **not** a public Mod version. Offline gate is 46/46 PASS; WH3 RT-TP-02/03 remains pending. Immediate future MOVE adoption is not part of this stage.
