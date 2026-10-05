# Maintainer Index — read this before history

This file is the **navigation authority** for this maintenance package. Its purpose is to prevent a maintainer from reading one historical branch, one RC number, or one old architecture description and treating it as the current design.

## 1. Document authority

When documents disagree, use this order:

1. **Runtime/source truth:** current source and build-locked guards.
2. **Current-state docs:** `ARCHITECTURE_STATUS_20260929.md`, `OPEN_ISSUES.md`, `ASSUMPTION_LEDGER.md`, `TEST_MATRIX.md`, `CURRENT_BUILD_MAP.md`.
3. **Implemented TPOL scaffold + approved-next design:** `docs/design/HIDDEN_MCT_INTERFACE_T1H.md` describes the implemented hidden profile scaffold; `docs/design/BSC_TRANSITION_POLICY_ARCHITECTURE_D1.md` and companion docs describe later T2/T3 behavior. Implemented source wins where the design remains future-facing.
4. **Current decisions:** `DECISION_LOG.md`.
5. **Version identity / provenance:** `VERSION_LINEAGE.md`, `PROVENANCE.md`, `HISTORY_COVERAGE.md`, root `RELEASE_MANIFEST.json`.
6. **Change description:** root `COREPATH_CHANGELOG.md`, `src/native_bridge/CHANGELOG.md`.
7. **Historical narrative:** `DEVELOPMENT_HISTORY.md`.
8. **Archives / old patches / old test instructions:** `archive/`.

A lower tier can explain **why** something happened, but it cannot silently override a higher-tier current fact.

## 2. Current state, not history

Current runtime baseline / design stage:

- formal maintained Mod version: **v1.3.0**;
- upstream gameplay behavior ancestry: **v1.2.2**;
- current controller version: `1.3.0`;
- native candidate: `1.0.17-corepath-wh3-6c104-movevtfix`;
- target WH3 SHA: `6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297`;
- mandatory hooks: **16**;
- physical Evidence V3 production gate: **QUARANTINED**;
- ContactPair runtime: **STAGED_DISABLED**;
- Smart Guard runtime: **STAGED_DISABLED**;
- current runtime stage: Move-VTable correction built and exercised in WH3; gameplay smoothness/lifecycle work remains open;
- transition design stream: **`BSC-TPOL-D1`**;
- implemented substages: **`BSC-TPOL-T1H`** hidden profile/MCT scaffold + **`BSC-TPOL-T1`** shared behavior-neutral TransitionPolicy evaluator + **`BSC-TPOL-T1.5`** execution-lineage separation + **`BSC-TPOL-T1.6`** committed-edge transaction protocol;
- visible BSC MCT UI: **not registered**;
- movement transition behavior: still the pre-T2 CorePath SC1–SC6 baseline; T1 centralizes decisions, T1.5 separates execution lineage, and T1.6 makes transition commitment transactional, but none changes transition permission.

## 3. What each document answers

| Document | Use it to answer | Do not use it for |
|---|---|---|
| `ARCHITECTURE_STATUS_20260929.md` | What runtime is now vs what D1 is approved to become | Historical archaeology |
| `OPEN_ISSUES.md` | What is unfinished now | Listing every old failure |
| `design/HIDDEN_MCT_INTERFACE_T1H.md` | What policy/MCT scaffold is actually implemented now | Claiming T2 movement behavior is live |
| `design/BSC_TRANSITION_POLICY_ARCHITECTURE_D1.md` | Approved next transition architecture | Claiming unimplemented T2/T3 behavior is already live |
| `design/MCT_POLICY_SCHEMA_D1.md` | Stable user-facing preset/slider model | Raw Native/RE settings |
| `design/TRANSITION_POLICY_MIGRATION_D1.md` | Stage order and promotion gates | Skipping directly to all-at-once implementation |
| `design/TRANSITION_POLICY_TEST_PLAN_D1.md` | Tests required for D1 promotion | Treating design intent as PASS evidence |
| `ASSUMPTION_LEDGER.md` | What reverse-engineered fact is proven/unverified/retracted | Gameplay chronology |
| `TEST_MATRIX.md` | What has actually passed | Inferring semantics from a unit test alone |
| `CURRENT_BUILD_MAP.md` | Current build-locked RVAs/guards | Other WH3 builds |
| `DECISION_LOG.md` | Why architecture/trade-off decisions were made | Raw version chronology |
| `VERSION_LINEAGE.md` | Which `RC2`, `SC5`, `v1.0.16`, etc. belongs to which stream | Detailed implementation |
| `PROVENANCE.md` | Where current baselines/archives came from | Current bug status |
| `HISTORY_COVERAGE.md` | Which eras are fully/partially preserved | Treating gaps as evidence |
| `DEVELOPMENT_HISTORY.md` | Long narrative of problems/solutions | Current authority |
| `src/native_bridge/CHANGELOG.md` | Native-bridge evolution | BSC Controller release status |
| `archive/` | Reproduce/inspect old work | Current release gating |

## 4. Fast triage rules

Before proposing a fix, answer in this order:

1. Is the problem in `OPEN_ISSUES.md`, or is it a newly observed regression?
2. Which version stream owns it? Use `VERSION_LINEAGE.md`.
3. Does the proposed fix rely on a reverse-engineered field? Check `ASSUMPTION_LEDGER.md` first.
4. Does an existing decision prohibit/promote this architecture? Check `DECISION_LOG.md`.
5. Which test gate would prove the fix? Update `TEST_MATRIX.md` and the package-specific test instruction.
6. Only then read the relevant section of `DEVELOPMENT_HISTORY.md` / archive for context.

## 5. Important current prohibitions

- Do not restore `Entity +0x18 = MovementComponent*` as fact; it is **RETRACTED**.
- Do not make Entity/Component/Alive/ContactPair a CorePath release prerequisite without a new promotion decision in `ASSUMPTION_LEDGER.md` + `DECISION_LOG.md`.
- Do not count ContactPair as the 17th mandatory hook in RC8.
- Do not stop the observer on normal battle completion; safe-stop is Quit-to-Windows only.
- Do not treat `current_target()`, UI command lines, sticky `melee`, or ACK alone as exact execution identity.
- Do not interpret one bare `RCx` label without its version stream.

## 6. Historical reading rule

`DEVELOPMENT_HISTORY.md` preserves what engineers believed **at that time**. Where it discusses Evidence V3, EntitySnapshot, MovementComponent, ContactPair, or old Native ABI strings, read those passages as historical unless a current-state document explicitly re-promotes the claim.

When a future maintainer discovers a conflict, fix the navigation/current-state docs first and record the resolution in `DECISION_LOG.md`; do not simply delete the historical record.

## 7. D1 promotion rule

`BSC-TPOL-D1` remains the design stream. `BSC-TPOL-T1H`, `BSC-TPOL-T1`, `BSC-TPOL-T1.5`, and permission-neutral `BSC-TPOL-T1.6` are implemented. T1.7 policy-envelope normalization, T2 gameplay behavior and T3 visible MCT are still future work. The 2026-10-05 direct T2/passthrough experiments are historical evidence, not current runtime authority. Source behavior wins any disagreement with a design-only or historical section.
