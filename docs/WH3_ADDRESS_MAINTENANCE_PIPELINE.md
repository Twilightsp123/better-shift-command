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

## Candidate pointer and CI

`native_maps/CANDIDATE` selects the staged map for Windows candidate CI. It is
independent from `native_maps/CURRENT`; changing the candidate pointer never
promotes a runtime map. The Windows workflow generates a build-local header from
that candidate, builds with VS2022 + v142, runs Native CTest, and uploads the
candidate DLL only if the gate passes.

The workflow also emits an early full-source snapshot after forcing
`core.autocrlf=false` and `git reset --hard HEAD`, so Remote Worktree consumers
receive repository byte-normalized text rather than Windows CRLF conversions.

## Stage 6 anchor graph v2

Stage 6 uses a fixed-point constraint graph, not one-way filters. Every mandatory
site owns a candidate domain. Hard relationships prune both endpoints until no
more domains change:

- `calls`: caller/callee pairs are kept only when the candidate caller has a
  direct `E8 rel32` edge to the candidate callee. This is bidirectional: a known
  caller can locate an ambiguous callee and a known callee can locate an
  ambiguous caller.
- `rip_target_delta`: preserves exact relationships between RIP-relative global
  targets.
- `rva_delta`: preserves explicitly declared close-family deltas with tolerance.

`regional_shift` is advisory only. It ranks candidates around the median shift of
resolved regional anchors but cannot by itself convert an ambiguous site into a
resolved site.

Every hard graph contradiction blocks Stage 6. The report records:

- initial/final domain sizes;
- the hard relationship(s) that proved each reduction;
- compatible call/RVA pairs and callsite witnesses;
- final contradictions;
- advisory regional rankings.

The lightweight Stage-6 call detector is intentionally labelled
`E8_REL32_HEURISTIC`; Stage 7 Ghidra evidence is the exact-disassembly fallback
when byte-level call evidence is insufficient or contradictory.

## Stage 7 Ghidra Headless

Create the fail-closed evidence bundle first:

```
python maintenance_tools/export_re_bundle.py \
  --exe <new-Warhammer3.exe> \
  --map <promoted-map.json> \
  --out relocation_evidence.zip
```

The bundle now contains the Stage-6 anchor graph, every already-resolved core
anchor, unresolved byte candidates, and a projected search window for sites that
have no byte candidate at all. It never contains the game EXE.

Run Ghidra Headless:

```
python maintenance_tools/run_ghidra_fallback.py \
  --ghidra-home <ghidra-dir> \
  --exe <new-Warhammer3.exe> \
  --bundle relocation_evidence.zip \
  --out-dir reports/ghidra
```

`BscRelocationEvidence.py` exports exact Ghidra evidence for anchors/candidates:
function entry and site offset, instruction/basic-block/edge counts, mnemonic
histogram, exact callsites/callees, and callers. If Stage 6 produced no byte
candidate, it enumerates functions in the projected search window. The wrapper
then runs `consume_ghidra_evidence.py`, which can reduce domains using exact
Ghidra callgraph edges. A `GHIDRA_GRAPH_UNIQUE` result is still review evidence,
not release authorization.

## Optional BinExport / BinDiff fallback

BinDiff is useful when code generation changed enough that no guard/window
candidate is convincing. It requires the old executable (or an old `.BinExport`)
in addition to the new build.

Export the new side from the same analyzed Ghidra project by adding:

```
--binexport-out reports/ghidra/new.BinExport
```

For the old build, produce another BinExport with image-base subtraction enabled.
Then run:

```
python maintenance_tools/run_bindiff_fallback.py \
  --bindiff <bindiff-executable> \
  --baseline-binexport old.BinExport \
  --candidate-binexport new.BinExport \
  --map <promoted-map.json> \
  --out-dir reports/bindiff
```

The wrapper asks BinDiff for both log and binary output, then
`extract_bindiff_matches.py` discovers the BinDiff SQLite function-match table
and extracts matches for the old BSC anchor RVAs. BinDiff results are never
promoted directly: the matched new RVA must be rechecked against Ghidra/static
relationships and the normal build/runtime gates.
