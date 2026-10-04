#!/usr/bin/env python3
"""Run Stage-7 Ghidra Headless evidence extraction, optionally BinExport.

Ghidra is an external maintenance dependency and is intentionally not required
for Stages 1-6 or for the runtime bridge.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from consume_ghidra_evidence import resolve as resolve_evidence

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "maintenance_tools" / "ghidra"


def analyze_headless(ghidra_home: Path) -> Path:
    candidates = [
        ghidra_home / "support" / "analyzeHeadless",
        ghidra_home / "support" / "analyzeHeadless.bat",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("Ghidra analyzeHeadless not found under --ghidra-home/support")


def run_command(cmd: list[str], log_path: Path) -> None:
    launch = cmd
    if cmd and str(cmd[0]).lower().endswith(".bat") and os.name == "nt":
        launch = ["cmd", "/c"] + cmd
    result = subprocess.run(launch, capture_output=True, text=True)
    log_path.write_text(
        "$ " + " ".join(str(x) for x in cmd) + "\n" + result.stdout + result.stderr,
        encoding="utf-8",
    )
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}); see {log_path}")


def run(
    ghidra_home: Path,
    exe: Path,
    bundle: Path,
    out_dir: Path,
    binexport_out: Path | None = None,
    timeout_seconds: int = 1200,
) -> dict:
    headless = analyze_headless(ghidra_home)
    out_dir.mkdir(parents=True, exist_ok=True)
    extracted = out_dir / "bundle"
    if extracted.exists():
        shutil.rmtree(extracted)
    extracted.mkdir(parents=True)
    with zipfile.ZipFile(bundle) as z:
        z.extractall(extracted)
    unresolved = extracted / "unresolved.json"
    if not unresolved.is_file():
        raise ValueError("Stage-7 bundle missing unresolved.json")

    evidence = out_dir / "ghidra_evidence.json"
    project_dir = out_dir / "ghidra_project"
    project_dir.mkdir(parents=True, exist_ok=True)
    project_name = "BSC_Relocation"

    import_cmd = [
        str(headless),
        str(project_dir),
        project_name,
        "-import",
        str(exe.resolve()),
        "-overwrite",
        "-analysisTimeoutPerFile",
        str(timeout_seconds),
        "-scriptPath",
        str(SCRIPT_DIR.resolve()),
        "-postScript",
        "BscRelocationEvidence.py",
        str(unresolved.resolve()),
        str(evidence.resolve()),
    ]
    run_command(import_cmd, out_dir / "ghidra_import.log")
    if not evidence.is_file():
        raise RuntimeError("Ghidra completed without ghidra_evidence.json")

    if binexport_out is not None:
        binexport_out.parent.mkdir(parents=True, exist_ok=True)
        export_cmd = [
            str(headless),
            str(project_dir),
            project_name,
            "-process",
            exe.name,
            "-preScript",
            "BinExport.java",
            str(binexport_out.resolve()),
            "Subtract Imagebase;Prepend Namespace to Function Names",
            "-noanalysis",
        ]
        run_command(export_cmd, out_dir / "ghidra_binexport.log")
        if not binexport_out.is_file():
            raise RuntimeError(
                "BinExport.java did not create output; install/enable the Ghidra BinExport extension"
            )

    payload = json.loads(evidence.read_text(encoding="utf-8"))
    bundle_payload = json.loads(unresolved.read_text(encoding="utf-8"))
    expected_sha = str(bundle_payload.get("manifest", {}).get("exe_sha256") or "").lower()
    evidence_sha = str(payload.get("exe_sha256") or "").lower()
    if not expected_sha or not evidence_sha or evidence_sha != expected_sha:
        raise RuntimeError(
            "Ghidra evidence EXE SHA mismatch: expected=%s actual=%s"
            % (expected_sha or "MISSING", evidence_sha or "MISSING")
        )
    resolution = resolve_evidence(bundle_payload, payload)
    resolution_path = out_dir / "ghidra_resolution.json"
    resolution_path.write_text(json.dumps(resolution, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {
        "schema": 1,
        "tool": "run_ghidra_fallback",
        "exe": str(exe.resolve()),
        "bundle": str(bundle.resolve()),
        "evidence": str(evidence.resolve()),
        "resolution": str(resolution_path.resolve()),
        "resolved_sites": {
            name: row["resolved_rva"]
            for name, row in resolution.get("sites", {}).items()
            if row.get("resolved_rva")
        },
        "record_count": len(payload.get("records", {})),
        "binexport": None if binexport_out is None else str(binexport_out.resolve()),
    }
    (out_dir / "ghidra_fallback_result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ghidra-home", type=Path)
    ap.add_argument("--exe", required=True, type=Path)
    ap.add_argument("--bundle", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--binexport-out", type=Path)
    ap.add_argument("--timeout-seconds", type=int, default=1200)
    args = ap.parse_args()
    ghidra_home = args.ghidra_home or (Path(os.environ["GHIDRA_HOME"]) if os.environ.get("GHIDRA_HOME") else None)
    if ghidra_home is None:
        raise SystemExit("--ghidra-home or GHIDRA_HOME is required")
    print(json.dumps(run(
        ghidra_home,
        args.exe,
        args.bundle,
        args.out_dir,
        args.binexport_out,
        args.timeout_seconds,
    )))


if __name__ == "__main__":
    main()
