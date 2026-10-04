# WH3 Native Address Maintenance Pipeline

This pipeline minimizes manual reverse engineering after a Total War: WARHAMMER III update while keeping the runtime bridge static and fail-closed.

## Stages

1. Canonical JSON map in `native_maps/`.
2. Exact guard relocation.
3. Build/update classification.
4. Relocation-normalized x64 guard matching.
5. Windows x64 `.pdata` runtime-function fingerprints.
6. Declarative RVA/callgraph/relationship resolution plus constructor/VTable re-derivation.
7. Ghidra/BinDiff fallback only for mandatory sites still unresolved after Stage 6.

Run the normal path with:

```
python maintenance_tools/wh3_update.py --exe <Warhammer3.exe> --game-version <version>
```

If Stage 6 resolves all mandatory sites, the pipeline emits a candidate map and immediately performs static candidate verification against the same EXE.

## Proof levels

- `L1_BYTE_MATCH`: exact unique guard.
- `L2_NORMALIZED_MATCH`: unique match after masking relocation-dependent bytes.
- `L3_STRUCTURAL_MATCH`: an ambiguous byte match was reduced to one candidate by declared relationships/callgraph evidence.
- `L4_DATAFLOW_DERIVED`: order constructor/VTable identity was re-derived from current executable dataflow.
- `L5_RUNTIME_VERIFIED`: reserved for the later WH3 runtime smoke gate.

A candidate map is never release-authorized automatically.

## Promotion

`native_maps/CURRENT` points only to the promoted runtime map. Do not point it at a new candidate until all required gates pass:

- candidate static verification;
- generated-header/prebuild contract;
- Windows v142/MASM build;
- Windows Native CTest;
- WH3 native smoke, including Move, Attack, queued Shift execution identity, external/player identity, and safe stop.

Optional ContactPair and Smart Guard sites remain non-gating unless a separate architecture decision explicitly promotes them.

## Stage 7

When Stage 6 cannot uniquely resolve every mandatory core site:

```
python maintenance_tools/export_re_bundle.py --exe <Warhammer3.exe> --map <current-map> --out relocation_evidence.zip
```

The evidence bundle excludes the EXE. The included Ghidra post-script labels candidate RVAs for manual semantic review.

## Candidate build lane

A newly resolved map must not be promoted just to compile it. Prepare an isolated
build overlay instead:

```
python maintenance_tools/prepare_candidate_build.py \
  --exe <Warhammer3.exe> \
  --map native_maps/candidates/<candidate>.json \
  --out build/<candidate>
```

The command verifies the candidate against the EXE, renders
`build/<candidate>/include/wh3/generated_native_map.hpp`, records a manifest,
and writes `build_windows_v142.ps1`. CMake consumes that header only when
`WH3_NATIVE_MAP_INCLUDE_DIR` is supplied. The checked-in promoted header and
`native_maps/CURRENT` remain untouched.

The Native Bridge build ID comes from `native_map::kMapId`; therefore a
candidate DLL identifies the actual map it was built against even while the
bridge ABI version remains unchanged.
