# Open Issues — CorePath RC8

This file contains **only current unresolved work and accepted current trade-offs**. Historical failures belong in `DEVELOPMENT_HISTORY.md` / archives, not here.

**2026-09-29 current source note:** the locked EXE outcome dataflow audit proved the prior top-level Move VTable map was wrong. This tree contains the source correction (`0x03910AA8`) and therefore requires a fresh Windows BuildOnly/candidate before runtime. The older Windows DLL/candidate must not be reused.

## A. Release-blocking pending gates

| ID | Status | Required evidence | Notes |
|---|---|---|---|
| O-01 Windows v142 + MASM BuildOnly | PENDING | clean Release build of current source | no gameplay/source redesign during BuildOnly |
| O-02 Windows Native CTest | PENDING | all Windows tests pass, including backend/module/mid-function smoke | ordinary MinHook entry-hook success is not a substitute for the mid-function fixture |
| O-03 Current EXE inspection | PENDING ON WINDOWS | target SHA matches and **16/16 mandatory core guards** match | optional ContactPair/Smart Guard sites reported separately, not release prerequisites |
| O-04 PE toolchain verification | PENDING | AMD64 + VS2019/v142 contract passes | must be recorded with build artifacts |
| O-05 Deterministic candidate pack | PENDING WINDOWS DLL | pack rebuild exact-match; embedded Bridge/MinHook hashes match inputs | PREBUILD ZIP itself is not install-ready |
| O-06 WH3 CorePath runtime smoke | PENDING | behavior matrix below | final install-candidate gate |

### WH3 runtime matrix for O-06

- Move→Move steering continuity.
- Move→Attack boundary remains strict.
- Attack→Exit Move disengagement.
- Exit→Attack transition.
- ordinary RMB cancel.
- SC5 bounded fallback on exact current Exit MOVE stall.
- SC6 early-successor rollback.
- SC6 legal-successor adopt.
- multi-unit behavior (no four-unit batching regression).
- second battle in the same WH3 process still works.
- Quit-to-Windows safe-stop and process exit behavior.

## B. Accepted current trade-off

### O-07 Quit confirmation cancellation

`stop_observer()` is triggered from the Quit-to-Windows click path. If the user cancels the subsequent quit confirmation, BSC may already be stopped until WH3 restart.

Status: **KNOWN / ACCEPTED FOR RC8**. Do not “fix” this by moving safe-stop to ordinary battle completion; that would break later battles in the same process.

## C. Quarantined research questions — not release blockers

| Research question | Current status | Release impact |
|---|---|---|
| actual semantic identity of historical member-array entries named `Entity` | unverified | none in RC8 |
| true Entity→MovementComponent relationship | historical `+0x18` proof retracted; RC7 pair search found 0 | none in RC8 |
| movement-state field semantics on a proven current component | unresolved | none in RC8 |
| `vt+0x630` exact alive semantics/class binding | partial evidence only | none in RC8 |
| ContactPair current-build ownership chain | static site retained, staged disabled | none in RC8 |
| Smart Guard current-build runtime path | static site retained, staged disabled | none in BSC CorePath |

Research may continue, but a new promotion to production requires the three-part rule in `ASSUMPTION_LEDGER.md` and a new decision entry.

## D. Closed historical issues that must not be reopened by default

- `Entity +0x18 = MovementComponent*` is not “pending verification”; the old proof is **RETRACTED**. A new proof must start from zero provenance.
- BSC-CONV-RC1/RC2 is an abandoned convergence branch, not the next release candidate.
- ContactPair is not the missing 17th CorePath hook in RC8.
- Physical evidence failure does not by itself block BSC CorePath release.

Update this file whenever a release blocker is opened/closed. Do not leave a closed item here merely for history; move the outcome to `DEVELOPMENT_HISTORY.md` / `DECISION_LOG.md` instead.


## E. Static-audit caveat retained intentionally

The supplied 2026-09-29 disassembly reports prove allocator return ABI, top-level constructors, VTables, slot geometry, sequence write, and payload locations. However their prose has one unresolved control-flow inconsistency: both Move and Attack reports show the queued-count `>= 40` branch targeting an address later labeled `AL=1`, while the narrative calls it rejection and the sequence report claims accepted-without-sequence is impossible. CorePath therefore **retains `ACCEPTED_NO_SLOT` as a valid fail-safe state** and does not delete that contract based on the report summary. This caveat is not a blocker for the Move-VTable correction.
