# T2-MOVE-G — Native adoption turnback-route safety (OFFLINE CANDIDATE ONLY)

Date: 2026-10-09.
Frozen parent F: `206221bcdf5b16db92ea70124aa9c8be4149e557`.
Isolated development branch: `maintenance/t2move-g-adversarial`.
Draft PR: https://github.com/Twilightsp123/better-shift-command/pull/2

## Goal and non-goals

Retain the player's canonical Shift route and avoid falsely completing a MOVE waypoint
when Native has already promoted an exact immediate successor on a backward/hairpin path.
Do not change Native Bridge, RVA/VTables/ABI, gameplay CFG scalars, formal release pack,
T2-B G1.1 Move→Attack, T1.6 transaction authority or existing SC1–SC4 proactive dispatch.

**Important scope distinction:** Existing SC1 includes a tested policy to proactively start
U-turn movement well before the waypoint, even though a sharp turn may reduce route fidelity.
The T2-B contract freezes `route_handoff_ready()` byte-for-byte. This stage therefore
**does not fix or authorize** proactive U-turn semantics. It hardens only the separately
proven dangerous E/F Native `i+1 MOVE` adoption / completion-credit path.

## Reproduced counterexamples on unmodified F

GitHub Actions [37822137891](https://github.com/Twilightsp123/better-shift-command/actions/runs/37822137891)
ran seven adversarial real-controller fixtures before code changes:

- G-RT01 **FAIL**: 180° reversal from waypoint (100,0) toward (0,0) was
  Native-adopted while the controller was still 30m from the waypoint.
  `STEERING_CORNER` completed it even though the path deviation was 30m and
  the frozen corridor tolerance was only 5m.
- G-RT02 **FAIL**: 135° backward successor (30,70) likewise gained early steering credit.
- G-RT04 **FAIL**: dense short leg / reversal prematurely promoted while prior
  route obligation remained unresolved.
- G-RT00 / 03 / 05 / 06 **PASS**: collinear three-node route, safe 90° lateral
  turn, two simultaneously unpaid SC3 debts, and per-unit Native revision isolation.

These failures are in the synthetic real-controller fixture, not in WH3 process testing.

## Architectural correction after the initial rejected approach

The initial experimental change blocked backward steering inside
`route_handoff_ready()`. It turned all seven new tests green but **failed** the original
SC1 U-turn fixture and the frozen T2-B Move→Move static contract.
That approach was **reverted**. The legacy early steering policy is unchanged.

The retained G change operates after E's exact V3 + revision + D debt
revalidation and before A/B permission is consumed:

1. While Native still executes the exact current MOVE, D's observer freezes the
   successor's backward projection on the *inbound* current-leg axis, together with
   the existing current MOVE reach tolerance. Both are scalar facts computed in the
   pre-promotion frame; they cannot be recomputed from post-successor motion.
2. If cached route mode is `STEERING_CORNER`, the E Native adoption preview denies
   when both (a) the successor endpoint projects back past the current waypoint
   by more than the frozen reach tolerance, and (b) remaining distance to the owed
   waypoint also exceeds that same frozen tolerance.
3. `PATH_SAFE` remains governed by its original chord/cut-error check.
   Normal 90° steering, multiple SC3 debts, native identity and T1.6 commit remain unchanged.
4. The result is **denial of Native adoption credit**, not forced completion or a
   new reassert loop. Existing bounded SC6 rollback rules remain authoritative.

No new meter, fraction, speed or angular gameplay constant was introduced.

## Verified offline CI

[Actions 37822771962](https://github.com/Twilightsp123/better-shift-command/actions/runs/37822771962)
**SUCCESS** with G controller 7/7 PASS; three G behavioral mutants CAUGHT,
including removal of the frozen turnback guard, bypass of PATH_SAFE chord geometry,
and deletion of registered waypoint debt. E controller 11/11 and 8/8 E mutants
CAUGHT; F controller 5/5 and 3/3 F mutants CAUGHT. A/B/C/D suites, original
full 46-job maintenance checks and documentation contract all passed.

## Remaining risks and promotion gates

- **Not resolved:** SC1 proactive U-turn may still cut a route because legacy tests
  expressly require very early U-turn steering. Redesigning that is a separate
  permission/route-credit architecture decision, not an invisible G regression fix.
- **Not proven:** live WH3 engine movement after a denied Native successor,
  hairpin compression, stepwise movement and collision avoidance.
- **Not proven:** large-scale multi-unit fairness beyond the two-unit controller fixture.
- **Deferred:** WH3 RT-TP-02/03 (T2-B), RT-TP-04/05 (T2-MOVE).

The G branch and any source archive remain **offline-only**, not a Steam pack,
not WH3-promoted, and must not merge into frozen F, E or T2-B merely because CI passed.
