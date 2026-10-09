# T2-MOVE-C — T1.6 OBSERVED/COMMITTED integration simulator

**Status: OFFLINE TRANSACTION SIMULATION ONLY — NOT CONTROLLER-WIRED.**
Date: 2026-10-08. Baseline: `maintenance/t2move-a-shadow` at `f6cfae10ae58ef93e54bb22bbc45b52822543194`.

## What C accomplished

1. A/B are the sole permission evidence: exact pre-promotion `MOVE→MOVE` issue / ADOPT_ONLY, still explicitly `authoritative=false`.
2. C models the transaction interface of real `Core.begin_transition_txn` and `Core.commit_transition_edge` using a deterministic mock. The only success path is `AUTHORIZED → OBSERVED → COMMITTED`. **No Native issue occurs.**
3. The core authority derives route credit from `geometry.route_mode` (matching T1.6) rather than a new invented credit: `STEERING_CORNER` completes the old Move, `PATH_SAFE` registers the old waypoint obligation, `COMPLETE` does not award another credit.
4. Generation, canonical plan revision, exact current/successor object identities, unit lifetime, one-poll freshness, and prior debt signature are checked before the simulated transaction. Any preexisting pending/transaction state blocks the operation.
5. No `i+2` movement, identity mismatch, noncanonical order, stale cache, or changed route-debt identity can authorize a transaction.

## Integration blocker discovered — do not misreport as READY

The current real `transition_geometry_snapshot()` omits several fields used by B's permission proof, including **`leg`, `progress`, `route_min_progress`, `threshold`, `stall`, `cut_safe_limit`**, and other mode details. Reusing that snapshot for Native pre-promotion MOVE admission would make live geometry weaker/incomplete than the tested A/B fixtures.

C therefore requires a *dedicated move-only pre-promotion snapshot* containing the exact fields used by A/B. It is **not implemented in the live controller**. A second mapping is needed for **stable prior route-debt signature** tied to route-debt action IDs/tolerance/current block revision. A raw table identity or untracked `st.route_debts` alias is not acceptable.

`test_t2move_c_snapshot_contract.py` explicitly detects these missing fields as an expected blocker, verifies T2-B stage and live MOVE hard-closed state, and must be converted into a positive mapping contract before any gameplay enablement.

## GitHub validation — 2026-10-08

GitHub Actions run `37718568414` **SUCCESS**. Exact source/template snapshot audit found six missing mandatory MOVE-proof fields: `cut_safe_limit`, `leg`, `progress`, `route_min_progress`, `stall`, `threshold`. A/B and the existing maintenance suite remain green. No controller byte changed.

## Validation and next work

- C simulated T1.6 scenarios: **25/25 PASS**.
- C transaction/identity/commit mutations: **14/14 CAUGHT**, excluding syntax-only mutations.
- A/B remain independently validated (A 20/20 and 12/12; B 28/28 and 20/20).
- WH3 remains **unavailable**, including T2-B RT-TP-02/03.
- Next: (1) implement and test dedicated Move evidence snapshot and route-debt revision identity, (2) run a zero-permission, shadow-only controller fixture to verify exact current MOVE sample ordering, (3) only after that create one **isolated**, explicitly gated A+B+C integration candidate, still not a production promotion.
- **Do not** modify Native/address, SC1–SC4 scalar CFG, T2-B G1.1, or the production MOVE adopt envelope to sidestep these blockers.
