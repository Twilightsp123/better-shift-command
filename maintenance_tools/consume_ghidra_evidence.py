#!/usr/bin/env python3
"""Reduce Stage-7 candidate domains using exact Ghidra callgraph evidence.

This tool produces review evidence only. Even a unique Ghidra result is not
release-authorized until the normal static/build/runtime gates pass.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _record_rva(record: dict) -> int:
    return int(record["site_rva"], 0)


def _call_targets(record: dict) -> set[int]:
    out = set()
    for row in record.get("direct_calls", []):
        target = row.get("target_rva")
        if target:
            out.add(int(target, 0))
    return out


def _site_records(evidence: dict, site: str) -> list[dict]:
    prefixes = ("candidate:" + site + ":", "window:" + site + ":")
    rows = []
    for key, record in evidence.get("records", {}).items():
        if key.startswith(prefixes):
            item = dict(record)
            item["record_key"] = key
            rows.append(item)
    return rows


def _anchor_record(evidence: dict, name: str) -> dict | None:
    return evidence.get("records", {}).get("anchor:" + name)


def resolve(bundle: dict, evidence: dict) -> dict:
    sites = bundle.get("sites", {})
    resolved = {
        name: int(rva, 0)
        for name, rva in bundle.get("resolved_core", {}).items()
        if rva
    }
    domains = {site: _site_records(evidence, site) for site in sites}
    initial_counts = {site: len(rows) for site, rows in domains.items()}
    proof = {site: [] for site in domains}
    audit = []

    # Add resolved anchors as singleton pseudo-domains for pair evaluation.
    def rows_for(name: str) -> list[dict]:
        if name in domains:
            return domains[name]
        anchor = _anchor_record(evidence, name)
        if anchor:
            item = dict(anchor); item["record_key"] = "anchor:" + name
            return [item]
        if name in resolved:
            return [{"site_rva": f"0x{resolved[name]:08X}", "direct_calls": [], "record_key": "resolved:" + name}]
        return []

    relationships = []
    seen = set()
    for site, item in sites.items():
        for rel in item.get("relationships", []):
            rid = rel.get("id")
            if rid and rid not in seen:
                seen.add(rid); relationships.append(rel)

    for round_no in range(1, 9):
        changed = False
        for rel in relationships:
            if rel.get("strength", "hard") != "hard":
                continue
            kind = rel.get("type")
            if kind == "calls":
                left, right = rel["caller"], rel["callee"]
                left_rows, right_rows = rows_for(left), rows_for(right)
                if not left_rows or not right_rows:
                    continue
                pairs = []
                for a in left_rows:
                    targets = _call_targets(a)
                    for b in right_rows:
                        if _record_rva(b) in targets:
                            pairs.append((a, b))
            elif kind == "rva_delta":
                left, right = rel["left"], rel["right"]
                left_rows, right_rows = rows_for(left), rows_for(right)
                if not left_rows or not right_rows:
                    continue
                expected = int(rel["expected_delta"]); tol = int(rel.get("tolerance", 0))
                pairs = [
                    (a, b) for a in left_rows for b in right_rows
                    if abs((_record_rva(a) - _record_rva(b)) - expected) <= tol
                ]
            else:
                continue
            if not pairs:
                continue
            before = {left: len(left_rows), right: len(right_rows)}
            if left in domains:
                keys = {a["record_key"] for a, _ in pairs}
                new = [x for x in domains[left] if x["record_key"] in keys]
                if len(new) != len(domains[left]):
                    domains[left] = new; changed = True; proof[left].append(rel["id"])
            if right in domains:
                keys = {b["record_key"] for _, b in pairs}
                new = [x for x in domains[right] if x["record_key"] in keys]
                if len(new) != len(domains[right]):
                    domains[right] = new; changed = True; proof[right].append(rel["id"])
            after = {left: len(rows_for(left)), right: len(rows_for(right))}
            if after != before:
                audit.append({"round": round_no, "relationship": rel["id"], "type": kind, "before": before, "after": after})
        if not changed:
            break

    results = {}
    for site, rows in domains.items():
        call_proofs = []
        touched = {rel.get("id"): rel for rel in relationships}
        for rid in proof[site]:
            if touched.get(rid, {}).get("type") == "calls":
                call_proofs.append(rid)
        unique = len(rows) == 1 and bool(call_proofs)
        results[site] = {
            "initial_candidate_count": initial_counts[site],
            "final_candidate_count": len(rows),
            "candidates": [row["site_rva"] for row in rows],
            "resolution": "GHIDRA_GRAPH_UNIQUE" if unique else None,
            "resolved_rva": rows[0]["site_rva"] if unique else None,
            "proof_relations": proof[site],
            "ghidra_call_proofs": call_proofs,
            "release_authorized": False,
        }
    return {
        "schema": 1,
        "tool": "consume_ghidra_evidence",
        "exe_sha256": evidence.get("exe_sha256"),
        "sites": results,
        "audit": audit,
        "release_authorized": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle-json", required=True, type=Path, help="extracted unresolved.json")
    ap.add_argument("--ghidra-evidence", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    bundle = json.loads(args.bundle_json.read_text(encoding="utf-8"))
    evidence = json.loads(args.ghidra_evidence.read_text(encoding="utf-8"))
    result = resolve(bundle, evidence)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "resolved": {name: row["resolved_rva"] for name, row in result["sites"].items() if row["resolved_rva"]},
        "release_authorized": False,
    }))


if __name__ == "__main__":
    main()
