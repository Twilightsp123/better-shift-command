#!/usr/bin/env python3
"""One-command WH3 update triage for Better Shift Command.

Current implementation covers pipeline stages:
1. canonical native-map contract input
2. exact signature relocation
3. update classification

Later phases add normalized instruction matching, .pdata fingerprints,
relationship/callgraph proof, and Ghidra/BinDiff fallback.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from relocate_exact import candidate_map, printable, run


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "native_maps" / "wh3_9.0.1_6c104a63.json"
DEFAULT_REPORT_ROOT = ROOT / "reports" / "wh3_updates"


def summary_markdown(report: dict) -> str:
    lines = [
        "# WH3 Update Triage",
        "",
        f"- Classification: **{report['classification']}**",
        f"- Expected SHA256: {report['expected_sha256']}",
        f"- Actual SHA256: {report['actual_sha256']}",
        f"- SHA match: {str(report['sha_match']).lower()}",
        "",
        "## Mandatory core sites",
        "",
        "| Site | Old RVA | Result | Resolved RVA | Matches |",
        "|---|---:|---|---:|---:|",
    ]
    for row in report["core"]:
        lines.append(
            f"| {row['name']} | {row['old_rva']} | {row['status']} | "
            f"{row['resolved_rva'] or '-'} | {len(row['matches'])} |"
        )

    lines += [
        "",
        "## Optional sites",
        "",
        "| Site | Old RVA | Result | Resolved RVA | Runtime impact |",
        "|---|---:|---|---:|---|",
    ]
    for row in report["optional"]:
        lines.append(
            f"| {row['name']} | {row['old_rva']} | {row['status']} | "
            f"{row['resolved_rva'] or '-'} | none on CorePath release gate |"
        )

    s = report["summary"]
    lines += [
        "",
        "## Totals",
        "",
        f"- Core same RVA: **{s['core_same_rva']}**",
        f"- Core exact relocated: **{s['core_exact_relocated']}**",
        f"- Core ambiguous: **{s['core_ambiguous']}**",
        f"- Core not found: **{s['core_not_found']}**",
        f"- Optional resolved: **{s['optional_resolved']}/{s['optional_total']}**",
        "",
        "## Next gate",
        "",
    ]

    classification = report["classification"]
    if classification == "CURRENT_BUILD_EXACT":
        lines.append("No address migration required. Continue normal validation.")
    elif classification == "HASH_ONLY":
        lines.append(
            "All mandatory bytes remain at the same RVAs. Review build identity, then "
            "promote only after static/runtime validation."
        )
    elif classification == "RVA_ONLY":
        lines.append(
            "Every mandatory site was exact-relocated without ambiguity. Review the "
            "candidate map, then continue structural/runtime validation."
        )
    elif classification == "PARTIAL_EXACT_AMBIGUOUS":
        lines.append(
            "At least one mandatory guard has multiple exact candidates. Do not promote. "
            "Proceed to normalized and structural matching."
        )
    else:
        lines.append(
            "At least one mandatory guard was not found exactly. Do not promote. "
            "Proceed to normalized instruction matching."
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    args = parser.parse_args()

    report = run(args.exe, args.map)
    sha12 = report["actual_sha256"][:12]
    out_dir = args.report_root / sha12
    out_dir.mkdir(parents=True, exist_ok=True)

    clean = printable(report)
    (out_dir / "exact_relocation.json").write_text(
        json.dumps(clean, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "summary.md").write_text(summary_markdown(report), encoding="utf-8")

    if report["classification"] in {"CURRENT_BUILD_EXACT", "HASH_ONLY", "RVA_ONLY"}:
        candidate = candidate_map(
            report["_candidate_map_source"],
            report["actual_sha256"],
            report["core"],
            report["optional"],
        )
        (out_dir / "candidate_map_exact.json").write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print("========================================")
    print(" Better Shift Command WH3 Update Triage")
    print("========================================")
    print(f"classification       {report['classification']}")
    print(f"expected_sha         {report['expected_sha256']}")
    print(f"actual_sha           {report['actual_sha256']}")
    print(f"core_same_rva        {report['summary']['core_same_rva']}")
    print(f"core_exact_relocated {report['summary']['core_exact_relocated']}")
    print(f"core_ambiguous       {report['summary']['core_ambiguous']}")
    print(f"core_not_found       {report['summary']['core_not_found']}")
    print(
        f"optional_resolved    {report['summary']['optional_resolved']}/"
        f"{report['summary']['optional_total']}"
    )
    print(f"report_dir           {out_dir}")

    if report["classification"] in {"PARTIAL_EXACT_AMBIGUOUS", "CODEGEN_OR_SEMANTIC_DRIFT"}:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
