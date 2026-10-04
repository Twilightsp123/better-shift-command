#!/usr/bin/env python3
"""Run BinDiff on baseline/new BinExport files and extract BSC anchor matches."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from extract_bindiff_matches import extract


def run(bindiff: Path, baseline: Path, candidate: Path, native_map: dict, out_dir: Path) -> dict:
    exe = bindiff if bindiff.is_file() else Path(shutil.which(str(bindiff)) or "")
    if not exe or not exe.is_file():
        raise FileNotFoundError(f"BinDiff executable not found: {bindiff}")
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(exe),
        f"--primary={baseline.resolve()}",
        f"--secondary={candidate.resolve()}",
        f"--output_dir={out_dir.resolve()}",
        "--output_format=log,bin",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    (out_dir / "bindiff.log").write_text(
        "$ " + " ".join(cmd) + "\n" + proc.stdout + proc.stderr,
        encoding="utf-8",
    )
    if proc.returncode:
        raise RuntimeError(f"BinDiff failed ({proc.returncode}); see bindiff.log")
    databases = sorted(out_dir.glob("*.BinDiff"), key=lambda p: p.stat().st_mtime)
    if not databases:
        raise RuntimeError("BinDiff produced no .BinDiff database")
    db = databases[-1]
    matches = extract(db, native_map)
    out = out_dir / "bindiff_anchor_matches.json"
    out.write_text(json.dumps(matches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "schema": 1,
        "tool": "run_bindiff_fallback",
        "database": str(db.resolve()),
        "anchor_matches": str(out.resolve()),
        "match_count": len(matches["matches"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bindiff", required=True, type=Path)
    ap.add_argument("--baseline-binexport", required=True, type=Path)
    ap.add_argument("--candidate-binexport", required=True, type=Path)
    ap.add_argument("--map", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()
    native_map = json.loads(args.map.read_text(encoding="utf-8"))
    print(json.dumps(run(
        args.bindiff,
        args.baseline_binexport,
        args.candidate_binexport,
        native_map,
        args.out_dir,
    )))


if __name__ == "__main__":
    main()
