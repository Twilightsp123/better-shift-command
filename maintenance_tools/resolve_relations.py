#!/usr/bin/env python3
"""Stage-6 anchor graph / callgraph resolver.

Candidate sets come from exact or relocation-normalized byte guards. Hard graph
relationships are propagated bidirectionally to a fixed point. Advisory regional
shift evidence is reported but never resolves ambiguity by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
from pathlib import Path

from anchor_graph import propagate
from pe_tools import PE, compile_mask, exact_occurrences, masked_occurrences, parse_rva


MIN_STRUCTURAL_SUPPORT = 2


def classify_resolution(method: str, old_rva: int, node: dict) -> dict:
    domain_unique = node["final_candidate_count"] == 1
    relationship_candidate = domain_unique and node["initial_candidate_count"] != 1
    support = node.get("support_relations", [])
    relationship_resolved = relationship_candidate and len(support) >= MIN_STRUCTURAL_SUPPORT
    resolved_now = domain_unique and (node["initial_candidate_count"] == 1 or relationship_resolved)
    if relationship_resolved:
        final_method = method + "_RELATION_RESOLVED"
    elif resolved_now and node["initial_candidate_count"] == 1:
        final_method = method + "_UNIQUE"
    else:
        final_method = method
    return {
        "method": final_method,
        "base_method": method,
        "old_rva": f"0x{old_rva:08X}",
        "initial_candidate_count": node["initial_candidate_count"],
        "candidates": node["candidates"],
        "resolved_rva": node["resolved_rva"],
        "resolved": resolved_now,
        "relationship_resolved": relationship_resolved,
        "proof_relations": node["proof_relations"],
        "support_relations": support,
        "minimum_structural_support_met": (
            node["initial_candidate_count"] == 1 or len(support) >= MIN_STRUCTURAL_SUPPORT
        ),
    }


def load_map(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("unsupported native map schema")
    return data


def initial_candidates(mm: mmap.mmap, pe: PE, native_map: dict) -> tuple[dict[str, list[int]], dict[str, str]]:
    candidates: dict[str, list[int]] = {}
    methods: dict[str, str] = {}
    for name, spec in native_map["core"].items():
        pattern = bytes.fromhex(spec["guard"])
        exact = exact_occurrences(mm, pe, pattern)
        if exact:
            candidates[name] = exact
            methods[name] = "EXACT"
            continue
        norm = spec.get("normalization")
        if norm and norm.get("kind") == "relocation_mask":
            mask = compile_mask(len(pattern), norm.get("mask_ranges", []))
            candidates[name] = masked_occurrences(mm, pe, pattern, mask)
            methods[name] = "NORMALIZED"
        else:
            candidates[name] = []
            methods[name] = "NONE"
    return candidates, methods


def run(exe: Path, map_path: Path) -> dict:
    native_map = load_map(map_path)
    with exe.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        pe = PE(mm)
        candidates, methods = initial_candidates(mm, pe, native_map)
        graph = propagate(mm, pe, native_map, candidates)

        rows = {}
        for name, node in graph["nodes"].items():
            rows[name] = classify_resolution(
                methods[name], parse_rva(native_map["core"][name]["rva"]), node
            )

        resolved = sum(row["resolved"] for row in rows.values())
        all_core_resolved = resolved == len(rows) and graph["consistent"]
        return {
            "schema": 2,
            "tool": "resolve_relations",
            "resolution_engine": graph["engine"],
            "actual_sha256": hashlib.sha256(mm).hexdigest(),
            "resolved_core": resolved,
            "core_total": len(rows),
            "all_core_resolved": all_core_resolved,
            "graph_consistent": graph["consistent"],
            "core": rows,
            "relationship_audit": graph["hard_edge_audit"],
            "anchor_graph": graph,
        }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", required=True, type=Path)
    ap.add_argument("--map", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = run(args.exe, args.map)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "resolved_core": report["resolved_core"],
        "core_total": report["core_total"],
        "all_core_resolved": report["all_core_resolved"],
        "graph_consistent": report["graph_consistent"],
        "unresolved": [name for name, row in report["core"].items() if not row["resolved"]],
        "contradictions": report["anchor_graph"]["contradictions"],
    }))
    if not report["all_core_resolved"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
