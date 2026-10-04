#!/usr/bin/env python3
"""One-command WH3 update triage and relocation pipeline for Better Shift Command.

Implemented stages:
1. canonical JSON source of truth
2. exact guard relocation
3. update classification
4. relocation-normalized guard matching
5. .pdata/runtime-function fingerprints
6. declarative anchor relationship/callgraph resolution + constructor/VTable derivation

Stage 7 remains an explicit fallback only when Stage 6 cannot close the map.
Generated maps are never release-authorized automatically.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_candidate_map import generate as generate_candidate
from native_map_config import current_map_path
from relocate_exact import printable, run as run_exact
from relocate_normalized import run as run_normalized
from resolve_relations import run as run_relations
from verify_candidate_map import verify as verify_candidate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = current_map_path()
DEFAULT_REPORT_ROOT = ROOT / "reports" / "wh3_updates"


def summary_markdown(exact: dict, normalized: dict, relations: dict, candidate: dict | None) -> str:
    final_status = (
        "STRUCTURALLY_RESOLVED_CANDIDATE"
        if relations["all_core_resolved"]
        else "MANUAL_REVERSE_ENGINEERING_REQUIRED"
    )
    lines = [
        "# WH3 Update Triage",
        "",
        f"- Exact classification: **{exact['classification']}**",
        f"- Pipeline status: **{final_status}**",
        f"- Expected SHA256: {exact['expected_sha256']}",
        f"- Actual SHA256: {exact['actual_sha256']}",
        f"- Mandatory core resolved after Stage 6: **{relations['resolved_core']}/{relations['core_total']}**",
        f"- Anchor graph: **{relations.get('resolution_engine', 'UNKNOWN')}**, consistent={relations.get('graph_consistent')}",
        "",
        "## Core relocation",
        "",
        "| Site | Exact result | Stage-6 resolved RVA | Method |",
        "|---|---|---:|---|",
    ]
    exact_by_name = {row["name"]: row for row in exact["core"]}
    for name, row in relations["core"].items():
        erow = exact_by_name[name]
        lines.append(
            f"| {name} | {erow['status']} | {row['resolved_rva'] or '-'} | {row['method']} |"
        )

    if normalized["core"]:
        lines += [
            "",
            "## Normalized sites",
            "",
            "| Site | Result | Candidate count |",
            "|---|---|---:|",
        ]
        for row in normalized["core"]:
            lines.append(f"| {row['name']} | {row['status']} | {row['match_count']} |")

    lines += ["", "## Relationship reductions", ""]
    if relations["relationship_audit"]:
        for item in relations["relationship_audit"]:
            lines.append(
                f"- Round {item['round']}: {item['relationship']} ({item['type']}) reduced candidates."
            )
    else:
        lines.append("- No structural reduction was needed.")

    if candidate is not None:
        identity = candidate["candidate"]["order_identity"]
        lines += [
            "",
            "## Re-derived order identity",
            "",
            f"- Base constructor: {identity['base_constructor']}",
            f"- Full Move constructor: {identity['full_move_constructor']}",
            f"- Attack constructor: {identity['attack_constructor']}",
            f"- Full Move VTable: {identity['full_move_vtable']}",
            f"- Attack VTable: {identity['attack_vtable']}",
            f"- Simple/Intercept Move constructor: {identity['simple_intercept_move_constructor']}",
            f"- Simple/Intercept Move VTable: {identity['simple_intercept_move_vtable']}",
            "",
            "The generated map is NOT release-authorized. Continue with source generation, "
            "prebuild checks, Windows native tests, and WH3 runtime smoke.",
        ]
    else:
        lines += [
            "",
            "## Next action",
            "",
            "Stage 6 did not uniquely resolve every mandatory core site. Produce the evidence "
            "bundle and use Stage 7 Ghidra/BinDiff fallback only for the remaining sites.",
        ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--game-version", default="unknown")
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    args = parser.parse_args()

    exact = run_exact(args.exe, args.map)
    normalized = run_normalized(args.exe, args.map)
    relations = run_relations(args.exe, args.map)

    sha12 = exact["actual_sha256"][:12]
    out_dir = args.report_root / sha12
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "exact_relocation.json").write_text(
        json.dumps(printable(exact), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "normalized_relocation.json").write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "relation_resolution.json").write_text(
        json.dumps(relations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    candidate = None
    verification = None
    if relations["all_core_resolved"]:
        candidate = generate_candidate(args.exe, args.map, args.game_version)
        (out_dir / "candidate_map.json").write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        verification = verify_candidate(args.exe, candidate)
        (out_dir / "candidate_static_verification.json").write_text(
            json.dumps(verification, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    (out_dir / "summary.md").write_text(
        summary_markdown(exact, normalized, relations, candidate),
        encoding="utf-8",
    )

    print("========================================")
    print(" Better Shift Command WH3 Update Pipeline")
    print("========================================")
    print(f"exact_classification  {exact['classification']}")
    print(f"actual_sha            {exact['actual_sha256']}")
    print(f"core_stage6           {relations['resolved_core']}/{relations['core_total']}")
    print(f"candidate_generated   {candidate is not None}")
    print(f"report_dir             {out_dir}")
    if candidate is not None:
        print("release_authorized     false")
        print("next_gate              GENERATE_SOURCE_AND_VALIDATE")
    else:
        print("next_gate              STAGE7_FALLBACK")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
