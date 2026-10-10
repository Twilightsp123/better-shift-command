# N1 — Exact WH3 9.0.3 member-distance selection: a negative root-cause check

**2026-10-10 | Research only, no Native gameplay patch.** Exact user EXE SHA256: `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`; PE image base `0x140000000`. The user's reported defect remains asynchronous soldier-model waypoint turning and crowding *within a unit card*, not vanilla full-stop. Historic Lua MOVE→ATTACK pausing is a separate BSC regression.

## Verified native per-member operation

- Function **0x031E11AC** reads a context's **+0x114 count / +0x118 pointer array** and loops over its members. This is an actual structured iteration, unlike coincidental raw displacement-byte matches.
- For member+0x20, it calls **0x03113AE4** at **0x031E12C6**, and repeats for the previously selected member at **0x031E12D6**.
- **0x03113AE4** handles coordinate-frame differences via native **0x0311D0CC**, then returns **squared 2D distance** calculated by two `mulss` and `addss` operations at **0x03113B54–0x03113B5C**.
- **0x031E12DB–0x031E12EA** uses `comiss` (previous candidate versus new), `seta`, and `cmove`: on ordinary ordered finite squared distances it retains the **nearest** member, retaining the earlier member on a tie.
- It calls relationship lookups **0x031F6638** and **0x031F6D18**, which use other **+0x124/+0x128** member containers, and a conditional follow-on **0x031DF6A0**.

**Conclusion:** native code can choose a member by proximity and query its relationships. This is **not** proof that each soldier owns a Shift command or that this selector controls waypoint switching. The class of the members and their exact connection to Shift MOVE remain unproved.

## Negative control: no direct E8 caller to the selector

Read-only scanning of both executable PE sections for candidate `E8 rel32` calls targeting **0x031E11AC** found **zero raw direct-call candidates**. This does **NOT** eliminate indirect virtual dispatch or function-pointer calls. But an original queued MOVE → selector call path has **not** been verified and therefore no modification of this selector can be justified.

A broader raw displacement scan across native functions also produced many **false positives**: in several candidate functions `+0x114/+0x118` are floating-point vector fields rather than count/pointer-array fields. Every candidate must be validated at the decoded instruction and object-provenance level.

## Next required *causal*, not merely geometric, proof

1. Identify the actual native **per-soldier destination and facing writer** and type of member object; distinguish unit-wide target allocation from independent soldier arrival/turn rules.
2. Trace which changes at a chained Shift corner first: unit's formation target/heading, model-specific assigned destination, model-local path/steering, or avoidance. Show whether mixed directions occur from *different commands* versus the same native command applied at different physical phases.
3. Connect that first divergent decision to the crowding geometry with native callgraph/dataflow and compare normal right-click behavior.
4. If no local original group/formation transition predicate can fix it without rewriting navigation/collision, record a minimal Native patch **NO-GO** instead of resuming the Lua scheduler.

## Exact-file reproducibility

The complete separately provided **BSC_N1_903_MEMBER_DISTANCE_ACTUAL_AUDIT.zip** contains: pinned SHA and read-only PE verifier, 19 instruction guards, five E8 call guards, bounded direct-call scanner, `test_audit.py` (**10/10 synthetic cases PASS**), JSON evidence, this report and SHA256 manifest. No Warhammer3.exe redistributed. `runtime_patch_authorized=false` in the evidence.

**STATIC/OFFLINE only** — no verified native soldier arrival/turn Hook, no Windows or WH3 test, DLL, PACK or release.
