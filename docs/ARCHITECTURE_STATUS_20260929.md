# Architecture Status — 2026-09-29

Formal maintained Mod version: **v1.3.0**. Internal labels such as CorePath RC8 / TPOL-T1H describe implementation lineage, not the release version.

## 1. Current production/runtime architecture

Current v1.3.0 runtime retains the CorePath RC8 architecture with the Move-VTable correction:

`player command → Native capture/journal → canonical Lua action/block → SC1–SC4 route logic → verified Native issue/ACK → V3 exact active execution → SC6 reconcile → CA locomotion`

Attack observation/hold remains FEG-based. SC5 still runs only after exact current Exit-MOVE execution is confirmed. Physical Entity/Component/ContactPair evidence remains quarantined/staged-disabled.

Native identity:

- Bridge `1.0.17-corepath-wh3-6c104-movevtfix`;
- 16 mandatory hooks;
- Full top-level Move VTable `0x03910AA8`;
- Attack VTable `0x03910228`.

## 2. Runtime closure achieved on 2026-09-29

The corrected bridge runs in WH3 without the old `OWNED_OUTCOME_INDETERMINATE` failure caused by the wrong top-level Move VTable. This closes the address/outcome blocker sufficiently to expose remaining gameplay policy behavior.

## 3. Current gameplay limitations now visible

### 3.1 Move→Attack T2-B runtime closure

The strict Move→Attack boundary has been replaced by the bounded `ATTACK_TERMINAL_CORRIDOR`. The 2026-10-05 WH3 9.0.2 runtime smoke records successful `ATTACK_TERMINAL_HANDOFF` events without the old Attack rollback pattern. T2-B is runtime verified.

### 3.2 T2-A immediate-MOVE adopt-only candidate

`reconcile_native_successor()` now permits an **exact immediate i+1 MOVE** to soft-adopt only when the current Move is already inside the existing bounded dispatch/steering window. The path is adopt-only: it grants no new proactive Move issue permission, keeps i+2+ rollback, exact execution identity, prior route debt, short-leg protection, and Exit-route separation. Offline T2-A is 11/11 PASS plus mutation protection; WH3 RT-TP-04/05 is still pending.

## 4. Approved architecture — partially implemented

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

## 6. TPOL-T1H + partial T2 implementation status

The hidden policy/profile scaffold is implemented, and two bounded gameplay slices now exist under the built-in default behavior.

- no visible MCT UI exists;
- no MCT dependency is required;
- built-in hidden source remains authoritative;
- `engagement_hold_seconds=3.0` is wired to the existing 3000 ms Attack hold requirement;
- T2-B Move→Attack terminal handoff is WH3 9.0.2 runtime verified;
- T2-A exact immediate Move reconciliation is an offline-tested adopt-only candidate awaiting RT-TP-04/05;
- movement policy values are still not profile-driven; T1 shared evaluator, T2-C hysteresis and T3 visible MCT remain pending.
