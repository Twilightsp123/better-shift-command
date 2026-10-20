# BSC R49 — memreader Plus 0.13.0 Passive Sampler Hardening

**Research-only. NOT AN INSTALLABLE MOD. No native DLL, Warhammer3.exe, raw player addresses, or third-party .pack files in this ZIP.**

## Files

- `docs/current/N1_R49_MEMREADER_PASSIVE_SAMPLER_CONTRACT_20261020.md` — Chinese technical report and caveats
- `maintenance_tools/native_shift_re/bsc_r49_guarded_passive_sampler_research.lua` — manual no-hook sampler prototype (not auto-loaded)
- `maintenance_tools/native_shift_re/r49_spatial_evidence_preflight.py` — strict offline gate for R49 snapshots
- `maintenance_tools/native_shift_re/r47_spatial_action_triage.py` — R47 offline shape engine dependency
- `maintenance_tools/native_shift_re/audit_r49_sampler_contract.py` and `audit_r47_action_fingerprints_20261020.py` — private original-EXE and two archive static audits
- `tests/test_r49_sampler_mock.lua` — native-typed-pointer mock, 20 scenarios
- `tests/test_r49_spatial_evidence_preflight.py` and `tests/test_r49_static_contract.py` — 20 Python tests combined
- `evidence/` — static public evidence / non-private test runs / synthetic JSONL
- `prior/BSC_R48_LEGACY_TRACE_SPATIAL_REUSE_20261020.zip` — preceding complete archive (no game assets)

## Offline reproduction

```bash
texluac -p maintenance_tools/native_shift_re/bsc_r49_guarded_passive_sampler_research.lua
texlua tests/test_r49_sampler_mock.lua maintenance_tools/native_shift_re/bsc_r49_guarded_passive_sampler_research.lua
python -m unittest discover -s tests -p 'test_r49_*.py' -q
python maintenance_tools/native_shift_re/r49_spatial_evidence_preflight.py --input evidence/synthetic_r49_samples.jsonl --output /tmp/r49_report.json
```

With the original, **private** user inputs available locally, set environment variables `BSC_CURRENT_EXE`, `BSC_DERPY_ZIP`, `BSC_MEMREADER_ZIP` and re-run Python tests. No game process access required.

**No gameplay fix; the user does not need to repeat the defect demonstration.**
