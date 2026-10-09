# T2-MOVE-F — isolated offline safety hardening (NOT WH3 promoted)

Date: 2026-10-09. Parent E HEAD: `21417a8c652e6ca54801c66813581a46f01699d2`.
Working branch: `maintenance/t2move-f-audit-hardening`.
Draft review: https://github.com/Twilightsp123/better-shift-command/pull/1

## Scope

Preserve A/B/C/D/E transition logic, SC1–SC4 route geometry, T1.6 transaction/cursor authority,
all Native Bridge address/ABI hooks, and T2-B Attack handoff. Harden **only** experimental
Native exact-immediate MOVE reconciliation.

## Reproduced E baseline risks

E baseline plus the new real-controller F boundary fixture was executed by GitHub Actions
run `37819203083`. Existing A/B/C/D and E controller/mutations were green before the F
boundary step. In the new fixture:

- **F-RISK-01 FAIL on E**: exact V2 fallback promoted an immediate MOVE even though the
  E contract requires trusted V3 execution identity.
- **F-RISK-02 FAIL on E**: Native live revision changed without a drained Journal row,
  while the E proof still matched the cached Lua revision; an old MOVE was committed.
- **F-RISK-03 PASS on E**: ordinary matching V3 MOVE correctly promoted.

These are **synthetic real-controller fixtures**, not observed WH3 gameplay failures.

## F behavior repair

`R1.T2MoveEPreview()` now:

1. Requires `ctx.execution_provider == "V3"`. Other controller consumers may continue to use
   their original V2-compatible adapter; there is no global ABI or policy change.
2. Calls `bridge.get_unit_revision(st.uid)` immediately before permission and rejects
   missing/invalid or mismatched live revision against both `st.revision` and the frozen cache.
3. Preserves all D cache generation/revision/action identity, one-poll freshness and
   route-debt signature revalidation, A/B timing-and-corridor proof, and the T1.6
   `OBSERVED -> COMMITTED` transaction.

The provider is passed from the exact Native execution observation in SC6. Changes
are mirrored in `source/better_shift_command.lua`, `src/better_shift_command.lua`,
and `src/better_shift_command_selfcontained.template.lua`.

## Required offline gates

- F real-controller: V2 rejection, live revision drift rejection, normal V3 adoption,
  changed SC3 debt signature, fail-closed unavailable revision.
- E real controller 11/11, original E mutation gate with expanded F behavior checks,
  independent F guard mutants, A/B/C/D, documentation contract, original 46-job maintenance.
- Verify three controller mirrors and zero Native/address/CFG differences relative to E.
- Record exact GitHub Action run/result and candidate SHA only after execution, not in advance.

## Remaining risk / promotion status

Do not publish or merge F into E, T2-B or release. WH3 RT-TP-02/03 (T2-B)
and RT-TP-04/05 (T2-MOVE) are **BLOCKED/DEFERRED**.
135°/180° hairpins, dense short-leg routes, multi-unit fairness, multiple simultaneous
SC3 debts and native event race adversarial testing remain future expansion gates,
not implied PASS merely by the F evidence-guard tests.

The E source handoff artifact `11530553790` is an **E** archive, not a F archive.
Root `SHA256SUMS.txt` predates F and must not be used as a F package manifest.

## Verified CI evidence

- Original E regression exposure: [Actions `37819203083`](https://github.com/Twilightsp123/better-shift-command/actions/runs/37819203083): F-RISK-01 and F-RISK-02 FAIL on unchanged E, F-RISK-03 PASS.
- Hardened F candidate: [Actions `37820591847`](https://github.com/Twilightsp123/better-shift-command/actions/runs/37820591847) SUCCESS: all A/B/C/D/E and F gates, documentation contract and full maintenance.
- F real controller **5/5 PASS**. F guard mutants **3/3 CAUGHT** (V2 fallback, live revision drift, fabricated missing revision).
- E real controller **11/11 PASS**. E active controller mutants **8/8 CAUGHT**, including an expanded dynamic SC3 debt-completion fixture catching bypassed D revalidation.
- Existing maintenance suite **46/46 PASS** (see Actions job for individual test output). **WH3 gameplay: NOT TESTED**.
