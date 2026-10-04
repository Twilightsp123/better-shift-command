#!/usr/bin/env python3
"""Stage-6 anchor relationship / callgraph resolver.

Builds candidate sets from exact guards and, when needed, normalized masks.
Then applies declarative relationships from the canonical map:
- RVA delta preservation with tolerance
- regional shift coherence
- RIP-relative target delta preservation
- direct rel32 call-edge witnesses inside .pdata runtime functions

The output is a ranked/filtered candidate map. It is still a maintenance
candidate and never authorizes runtime hooks by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import statistics
from pathlib import Path

from pe_tools import (
    PE,
    compile_mask,
    direct_rel32_targets,
    exact_occurrences,
    masked_occurrences,
    parse_rva,
    rip_target,
)


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


def call_targets(mm: mmap.mmap, pe: PE, site_rva: int) -> set[int]:
    fn = pe.runtime_function(site_rva)
    if fn is None:
        return set()
    return {row["target_rva"] for row in direct_rel32_targets(mm, pe, fn)}


def old_shift(native_map: dict, name: str, new_rva: int) -> int:
    return new_rva - parse_rva(native_map["core"][name]["rva"])


def apply_rva_delta(candidates: dict[str, list[int]], rel: dict) -> bool:
    left, right = rel["left"], rel["right"]
    expected = int(rel["expected_delta"])
    tolerance = int(rel.get("tolerance", 0))
    pairs = [
        (a, b)
        for a in candidates[left]
        for b in candidates[right]
        if abs((a - b) - expected) <= tolerance
    ]
    if not pairs:
        return False
    new_left = sorted({a for a, _ in pairs})
    new_right = sorted({b for _, b in pairs})
    changed = new_left != candidates[left] or new_right != candidates[right]
    candidates[left], candidates[right] = new_left, new_right
    return changed


def apply_regional_shift(candidates: dict[str, list[int]], native_map: dict, rel: dict) -> bool:
    site = rel["site"]
    anchor_shifts = []
    for anchor in rel["anchors"]:
        rows = candidates.get(anchor, [])
        if len(rows) != 1:
            return False
        anchor_shifts.append(old_shift(native_map, anchor, rows[0]))
    if not anchor_shifts:
        return False
    center = statistics.median(anchor_shifts)
    tolerance = int(rel.get("tolerance", 0))
    old = parse_rva(native_map["core"][site]["rva"])
    filtered = [x for x in candidates[site] if abs((x - old) - center) <= tolerance]
    if filtered and filtered != candidates[site]:
        candidates[site] = filtered
        return True
    return False


def apply_rip_target_delta(
    mm: mmap.mmap,
    pe: PE,
    candidates: dict[str, list[int]],
    native_map: dict,
    rel: dict,
) -> bool:
    left, right = rel["left"], rel["right"]
    expected = int(rel["expected_delta"])
    tolerance = int(rel.get("tolerance", 0))

    def target(name: str, site: int) -> int | None:
        norm = native_map["core"][name].get("normalization", {})
        rip = norm.get("rip_target")
        if not rip:
            return None
        return rip_target(
            mm,
            pe,
            site,
            int(rip["disp_offset"]),
            int(rip["instruction_end_offset"]),
        )

    pairs = []
    for a in candidates[left]:
        ta = target(left, a)
        if ta is None:
            continue
        for b in candidates[right]:
            tb = target(right, b)
            if tb is not None and abs((ta - tb) - expected) <= tolerance:
                pairs.append((a, b))
    if not pairs:
        return False
    new_left = sorted({a for a, _ in pairs})
    new_right = sorted({b for _, b in pairs})
    changed = new_left != candidates[left] or new_right != candidates[right]
    candidates[left], candidates[right] = new_left, new_right
    return changed


def apply_calls(
    mm: mmap.mmap,
    pe: PE,
    candidates: dict[str, list[int]],
    rel: dict,
) -> bool:
    caller, callee = rel["caller"], rel["callee"]
    targets = candidates.get(callee, [])
    if len(targets) != 1:
        return False
    target = targets[0]
    filtered = [site for site in candidates.get(caller, []) if target in call_targets(mm, pe, site)]
    if filtered and filtered != candidates[caller]:
        candidates[caller] = filtered
        return True
    return False


def run(exe: Path, map_path: Path) -> dict:
    native_map = load_map(map_path)
    with exe.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        pe = PE(mm)
        candidates, methods = initial_candidates(mm, pe, native_map)
        audit: list[dict] = []

        for round_no in range(1, 9):
            changed = False
            for rel in native_map.get("relationships", []):
                before = {k: tuple(v) for k, v in candidates.items()}
                kind = rel["type"]
                if kind == "rva_delta":
                    did = apply_rva_delta(candidates, rel)
                elif kind == "regional_shift":
                    did = apply_regional_shift(candidates, native_map, rel)
                elif kind == "rip_target_delta":
                    did = apply_rip_target_delta(mm, pe, candidates, native_map, rel)
                elif kind == "calls":
                    did = apply_calls(mm, pe, candidates, rel)
                else:
                    raise ValueError(f"unsupported relationship type: {kind}")
                if did:
                    changed = True
                    audit.append(
                        {
                            "round": round_no,
                            "relationship": rel["id"],
                            "type": kind,
                            "before": {k: [f"0x{x:08X}" for x in v] for k, v in before.items() if tuple(candidates[k]) != v},
                            "after": {
                                k: [f"0x{x:08X}" for x in candidates[k]]
                                for k, v in before.items()
                                if tuple(candidates[k]) != v
                            },
                        }
                    )
            if not changed:
                break

        rows = {}
        for name, values in candidates.items():
            rows[name] = {
                "method": methods[name],
                "old_rva": f"0x{parse_rva(native_map['core'][name]['rva']):08X}",
                "candidates": [f"0x{x:08X}" for x in values],
                "resolved_rva": f"0x{values[0]:08X}" if len(values) == 1 else None,
                "resolved": len(values) == 1,
            }

        resolved = sum(row["resolved"] for row in rows.values())
        return {
            "schema": 1,
            "tool": "resolve_relations",
            "actual_sha256": hashlib.sha256(mm).hexdigest(),
            "resolved_core": resolved,
            "core_total": len(rows),
            "all_core_resolved": resolved == len(rows),
            "core": rows,
            "relationship_audit": audit,
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
        "unresolved": [
            name for name, row in report["core"].items() if not row["resolved"]
        ],
    }))
    if not report["all_core_resolved"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
