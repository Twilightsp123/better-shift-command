# Documentation Maintenance Protocol

Use this checklist for every future BSC maintenance package. The goal is that a new maintainer can understand the current state without reading half the repository or accidentally treating historical assumptions as current facts.

## 1. Before editing runtime code

Read in the order defined by `README_FIRST.md` / `MAINTAINER_INDEX.md`.

If the proposed change depends on a reverse-engineered semantic claim, update or cite `ASSUMPTION_LEDGER.md` **before** promoting it into a runtime gate.

## 2. During a maintenance stage

For each meaningful change, record:

1. **Observed problem** — exact symptom/log/runtime condition.
2. **Evidence** — what proves the problem and what is still inference.
3. **Hypothesis** — explicitly labeled; do not present it as fact.
4. **Single-variable change** — what code/behavior changed and what was intentionally untouched.
5. **Validation plan** — exact offline/Windows/WH3 test that can falsify the change.
6. **Result** — PASS / FAIL / INCONCLUSIVE, with artifact/log location.
7. **Remaining issue** — what is still open after this change.
8. **Superseded/retracted claims** — update the ledger immediately if a prior assumption is invalidated.

## 3. Required documents to update before creating the next ZIP

| File | Update when |
|---|---|
| `README_FIRST.md` | current stage, next required action, reading order changes |
| `docs/ARCHITECTURE_STATUS_*.md` | production architecture changes |
| `docs/OPEN_ISSUES.md` | any blocker/trade-off opens or closes |
| `docs/ASSUMPTION_LEDGER.md` | reverse-engineered fact status changes |
| `docs/TEST_MATRIX.md` | any gate is run or a new gate is added |
| `docs/CURRENT_BUILD_MAP.md` | build identity/RVA/guard changes |
| `docs/DECISION_LOG.md` | architecture policy/trade-off changes |
| `docs/VERSION_LINEAGE.md` | a new version stream/label is introduced |
| `docs/PROVENANCE.md` | baseline/archive origin changes |
| `docs/HISTORY_COVERAGE.md` | archive contents/gaps change |
| `docs/DEVELOPMENT_HISTORY.md` | append a closed/meaningful stage; preserve historical viewpoint but mark superseded claims |
| root `COREPATH_CHANGELOG.md` (or successor changelog) | exact candidate delta |
| `RELEASE_MANIFEST.json` | candidate identity/status/gates change |
| `SHA256SUMS.txt` | always regenerate last |

## 4. History rules

- Never delete an old failed approach merely because it is wrong; mark it `SUPERSEDED`, `RETRACTED`, or `ABANDONED` and preserve why.
- Never leave a historical section titled as if it is current proof after the claim is retracted.
- Historical documents may retain old ABI/version strings, but must contain a visible warning that current authority lives elsewhere.
- If a source artifact is not present, write **archive gap** rather than reconstructing it from later summaries.
- Nested archives must be indexed in `HISTORY_COVERAGE.md`.

## 5. Version naming rule

Do not use bare `RC1`, `RC2`, etc. in new shared documentation. Prefix the stream:

```text
BSC-CONV-RC2
NATIVE-MAP-RC7
COREPATH-RC8
SMARTGUARD-RC2
```

SC stages should be written as `BSC-SC1` ... `BSC-SC6` when ambiguity is possible.

## 6. BuildOnly boundary

A BuildOnly handoff must say whether source modification is forbidden. For CorePath RC8 it is forbidden: classify compile/link/test failures first and only change the smallest build-layer issue required by the recorded plan. Gameplay redesign belongs in a new maintenance stage, not inside BuildOnly.

## 7. Handoff summary template

Every future ZIP should make the following answerable from the first two documents:

```text
Candidate:
Upstream behavior baseline:
Target WH3 build/SHA:
What changed this stage:
What did NOT change:
Current proven facts:
Retracted/quarantined assumptions:
Offline validation status:
Windows validation status:
WH3 runtime status:
Release blockers:
Accepted trade-offs:
Exact next action:
Relevant patch/log/archive paths:
```

## 8. Integrity rule

When a documentation-only refresh is performed, preserve the pre-refresh docs under `archive/` and record a non-document/source hash audit. This makes it possible to prove that documentation cleanup did not silently alter runtime code.


## 9. Documentation contract gate

Before packaging, run:

```text
python maintenance_tools/check_documentation_contract.py
```

A failure means the handoff is not documentation-complete even if runtime tests pass. Fix the documentation inconsistency before generating `SHA256SUMS.txt`.


## 10. Approved-design vs implemented-runtime rule

A design document may be authoritative for the **next intended architecture** without being runtime truth. Such documents must be labeled `DESIGN ONLY` / `NOT YET IMPLEMENTED`, linked from `MAINTAINER_INDEX.md`, and promoted to current architecture only after the source/test/runtime gates named in the design have passed.

For `BSC-TPOL-D1`, every promotion stage must record:

```text
stage id (T1/T2/T3/T4)
source patch
behavior changed / behavior intentionally unchanged
offline regression
mutation result
Windows impact (if any)
WH3 runtime evidence
open regressions
current docs promoted? yes/no
```

## 11. Hidden policy scaffold rule

A future UI/configuration system may be scaffolded before exposure, but the stage must state which fields are merely reserved and which are runtime-wired. Hidden scaffolding must not silently change gameplay defaults. MCT adapters must feed one profile compiler/snapshot; they must not mutate scattered CFG globals directly.
