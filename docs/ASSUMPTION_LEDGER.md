# BSC Assumption Ledger — WH3 9.0.2 build candidate

This ledger separates facts from inherited names. A future maintainer must update the status here before promoting any reverse-engineered field into a release gate.

| Item | Current status | Release use |
|---|---|---|
| WH3 9.0.2 EXE SHA `fec656f4...3785` | current build-candidate identity lock; 9.0.1 `6c104a63...3297` retained as last runtime baseline | mandatory |
| 16 command/packet hook RVAs + guards | **9.0.2 STATIC VERIFIED 16/16 byte-exact**; Windows/runtime candidate build still pending | mandatory |
| Full Move VTable `0x03913618` for WH3 9.0.2 hooked top-level `issue_move` | **LEVEL-1 static dataflow candidate verified**; prior 9.0.1 value `0x03910AA8` remains historical baseline | command outcome + SC6 execution identity |
| Simple/Intercept Move VTable `0x03910438` on WH3 9.0.2 | sibling/internal constructor; use as the sole/top-level Move VTable remains **RETRACTED** | not valid for BSC top-level Move outcome |
| Attack VTable `0x03912988` on WH3 9.0.2 | statically re-derived from Attack constructor | command identity |
| allocator `0x02F53128` on WH3 9.0.2 | top-level Move/Attack call target; allocator ABI contract inherited pending runtime smoke | core outcome capture |
| Order slot `root+0x288`, stride `0x120` | statically verified | core |
| engine sequence `slot+0x20` | statically verified | SC6 core |
| MOVE payload `+0x58/+0x5C/+0x60` | statically verified | core |
| ATTACK target/flags | statically verified | core |
| `root+0x114/+0x118` member count/array-like fields | evidence exists, semantic naming is not promoted | research only |
| Name `Entity` for array members | **UNVERIFIED semantic label** | prohibited as release prerequisite |
| `Entity +0x18 = MovementComponent*` | **RETRACTED**; the cited proof was actually ResultRecord+0x18 Controller | prohibited |
| Component `+0x4A0` backref to that Entity | not closed from the member-array path; RC7 found zero pair candidates | quarantined |
| Component `+0x8B0` movement state for those members | not closed as part of a valid Entity→Component chain | quarantined |
| `vt+0x630 = Entity::is_alive()` | partial virtual-call evidence only; class/slot semantics not runtime-proven | quarantined |
| ContactPair site `0x030A4505` on WH3 9.0.2 | exact guard relocated; semantics remain research-only | optional, staged disabled |
| Smart Guard state transition `0x030E319C` on WH3 9.0.2 | exact guard relocated | optional, staged disabled |
| RC7 `platform_stop_observer()` | implementation present; RC7 runtime logged successful hook disable | retained; RC8 production desktop-quit runtime test pending |

## Promotion rule

A physical assumption can return to production only after all three are true:

1. provenance from a known engine object path is demonstrated without circular fixtures;
2. runtime evidence on the current build proves semantics across more than one unit/state;
3. disabling the physical provider has a documented behavior gap that cannot be covered by the command/FEG architecture.

## Transition Policy D1 assumption note

`BSC-TPOL-D1` adds **no new reverse-engineered prerequisite**. Its inputs are the existing canonical action/block state, supported battle-unit geometry/target APIs, current route-debt semantics, and already-authoritative V3 execution identity. MCT policy must not promote any quarantined physical evidence or weaken Native provenance requirements.
