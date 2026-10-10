# N1 — V3-active MOVE ↔ Mode 0 / model pose / group cohesion: bounded call audit

**2026-10-10.** This is a **new executable analysis tool and tests**, not another proven cause or a patch. It builds on the latest native-group-cohesion finding in `N1_903_REAL_TWO_BURSTS_AND_GROUP_COHESION.md`. The live research branch was read at `f4427b6` before this change.

## Correct current causal inference

The same mode-0 unit had two rapid native MOVE-work bursts (16 in 711 ms and 15 in 683 ms) but only the later burst was followed by strong intra-card crowding (29/40 compressed samples versus 0/26). Thus fast queue processing **alone** is not a sufficient explanation. Native `0x030D572C` computes member-to-generated-target distance and can stamp group readiness; the recorded `0x03044FAF`, `0x0304516B`, `0x03283806` callsites enter `0x030D56BC`. This is **not** proof that the feature gates the V3-observed mode-0 MOVE controller. The real V3 actor modes were 0 in all sampled member-mode readings; never force action modes or local path segment indices.

## Implemented

`maintenance_tools/native_shift_re/audit_903_active_cohesion_links.py`:

- Reads an unmodified PE32+ AMD64 target **only if exact SHA256 matches** `518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a`.
- Checks nine previously documented direct `E8` edges from real MOVE work, task tick, member pose update, mode-0 strategy and group-distance callers. A call displacement mismatch is a failure, not a fallback to guessed addresses.
- Uses GNU `objdump` on short, file-backed executable fragments to enumerate instruction-boundary `E8` calls and visibly unresolved indirect callsites around the known roots; emits JSON evidence for follow-up producer/consumer analysis.
- Never writes the EXE, installs hooks, selects a runtime patch condition, or asserts that lack of a direct `E8` edge excludes an indirect or dataflow relation. The bounded windows are **not** complete function bodies.

`tests/test_native_shift_re_active_cohesion.py`: eight isolated tests cover the scope contract, signed forward/backward call targets, instruction-boundary filtering, actual `objdump` decoding on synthetic x64 bytes, PE section mapping, SHA failure, no EXE overwrite and nonpatching design. **8/8 passed in the handoff development container using a minimal local test compatibility shim for the existing repository PE parser.** Tests with the repository's actual `scout_pe.py` in CI have not yet been observed.

## Reproduce

```bash
python -m unittest discover -s tests -p 'test_native_shift_re_active_cohesion.py' -v
python maintenance_tools/native_shift_re/audit_903_active_cohesion_links.py \
  --exe /path/to/Warhammer3.exe \
  --report /path/to/active_cohesion_links.json \
  --objdump objdump
```

## Actual evidence grade and single blocker

- **Already reported from prior pinned-EXE work:** active MOVE → task chain, native member pose/rate writer, mode-0 strategy delegation, group distance evaluator and three callers. See predecessor files for those original checks.
- **New now:** tool source and eight synthetic local tests. No new same-EXE trace has been executed here because the only mounted upload was `BSC_AI_HANDOFF_20261010.md`; neither the 241 MiB original EXE nor `captured_move_v3.jsonl` was accessible. No Windows build or WH3 trial happened.
- **One critical missing causal connection:** follow the **actual V3 mode-0 MOVE** route/state into the source of `member+0x2E0` local motion targets **and** determine whether original group readiness/distance updates govern that input. This requires original machine-code/dataflow around the indirect calls and producers, not an inferred callgraph or another synthetic geometry example.

**Decision:** no DLL/PACK / no native target mutation is justified yet. Keep the Lua reissuer retired; do not alter OrderHead, member modes, random delay, or local segment indexes. A safe, default-off native patch is gated on discovering an actual original policy predicate and ABI/lifetime safety. This audit is an executable narrowing step, not a gameplay fix.
