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

## Offline synthetic test

    python -m unittest discover -s tests -p "test_native_shift_re.py" -v

Initial isolated Python result: **9/9 PASS** on synthetic PE files. This is NOT Ghidra integration success, Windows runtime testing or WH3 acceptance.

No DLL, PACK, native injection, executable modification, shadow queue, Lua controller or Steam release results from these tools.

See docs/current/WH3_9_0_3_NATIVE_PATCH_DESIGN.md for the current N1–N6 plan.
