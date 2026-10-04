# Architecture Status — 2026-09-29

Formal maintained Mod version: **v1.3.0**. Internal labels such as CorePath RC8 / TPOL-T1H describe implementation lineage, not the release version.

## 1. Current production/runtime architecture

Current v1.3.0 runtime retains the CorePath RC8 architecture with the Move-VTable correction:

`player command → Native capture/journal → canonical Lua action/block → SC1–SC4 route logic → verified Native issue/ACK → V3 exact active execution → SC6 reconcile → CA locomotion`

Attack observation/hold remains FEG-based. SC5 still runs only after exact current Exit-MOVE execution is confirmed. Physical Entity/Component/ContactPair evidence remains quarantined/staged-disabled.

Native identity:

- Bridge `1.0.18-corepath-wh3-fec656f4-map902`;
- 16 mandatory hooks;
- target WH3 9.0.2 SHA `fec656f4...3785`;
- Full top-level Move VTable `0x03913618`;
- Attack VTable `0x03912988`;
- static map/dataflow validation PASS; Windows/runtime validation PENDING.

## 2. Native validation state

WH3 9.0.1 / Bridge 1.0.17 remains the last runtime-validated baseline. The current branch carries a WH3 9.0.2 / Bridge 1.0.18 build candidate whose 16 mandatory guards and Move/Attack constructor/VTable dataflow are statically verified. Do not inherit the 9.0.1 Windows/runtime PASS into the 9.0.2 candidate.

### Prior runtime closure achieved on 2026-09-29

The corrected bridge runs in WH3 without the old `OWNED_OUTCOME_INDETERMINATE` failure caused by the wrong top-level Move VTable. This closes the address/outcome blocker sufficiently to expose remaining gameplay policy behavior.

## 3. Current gameplay limitations now visible

### 3.1 Strict Move→Attack boundary

Current `route_handoff_ready()` explicitly returns `ATTACK_REQUIRES_ROUTE_COMPLETE` for Move→Attack until current Move `semantic_done`. This can allow CA arrival braking / stop before Attack is issued.

### 3.2 SC6 immediate-MOVE asymmetry

Current `reconcile_native_successor()` only permits the immediate future action to be adopted if `future.type == ATTACK`. An exact immediate future MOVE is classified as `NATIVE_FUTURE_OVERRUN` and rolled back even though it may be the correct next canonical action.

Runtime evidence exists in `runtime_evidence/20260929_transition_policy/`.

## 4. Approved next architecture — not yet implemented

`BSC-TPOL-D1` introduces a Transition Policy Plane between canonical semantics and execution coordination.

Key properties:

- one evaluator for proactive dispatch and SC6 reconciliation;
- hard invariants separated from soft timing/precision policy;
- Smooth is the default profile;
- Move→Attack gets a bounded terminal handoff corridor;
- exact immediate successor MOVE can be adopted when Move→Move policy permits;
- bounded adopt-only hysteresis prevents near-boundary rollback thrash;
- MCT configures only soft policy through an immutable per-battle `PolicyProfile`.

Full design: `docs/design/BSC_TRANSITION_POLICY_ARCHITECTURE_D1.md`.

## 5. Lifecycle is a separate stream

Battle-complete / desktop / main-menu hang investigation is **not** part of Transition Policy D1. Current safe-stop and UI-listener observations remain tracked separately in `OPEN_ISSUES.md`. Do not combine lifecycle and smoothness changes in one patch.

## 6. TPOL-T1H implementation status

The hidden policy/profile scaffold is now implemented in controller source.

- no visible MCT UI exists;
- no MCT dependency is required;
- built-in hidden source is authoritative for this stage;
- `engagement_hold_seconds=3.0` is wired to the existing 3000 ms Attack hold requirement;
- movement policy values are schema-only/reserved and do not yet change gameplay;
- T2 smoothness behavior remains pending.
