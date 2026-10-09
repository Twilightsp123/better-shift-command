# READ THIS FIRST — Better Shift Command v1.3.0

**Formal project version:** `v1.3.0`  
**Canonical Steam pack filename:** `zzz_better_shift_command_steam.pack`

This repository/archive is the long-term maintenance source for Better Shift Command. Internal labels such as `COREPATH-RC8`, `BSC-TPOL-D1`, `T1H`, and `movevtfix` are maintenance-history / architecture labels only. They are **not** the public Mod version.

## Important packaging rule

This archive does **not** generate or replace your already-renamed Steam pack. The canonical published/install filename is:

`zzz_better_shift_command_steam.pack`

The older installable T1H pack that existed before formal version normalization is preserved under:

`archive/pre_v130_installable_pack/`

It is historical/reference material and must not be mistaken for the formal v1.3.0 release artifact.

## Current runtime identity

- Mod/controller version: **v1.3.0**
- Upstream behavior ancestry: v1.2.2 + SC1–SC6 maintenance line
- Native Bridge compatibility/build ID: `1.0.17-corepath-wh3-6c104-movevtfix`
- Target WH3 SHA256: `6c104a63aacc4d865f78e6d198185f830a43255ae18367ad6be906f5f3433297`
- Mandatory Native hooks: 16
- Physical evidence: **QUARANTINED**
- MCT UI: **not exposed yet**
- Hidden policy/profile interface: present
- Minimum Engagement Time default: **3.0 s**

The Native Bridge string is an internal compatibility/build identifier, not the Mod version.

Validated structural substages: `BSC-TPOL-T1H` → `BSC-TPOL-T1` → `BSC-TPOL-T1.5` → `BSC-TPOL-T1.6` → `BSC-TPOL-T1.7` → behavior-neutral `ARRIVAL_BRAKE_G1`. The current construction branch additionally carries `BSC-TPOL-T2B-G11` (G1.1 + dual issue/adopt envelopes), which is **offline validated but still awaits WH3 runtime RT-TP-02/03**. T2-MOVE remains pending.

## Mandatory maintainer reading order

1. `README_FIRST.md`
2. `README.md`
3. `docs/MAINTAINER_INDEX.md`
4. `docs/VERSION_POLICY.md`
5. `docs/ARCHITECTURE_STATUS_20260929.md`
6. `docs/OPEN_ISSUES.md`
7. `docs/MAINTENANCE_TODO.md`
8. `docs/ASSUMPTION_LEDGER.md`
9. `docs/TEST_MATRIX.md`
10. `docs/CURRENT_BUILD_MAP.md`
11. `docs/DECISION_LOG.md`
12. `docs/VERSION_LINEAGE.md`
13. `docs/PROVENANCE.md`
14. `docs/HISTORY_COVERAGE.md`
15. `docs/design/HIDDEN_MCT_INTERFACE_T1H.md`
16. `docs/design/MCT_POLICY_SCHEMA_D1.md`
17. `docs/design/BSC_TRANSITION_POLICY_ARCHITECTURE_D1.md`
18. `docs/DEVELOPMENT_HISTORY.md` only for historical context

## Current architecture status

The frozen structural/permission baseline remains **BSC-TPOL-T1.7** over SC1–SC6, with behavior-neutral **ARRIVAL_BRAKE_G1** validated separately. The current construction branch intentionally advances ordinary Move→Attack to **BSC-TPOL-T2B-G11**: G1.1 distinguishes generic slowing from waypoint-coherent arrival braking, `TransitionPolicy` emits distinct Attack issue/adopt envelopes, and SC6 may consume a one-poll pre-promotion decision cache for an exact immediate Native Attack. T1H/T1/T1.5/T1.6/T1.7 still own the profile scaffold, shared evaluation, execution lineage, transactional edge commit and consumer-neutral envelope structure.

**T1.7 itself remains the frozen permission-neutral baseline**, but the current T2-B construction branch intentionally widens **ordinary Move→Attack only**. Proactive Attack issue never uses the one-poll synchronization margin; that margin may widen only the Native **adopt** envelope. `ATTACK_TERMINAL_HANDOFF` credit is granted only by the T1.6 shared commit path after verified ACK or exact Native observation. Immediate future MOVE adoption remains closed on the T2-B branch and all production/release candidates. **Exception: isolated `maintenance/t2move-e-integration` intentionally enables experimental exact `i+1 MOVE` adoption for offline tests only; it is not WH3-promoted or released.** The follow-on `maintenance/t2move-f-audit-hardening` branch additionally closes V3-only and live-Native-revision proof gaps and verifies dynamic SC3 debt invalidation offline; it is also NOT WH3-promoted or released. Isolated G (`maintenance/t2move-g-adversarial`) further denies unsafe 135°/180° turnback **Native MOVE adoption credit** using frozen geometry; legacy proactive SC1 U-turn semantics remain unchanged and unverified in WH3. The follow-on H1 branch adds **read-only** RouteObligation diagnostics (SATISFIED / DEBT_PRESERVED / BLOCKED) to expose the difference between early steering and verified waypoint completion; it changes no issue/adopt/commit permission and is not WH3-promoted. Isolated H2-B/C/D + H3 converts that observation into explicit ACK/route-credit separation and a conservative issue/adopt route-fidelity veto; it is offline-validated only and intentionally supersedes premature SC1 90°/U-turn tests within that branch, NOT within the frozen production or T2-B branches. GitHub Actions offline validation for the current candidate is **46/46 PASS**; core mutations are **44/44 CAUGHT**, T1.5/T1.6/T1.7 stage mutations remain **7/7 CAUGHT** each, and the dedicated G1.1/T2-B/cache mutation set is **13/13 CAUGHT**.

The 2026-10-05 direct T2-B, T2-A, hairpin and native-passthrough builds are preserved as historical experiments/evidence only. They do not override the staged D1 migration or current runtime source.

The current actionable queue is maintained in `docs/MAINTENANCE_TODO.md`.

The next transition work is therefore:

- WH3 **RT-TP-02 / RT-TP-03** is currently **BLOCKED / DEFERRED because runtime testing is not available**; when testing becomes available, run it against the already-prepared T2-B G1.1 candidate and promote only if there is no stop-before-Attack and no waypoint-cut regression;
- keep T2-MOVE immediate-successor MOVE reconciliation **with hysteresis from the first promotion**, using observed one-poll travel as the synchronization band rather than another hand-tuned meter value;
- wire visible MCT only after the Smooth default passes runtime;
- lifecycle/teardown remains a separate stream.

Battle teardown/hang remains a separate lifecycle stream and must not be mixed into transition-policy changes.


**9.0.2 H2/H3 experimental runtime handoff (2026-10-09):** The Windows Native 1.0.18 build now targets EXE SHA256 `fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785` with the preexisting 16-hook/VTable 9.0.2 address candidate. The original H2/H3 test pack was incorrectly built against the 9.0.1 DLL and failed at `OBSERVER_HOST_EXE_SHA256_MISMATCH`. The isolated `maintenance/t2move-h2h3-wh3-902-integration` branch builds a fresh WinX64 v142 DLL and seals plain/DEBUG candidate PACKs only after Windows Native CTest; it is **NOT WH3 runtime validated, NOT merged, NOT released**. See `docs/design/T2MOVE_H2H3_WH3_902_INTEGRATION_20261009.md`.
