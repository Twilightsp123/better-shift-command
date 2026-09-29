# READ THIS FIRST — BSC Transition Policy Architecture D1

Design stream: `BSC-TPOL-D1` — approved design, **not already implemented** in runtime source.

> **Package type:** design/maintenance handoff. Runtime source is intentionally unchanged from the corrected CorePath RC8 Move-VTable baseline. Do not treat the D1 design as already implemented.

## Mandatory reading order

1. `README_FIRST.md` — package identity and current stage.
2. `docs/MAINTAINER_INDEX.md` — authority order.
3. `docs/ARCHITECTURE_STATUS_20260929.md` — current runtime vs approved-next architecture.
4. `docs/design/BSC_TRANSITION_POLICY_ARCHITECTURE_D1.md` — full D1 design.
5. `docs/design/TRANSITION_DECISION_TABLE_D1.md` — exact transition rules.
6. `docs/design/MCT_POLICY_SCHEMA_D1.md` — presets/advanced settings.
7. `docs/design/TRANSITION_POLICY_MIGRATION_D1.md` — staged implementation order.
8. `docs/design/TRANSITION_POLICY_TEST_PLAN_D1.md` — falsifiable gates.
9. `docs/OPEN_ISSUES.md` — current unresolved work.
10. `docs/ASSUMPTION_LEDGER.md` — reverse-engineered facts/retractions.
11. `docs/TEST_MATRIX.md` — what has actually passed.
12. `docs/DECISION_LOG.md` — accepted architecture decisions.
13. `docs/VERSION_LINEAGE.md` — version-stream disambiguation.
14. `docs/DEVELOPMENT_HISTORY.md` — history only; not current authority.

If documents conflict, follow `MAINTAINER_INDEX.md`. Proposed D1 design does not override current source until its migration gates pass.

## Current runtime baseline

- Upstream gameplay baseline: **BSC v1.2.2**.
- Controller: `1.2.2-corepath-rc8`.
- Native Bridge: `1.0.17-corepath-wh3-6c104-movevtfix`.
- Target WH3 SHA256: `6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297`.
- Mandatory Native hooks: **16**.
- Full top-level Move VTable: `0x03910AA8`.
- Attack VTable: `0x03910228`.
- Physical Entity/Component/ContactPair evidence: **QUARANTINED/STAGED_DISABLED**.

## Runtime result that motivated D1

The Move-VTable repair closed the prior Native outcome failure: the bridge loads as `1.0.17-corepath-wh3-6c104-movevtfix` and no longer immediately dies on every Move.

After that closure, gameplay logs exposed two Lua-policy problems:

1. current Move→Attack is intentionally strict until `semantic_done`, allowing CA arrival braking before Attack handoff;
2. SC6 only treats an immediate future **ATTACK** as adoptable. Exact Native execution of an immediate future **MOVE** is still classified as overrun and rolled back.

D1 is a gameplay-policy redesign for those issues. It requires **no new EXE reverse engineering**.

## Approved D1 principles

- Default preset: **Smooth**.
- Canonical action order remains non-negotiable.
- Manual RMB/REPLACE remains highest authority.
- Exact Attack target identity remains mandatory.
- One shared TransitionPolicy evaluator serves both proactive dispatch and SC6 Native reconciliation.
- Native `i+1` MOVE may be adopted when the same Move→Move policy permits it.
- Move→Attack gains a bounded terminal handoff corridor instead of waiting only for full semantic completion.
- A bounded adopt-only hysteresis band prevents rollback/advance thrashing near transition boundaries.
- MCT controls only soft policy. It can never disable hard invariants or Native proof requirements.

## Implementation rule

Do **not** implement all of D1 and MCT in one patch.

Use the stages in `TRANSITION_POLICY_MIGRATION_D1.md`:

```text
T1 behavior-neutral evaluator refactor
→ T2 Smooth-default behavior correction
→ T3 MCT presets/custom controls
→ T4 Attack/Exit tuning
```

Each stage must have its own patch, regression result, mutation result and WH3 evidence before promotion.

## Separate unresolved stream

Battle teardown / observer suspend-resume and third-party battle-UI listener errors remain separate from Transition Policy D1. Do not hide a lifecycle fix inside gameplay policy work.
