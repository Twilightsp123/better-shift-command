# Native Address Maintenance Pipeline

This document defines the maintenance path used when a Total War: WARHAMMER III update changes the executable and invalidates the BSC Native Bridge map.

The runtime policy remains **static and fail-closed**. Relocation tools may discover a candidate map, but the shipped bridge never dynamically scans the game at startup.

## Source of truth

- `native_maps/CURRENT` selects the promoted map for the current branch.
- The selected JSON file is the only maintained source for EXE SHA, 16 mandatory guards/RVAs, two optional sites, and Move/Attack VTables.
- `maintenance_tools/generate_native_header.py` renders `src/native_bridge/include/wh3/generated_native_map.hpp`.
- C++ runtime source consumes that generated header; it must not duplicate an address table.
- `check_native_map_contract.py`, `prebuild_contract_check.py`, and CorePath checks fail if JSON/header/runtime wiring diverge.

## Update stages

1. **Canonical map** — start from the last proven map.
2. **Exact relocation** — scan executable PE sections for each exact old guard.
3. **Classification** — distinguish same build, hash-only, RVA-only, ambiguous, or codegen/semantic drift.
4. **Normalized relocation** — mask only explicitly declared relocation-dependent operands such as rel32 or RIP-relative displacement bytes.
5. **.pdata fingerprint** — identify the containing Windows x64 runtime-function boundary and record function-size/hash/call evidence.
6. **Relationship resolution** — use preserved relationships such as Move/Attack cluster distance, Lua Move/Attack pairing, handler pairing, shared global targets, and direct call edges. Re-derive allocator → constructor → VTable identity for Move/Attack.
7. **Ghidra/BinDiff fallback** — only if Stage 6 leaves a mandatory site unresolved. Export a small evidence bundle; never include the game EXE.

## One-command triage

Run on the machine that owns the game installation:

```text
python maintenance_tools/wh3_update.py --exe "<path>\Warhammer3.exe" --game-version "<version>"
```

The command writes a report under `reports/wh3_updates/<sha-prefix>/` containing exact, normalized and relationship results plus a candidate map when all mandatory sites resolve.

## Promotion gates

A candidate map may be promoted to a build-candidate branch only when:

- target EXE SHA is recorded;
- mandatory guards resolve 16/16;
- optional sites are reported independently and never gate CorePath;
- Move/Attack allocator→constructor→VTable dataflow is re-derived on the new EXE;
- the generated header is byte-for-byte synchronized with JSON.

A build candidate is **not release-authorized** until all of these also pass:

1. static source/documentation contracts;
2. Windows VS2019/v142 + MASM build;
3. Windows Native CTest;
4. target-EXE inspect 16/16;
5. WH3 native smoke: Bridge load, normal Move/Attack capture, BSC-owned Move/Attack issue, queued sequence, execution identity, external-player attribution, and Quit-to-Windows safe-stop.

## WH3 9.0.2 first real relocation

9.0.2 SHA:

`fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785`

The pipeline resolved all 16 mandatory sites and both optional sites. It also re-derived:

- allocator: `0x02F53128`
- full Move constructor: `0x0300BDC0`
- Attack constructor: `0x0300B8C4`
- common base constructor: `0x0300B518`
- full Move VTable: `0x03913618`
- Attack VTable: `0x03912988`
- sibling Simple/Intercept Move constructor: `0x0300BD64`
- sibling VTable: `0x03910438`

This is static relocation evidence only until Windows and WH3 runtime gates pass.
