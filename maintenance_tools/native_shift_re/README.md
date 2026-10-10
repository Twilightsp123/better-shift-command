# WH3 9.0.3 — Native Shift RE offline tooling

**Research-only. No executable patch and no proven 9.0.3 queue writer.**

## Scripts

- **scout_pe.py** (Python 3.8+, standard library). Read-only AMD64 PE header, SHA256 and executable-section scanner. Uses historical 9.0.2 byte guards exclusively as discovery leads, including relocation masks. Even an exact byte match is NOT a verified RVA/ABI/Hook.
- **ghidra_order_xrefs.py** (Ghidra Jython). Searches decoded executable instructions for operands matching the *historical* 9.0.2 offsets +0x2F88/+0x2F8C. Includes opcode bytes, function context and read/write hints; neither current Unit-root provenance nor actual field-access semantics are established.
- **../../tests/test_native_shift_re.py** contains synthetic fixture tests (not game physics or WH3 proof).

## Read-only PE fingerprint and byte-similarity scan

From the repository root, with the installed original 9.0.3 EXE:

    python maintenance_tools/native_shift_re/scout_pe.py --exe "C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\Warhammer3.exe" --report "N1_outputs\pe_scout.json"

The first pass records SHA256 but reports UNVERIFIED_BUILD_SHA_DISCOVERY_ONLY, because a matching digest for 9.0.3 is not pre-established. Independently confirm the EXE build before asserting its game version. Optional pinned rerun:

    python maintenance_tools/native_shift_re/scout_pe.py --exe "C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\Warhammer3.exe" --expected-sha256 "<recorded verified 9.0.3 SHA256>" --report "N1_outputs\pe_scout_pinned.json"

SHA_VERIFIED_BINARY_RESEARCH_ONLY means **hash matched user-supplied expectation**, not that byte pattern implies a valid engine hook. EXE and legacy JSON are never written. Invalid input returns code 2; explicit old-build rejection/expected SHA mismatch returns code 3.

## Ghidra decoded instruction candidate search

1. Import and fully analyze the *same* SHA-verified 9.0.3 executable in Ghidra; retain the original EXE on disk.
2. Add maintenance_tools/native_shift_re to the script search path.
3. Run ghidra_order_xrefs.py with script arguments:

    --exe=C:/WH3/Warhammer3.exe
    --expected-sha256=<same exact hash>
    --output=C:/WH3/N1_outputs/ghidra_order_xrefs.json

The script confirms the EXE SHA256, compares its MD5 to the Ghidra imported-program MD5, and refuses to overwrite the EXE. Ghidra was NOT run in the development container: treat the script as a tested Python syntax/contract draft awaiting Ghidra runtime compatibility and 9.0.3 binary verification.

**Output limitations:** the Ghidra script detects operands with scalar values matching historical fields. It cannot discover optimized aliases/changed offsets reliably; an operand read/write hint is not proof the memory belongs to a WH3 order queue. It never promotes a site or authorizes patching.

## Native proof steps after candidate export

Find an actual engine root provenance, confirm original head/count **writers**, and follow control/dataflow to MOVE completion, old order retirement and next activation. In parallel, trace original per-frame MOVE braking and motion state. Separately identify original ATTACK activation/target lifetime. Maintain exact SHA, instruction bytes, RVA, ABI, xrefs, alternatives and negative normal-RMB controls.

## Exact user-provided 9.0.3-labelled EXE state-origin proof

`verify_903_move_state_origin.py` is a **read-only, exact-SHA evidence verifier**, *not* an address relocator. It matches 25 selected machine-instruction guards and two original float constants and records that no patch is authorized. It rejects other EXE hashes, including other builds of WH3.

    python maintenance_tools/native_shift_re/verify_903_move_state_origin.py --exe "C:\\path\\to\\Warhammer3.exe" --report "N1_outputs\\state_origin_evidence.json"

Original result for SHA `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`: **25/25 instruction guards match**, 8/8 isolated byte/metadata tests passed against original EXE; six additional synthetic CI tests were added without the EXE. No gameplay, Ghidra, or Win64 loader behavior is verified.

See [native state origin report](../../docs/current/N1_903_MOVE_STATE_ORIGIN.md).

## Offline synthetic test

    python -m unittest discover -s tests -p "test_native_shift_re.py" -v

Initial isolated Python result: **9/9 PASS** on synthetic PE files. This is NOT Ghidra integration success, Windows runtime testing or WH3 acceptance.

No DLL, PACK, native injection, executable modification, shadow queue, Lua controller or Steam release results from these tools.

See docs/current/WH3_9_0_3_NATIVE_PATCH_DESIGN.md for the current N1–N6 plan.

## N1 route-gate evidence (9.0.3-labelled exact SHA)

`verify_903_route_gate.py` checks 46 frozen machine-instruction byte guards and 6 verified E8 call edges on the exact user-supplied EXE SHA only; always emits `runtime_patch_authorized: false`. The derived `state+0x24` truth table is **specific to the traced callback**, not a general WH3 mode or movement-speed rule. Run with:

    python maintenance_tools/native_shift_re/verify_903_route_gate.py --exe "C:\\path\\Warhammer3.exe" --out "N1_outputs\\route_gate.json"

Six synthetic CI cases reside in `tests/test_native_shift_re_route_gate.py`. The complete separately supplied local proof archive additionally contains bounded LLVM disassembly, byte evidence, tests and SHA manifest without the EXE. Actual WH3 physics/braking and Windows Hook compatibility have not been tested.

## N1 formation member/group coordinate entry (user-reported real defect)

The read-only `audit_903_formation_entry.py` accepts `--exe` and `--report` and refuses all EXE SHA mismatch. It compares **23 pinned exact instruction guards** and **6 decoded direct-call targets** for UnitRoot member-position aggregation and group coordinate updating before native order processing. This is NOT a proven soldier-array mapping, arrival condition or Hook location. Synthetic regression tests: `tests/test_native_shift_re_formation.py` (8 cases).

    python maintenance_tools/native_shift_re/audit_903_formation_entry.py --exe "C:\\path\\to\\Warhammer3.exe" --report "N1_outputs\\formation_entry.json"

See [N1 formation entry report](../../docs/current/N1_903_FORMATION_ENTRY_CALLGRAPH.md). The user-visible issue is within-unit soldier model desynchronization and crowding, **not a proven vanilla Move stop**.

## Distinct member layers (2026-10-10)

`audit_903_member_layers.py` verifies 23 exact user-EXE instruction byte guards and four E8 call targets. It preserves an important **negative inference**: two independent UnitRoot count/pointer vectors and one deeper child collection do **not** automatically identify individual soldier movement objects. It neither writes the EXE nor authorizes runtime changes.

    python maintenance_tools/native_shift_re/audit_903_member_layers.py --exe "C:\\path\\Warhammer3.exe" --report "N1_outputs\\member_layers.json"

See [N1 member layer report](../../docs/current/N1_903_MEMBER_LAYER_TYPE_GAP.md). Synthetic checks: tests/test_native_shift_re_member_layers.py. A separately provided full offline package also contains bounded LLVM instructions, 8 independent local tests and SHA manifest; no executable copy.

## Native MOVE → unit route proof (exact 9.0.3 user binary)

Run `audit_903_move_unit_route.py --exe PATH --report OUTPUT` to check the 23 exact byte guards and seven original E8 target calls linking both MOVE worker branches to `0x0301287C` and native route descriptor storage at root `+0x270`. Research only, not a Hook map. See [N1 report](../../docs/current/N1_903_MOVE_TO_UNIT_ROUTE_DIRECT.md).

Run `audit_903_member_route_virtual.py --exe PATH --report OUTPUT` to verify nine original bytes and two E8 targets near native unit-route/member virtual `+0xC8` dispatch. The vtable implementation and soldier identity are **not** proven. Old unrelated nearest-member selector `0x031E11AC` has no direct E8 caller identified; no patch proposed.

## N1 proven original MOVE fanout to group members

Read [N1_903_NATIVE_MOVE_MEMBER_FANOUT.md](../../docs/current/N1_903_NATIVE_MOVE_MEMBER_FANOUT.md). SHA-gated `audit_903_move_member_fanout.py` verifies **38 exact original machine instruction guards and nine E8 call destinations**: original MOVE issuer calls route update, constructs a unit-root-derived native group, creates group-specific 0x30-stride target records, and calls each member object's virtual +0x368 with a separately constructed native payload. The concrete VTable receiver/motor-completion logic is not yet identified. Synthetic CI gates: `tests/test_native_shift_re_move_member_fanout.py`.

    python maintenance_tools/native_shift_re/audit_903_move_member_fanout.py --exe "C:\\path\\Warhammer3.exe" --report "N1_outputs\\move_member_fanout.json"

This tool does not write to the executable, install hooks, or prove actual game animation/arrival behavior.

## N1 original member virtual receivers solved (9.0.3 labelled EXE)

`audit_903_member_virtual_receivers.py` verifies original SHA and **16 machine instruction byte guards**, scans native VTable slots +0x3F8 and +0x368, then independently confirms constructor RIP-relative LEA references. Exact-binary result: **38 VTables, 36 common member handler `0x0306B9F0`, 1 delegator `0x0306B9CC`, 1 special `0x03117CE0`**; group getter `0x008F37B0` reads `member+0x300`. Downstream member methods `+0xE8/+0x100` connect to native coordinate/heading writes and local route cache. No proven waypoint completion or runtime Hook. Synthetic CI tests: `tests/test_native_shift_re_member_virtual_receivers.py`. Full EXE-backed 7-case test bundle delivered separately.

    python maintenance_tools/native_shift_re/audit_903_member_virtual_receivers.py --exe "C:\\path\\Warhammer3.exe" --out "N1_outputs\\member_vtables.json"

See [research report](../../docs/current/N1_903_MEMBER_VIRTUAL_RECEIVER_RESOLVED.md).

## Exact 9.0.3 layout-count vs waypoint-arrival negative proof

`audit_903_layout_vs_arrival.py` statically verifies 26 code guards, eight constructor-backed strategy vtables (+0x20/+0x48), and distinct original group object virtual +0x20 (native RVA 0x030E0AA8). The strategy+0x20 values are formation layout cardinalities (sqrt(n), min(13,n), member-count lookup, etc.), not a demonstrated Shift waypoint arrival flag. Task+0xB8 caches these computed integers. The member receiver chooses +0x100/+0xE8 actions by member+0x104; no proven original leg-phase controller or Hook site. Offline tests `tests/test_native_shift_re_layout_vs_arrival.py` (8 cases).

    python maintenance_tools/native_shift_re/audit_903_layout_vs_arrival.py --exe "C:\\path\\Warhammer3.exe" --out "N1_outputs\\layout_vs_arrival.json"

See [finding](../../docs/current/N1_903_LAYOUT_COUNT_NOT_ARRIVAL_DISCONFIRMATION.md). No EXE writes.
