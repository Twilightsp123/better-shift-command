# N1: actual MOVE task has conditional direct path into member target fanout

**2026-10-10. Original EXE exact SHA256**
\`518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a\`.
Research-only static reachability; original V3 reported this fanout Hook zero-hit.
**Do not mistake static reachability for confirmation the V3 branch executed.**

## New original-binary proof

1. PE64 Exception Directory \`RVA 0x0F059000\`, size \`0x00264D50\`,
   has 209,180 \`RUNTIME_FUNCTION\` boundaries.
2. V3-confirmed native MOVE \`0x03025D70\` calls task constructor
   \`0x02F2C734\` at \`0x030260AF\`. Task VTable \`0x03ABBE18 +0x10\`
   is \`0x02F561E8\`.
3. **Gated**, not unconditional: with original shared state \`+0x20==4\`,
   \`+0x24!=0\` and task flag \`+0x74\`, original \`0x02F561E8\`
   calls \`0x03279E40\` at \`0x02F56404\`.
4. \`0x03279E40\` checks a context-mode helper \`0x02DC2E04\`,
   whose exact bit mask \`0x29\` allows values **0, 3, 5**
   in the checked 0..5 range. This is **not member+0x104**.
   The accepted branch calls \`0x030D554C\` at \`0x03279EB3\`.
5. \`0x030D554C\` -> \`0x030D5490\` at \`0x030D5603\`.
   Original \`0x030D5490\` invokes strategy \`+0x48\` for 48-byte
   per-member target records; takes \`member[i]\` with \`record[i]\`;
   copies data through \`0x02F5F868\` at \`0x030D54FC\`;
   calls member VTable \`+0x368\` at \`0x030D550F\`, with native
   group postprocessing only afterwards at \`0x030D5522\`.
6. Exact EXE 36 member VTables have \`+0x368 = 0x0306B9F0\`.
   The original VTable \`+0xE8\` census is:
   \`0x03073224: 28\`, \`0x02DCD63C: 3\`,
   \`0x02F4F910: 4\`, \`0x0311C92C: 1\`.
   \`0x03073224\` directly calls \`0x0315EC98\` at \`0x0307328B\`;
   latter contains original conditional member XYZ/facing writers and
   other movement/geometry branches. It is not a proven final solver.
7. Separately, \`0x0306EDA0\` at \`0x0306EDD4\` installs
   \`member+0x2E0\` controller, consumed by \`0x03060700\` and
   \`0x0315C1E4\`. The task-generated target -> local controller
   producer edge is STILL open.

## Explicit negative conclusion

\`0x030D5628\` query uses \`seta\` after comparing
\`stamp + 2*nativeStep\` against current tick: a **recent timestamp**
window rather than generic wait-for-all-models completion.
Its inspected caller \`0x03024C02\` checks unit queue count zero before
the query. Native group average-distance calculation
\`0x030D572C\` is real but **not shown to gate queued Shift**.
Do NOT patch group threshold, OrderHead, member action modes,
local spline indices or animation random delays.

V3 member actor mode \`member+0x104==0\` is not proof the separate
group formation strategy selector \`[[UnitRoot+0x3D48]+0x248]\`
had Mode 0.

## Finite repair boundary

The strongest *conditional* target-slot repair site is the original
\`0x030D5490\` \`member[i]/record[i]\` binding **before**
\`0x02F5F868\` copies payloads. Only authorize it if the actual
Shift branch/strategy and crossing assignment can be confirmed;
otherwise abandon slot remapping and trace the original
\`member+0x2E0\` controller target/avoidance producer.
Preserve CA progressive route, original command ownership and native
physics. No current reason to restore Lua scheduler.

## New code and grades

- \`maintenance_tools/native_shift_re/audit_903_real_move_conditional_fanout.py\`:
  exact SHA, PE exception boundaries, 12 E8 anchors, eight byte guards,
  two VTables and 36 original member receiver tables. Fails closed.
- \`tests/test_native_shift_re_real_move_conditional_fanout.py\`:
  synthetic PE and negative guard CI tests.
- Current conversation full EXE audit: 16 original E8 calls,
  10 exact opcode guards, 209,180 runtime function boundaries,
  36 member tables, 12/12 offline tests including original EXE.
  Full machine excerpts/JSON/verification archive delivered separately.
- Windows native DLL: **NOT BUILT**. WH3 gameplay fix: **NOT RUN**.
- Single causal blocker: no proven **V3-taken original
  member-target or local steering decision** accounting for crossing
  during the progressive Shift turn. Static conditional graph alone
  does not authorize patching.
