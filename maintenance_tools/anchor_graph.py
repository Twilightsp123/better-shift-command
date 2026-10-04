#!/usr/bin/env python3
"""Constraint graph for WH3 native anchor relocation.

Stage 6 must be fail-closed. Hard relationships reduce candidate domains in both
 directions until a fixed point. Advisory relationships may rank candidates but
never turn ambiguity into an automatic resolution.
"""
from __future__ import annotations

import statistics
from collections.abc import Callable
from typing import Any

from pe_tools import PE, direct_rel32_targets, parse_rva, rip_target


HARD_TYPES = {"calls", "rva_delta", "rip_target_delta"}
ADVISORY_TYPES = {"regional_shift"}


def relationship_strength(rel: dict) -> str:
    explicit = rel.get("strength")
    if explicit in {"hard", "advisory"}:
        return explicit
    if rel.get("type") in ADVISORY_TYPES:
        return "advisory"
    return "hard"


def relationship_endpoints(rel: dict) -> tuple[str, str] | None:
    kind = rel.get("type")
    if kind in {"rva_delta", "rip_target_delta"}:
        return rel["left"], rel["right"]
    if kind == "calls":
        return rel["caller"], rel["callee"]
    return None


class CallIndex:
    """Caches heuristic E8 rel32 targets per containing .pdata function."""

    def __init__(self, mm: Any, pe: PE):
        self.mm = mm
        self.pe = pe
        self._cache: dict[int, set[int]] = {}
        self._sites: dict[int, dict[int, list[int]]] = {}

    def targets(self, site_rva: int) -> set[int]:
        fn = self.pe.runtime_function(site_rva)
        if fn is None:
            return set()
        if fn.begin not in self._cache:
            by_target: dict[int, list[int]] = {}
            for row in direct_rel32_targets(self.mm, self.pe, fn):
                by_target.setdefault(row["target_rva"], []).append(row["call_rva"])
            self._sites[fn.begin] = by_target
            self._cache[fn.begin] = set(by_target)
        return self._cache[fn.begin]

    def callsites(self, site_rva: int, target_rva: int) -> list[int]:
        fn = self.pe.runtime_function(site_rva)
        if fn is None:
            return []
        self.targets(site_rva)
        return list(self._sites.get(fn.begin, {}).get(target_rva, []))


def _call_pairs(
    domains: dict[str, list[int]], rel: dict, calls: CallIndex
) -> tuple[str, str, list[tuple[int, int]], list[dict]]:
    left, right = rel["caller"], rel["callee"]
    right_set = set(domains.get(right, []))
    pairs: list[tuple[int, int]] = []
    witnesses: list[dict] = []
    for caller in domains.get(left, []):
        matches = sorted(right_set.intersection(calls.targets(caller)))
        for callee in matches:
            pairs.append((caller, callee))
            if len(witnesses) < 64:
                witnesses.append(
                    {
                        "caller": f"0x{caller:08X}",
                        "callee": f"0x{callee:08X}",
                        "callsites": [
                            f"0x{x:08X}" for x in calls.callsites(caller, callee)
                        ],
                        "source": "E8_REL32_HEURISTIC",
                    }
                )
    return left, right, pairs, witnesses


def _rva_delta_pairs(
    domains: dict[str, list[int]], rel: dict
) -> tuple[str, str, list[tuple[int, int]], list[dict]]:
    left, right = rel["left"], rel["right"]
    expected = int(rel["expected_delta"])
    tolerance = int(rel.get("tolerance", 0))
    pairs = [
        (a, b)
        for a in domains.get(left, [])
        for b in domains.get(right, [])
        if abs((a - b) - expected) <= tolerance
    ]
    witnesses = [
        {
            "left": f"0x{a:08X}",
            "right": f"0x{b:08X}",
            "actual_delta": a - b,
            "expected_delta": expected,
            "tolerance": tolerance,
        }
        for a, b in pairs[:64]
    ]
    return left, right, pairs, witnesses


def _rip_delta_pairs(
    mm: Any,
    pe: PE,
    native_map: dict,
    domains: dict[str, list[int]],
    rel: dict,
) -> tuple[str, str, list[tuple[int, int]], list[dict]]:
    left, right = rel["left"], rel["right"]
    expected = int(rel["expected_delta"])
    tolerance = int(rel.get("tolerance", 0))
    lspec = native_map["core"][left].get("normalization", {}).get("rip_target")
    rspec = native_map["core"][right].get("normalization", {}).get("rip_target")
    if not lspec or not rspec:
        return left, right, [], []
    left_targets = {
        a: rip_target(mm, pe, a, int(lspec["disp_offset"]), int(lspec["instruction_end_offset"]))
        for a in domains.get(left, [])
    }
    right_targets = {
        b: rip_target(mm, pe, b, int(rspec["disp_offset"]), int(rspec["instruction_end_offset"]))
        for b in domains.get(right, [])
    }
    pairs: list[tuple[int, int]] = []
    witnesses: list[dict] = []
    for a, ta in left_targets.items():
        if ta is None:
            continue
        for b, tb in right_targets.items():
            if tb is None:
                continue
            actual = ta - tb
            if abs(actual - expected) <= tolerance:
                pairs.append((a, b))
                if len(witnesses) < 64:
                    witnesses.append(
                        {
                            "left": f"0x{a:08X}",
                            "right": f"0x{b:08X}",
                            "left_target": f"0x{ta:08X}",
                            "right_target": f"0x{tb:08X}",
                            "actual_delta": actual,
                            "expected_delta": expected,
                        }
                    )
    return left, right, pairs, witnesses


def hard_pairs(
    mm: Any,
    pe: PE,
    native_map: dict,
    domains: dict[str, list[int]],
    rel: dict,
    calls: CallIndex,
) -> tuple[str, str, list[tuple[int, int]], list[dict]]:
    kind = rel["type"]
    if kind == "calls":
        return _call_pairs(domains, rel, calls)
    if kind == "rva_delta":
        return _rva_delta_pairs(domains, rel)
    if kind == "rip_target_delta":
        return _rip_delta_pairs(mm, pe, native_map, domains, rel)
    raise ValueError(f"unsupported hard relationship type: {kind}")


def regional_advisory(native_map: dict, domains: dict[str, list[int]], rel: dict) -> dict:
    site = rel["site"]
    shifts = []
    used = []
    for anchor in rel.get("anchors", []):
        values = domains.get(anchor, [])
        if len(values) != 1:
            continue
        old = parse_rva(native_map["core"][anchor]["rva"])
        shifts.append(values[0] - old)
        used.append(anchor)
    if not shifts:
        return {
            "id": rel["id"],
            "type": rel["type"],
            "strength": "advisory",
            "site": site,
            "status": "INSUFFICIENT_ANCHORS",
            "ranked": [],
        }
    center = statistics.median(shifts)
    tolerance = int(rel.get("tolerance", 0))
    old_site = parse_rva(native_map["core"][site]["rva"])
    ranked = []
    for candidate in domains.get(site, []):
        shift = candidate - old_site
        ranked.append(
            {
                "rva": f"0x{candidate:08X}",
                "shift": shift,
                "distance_from_center": abs(shift - center),
                "within_tolerance": abs(shift - center) <= tolerance,
            }
        )
    ranked.sort(key=lambda row: (row["distance_from_center"], row["rva"]))
    return {
        "id": rel["id"],
        "type": rel["type"],
        "strength": "advisory",
        "site": site,
        "status": "RANKED",
        "anchor_shift_median": center,
        "anchors_used": used,
        "tolerance": tolerance,
        "ranked": ranked[:16],
    }


def propagate(
    mm: Any,
    pe: PE,
    native_map: dict,
    initial_domains: dict[str, list[int]],
    max_rounds: int = 12,
) -> dict:
    domains = {name: sorted(set(values)) for name, values in initial_domains.items()}
    initial_counts = {name: len(values) for name, values in domains.items()}
    calls = CallIndex(mm, pe)
    audit: list[dict] = []
    contradictions: list[dict] = []
    proof_relations: dict[str, list[str]] = {name: [] for name in domains}

    hard_rels = [
        rel for rel in native_map.get("relationships", [])
        if relationship_strength(rel) == "hard"
    ]
    priority = {"calls": 0, "rip_target_delta": 1, "rva_delta": 2}
    hard_rels.sort(key=lambda rel: (priority.get(rel.get("type"), 99), -int(rel.get("weight", 0)), rel.get("id", "")))
    for round_no in range(1, max_rounds + 1):
        changed = False
        for rel in hard_rels:
            kind = rel.get("type")
            if kind not in HARD_TYPES:
                raise ValueError(f"unsupported hard relationship type: {kind}")
            left, right, pairs, witnesses = hard_pairs(
                mm, pe, native_map, domains, rel, calls
            )
            before_left = list(domains.get(left, []))
            before_right = list(domains.get(right, []))
            if not before_left or not before_right:
                continue
            if not pairs:
                contradictions.append(
                    {
                        "round": round_no,
                        "relationship": rel["id"],
                        "type": kind,
                        "left": left,
                        "right": right,
                        "left_count": len(before_left),
                        "right_count": len(before_right),
                        "status": "NO_COMPATIBLE_PAIR",
                    }
                )
                continue
            new_left = sorted({a for a, _ in pairs})
            new_right = sorted({b for _, b in pairs})
            if new_left != before_left or new_right != before_right:
                domains[left], domains[right] = new_left, new_right
                changed = True
                if new_left != before_left and rel["id"] not in proof_relations[left]:
                    proof_relations[left].append(rel["id"])
                if new_right != before_right and rel["id"] not in proof_relations[right]:
                    proof_relations[right].append(rel["id"])
                audit.append(
                    {
                        "round": round_no,
                        "relationship": rel["id"],
                        "type": kind,
                        "strength": "hard",
                        "left": left,
                        "right": right,
                        "before": {
                            left: [f"0x{x:08X}" for x in before_left],
                            right: [f"0x{x:08X}" for x in before_right],
                        },
                        "after": {
                            left: [f"0x{x:08X}" for x in new_left],
                            right: [f"0x{x:08X}" for x in new_right],
                        },
                        "compatible_pair_count": len(pairs),
                        "witnesses": witnesses,
                    }
                )
        if not changed:
            break

    # Re-evaluate hard constraints at the fixed point. A stale contradiction that
    # was observed before another edge pruned a domain must not poison the result.
    final_contradictions: list[dict] = []
    for rel in hard_rels:
        left, right, pairs, _ = hard_pairs(mm, pe, native_map, domains, rel, calls)
        if domains.get(left) and domains.get(right) and not pairs:
            final_contradictions.append(
                {
                    "relationship": rel["id"],
                    "type": rel["type"],
                    "left": left,
                    "right": right,
                    "status": "NO_COMPATIBLE_PAIR_AT_FIXPOINT",
                }
            )

    support_relations: dict[str, list[str]] = {name: [] for name in domains}
    for rel in hard_rels:
        left, right, pairs, _ = hard_pairs(mm, pe, native_map, domains, rel, calls)
        if not pairs:
            continue
        if len(domains.get(left, [])) == 1 and len(domains.get(right, [])) == 1:
            pair = (domains[left][0], domains[right][0])
            if pair in pairs:
                if rel["id"] not in support_relations[left]:
                    support_relations[left].append(rel["id"])
                if rel["id"] not in support_relations[right]:
                    support_relations[right].append(rel["id"])

    advisory = []
    for rel in native_map.get("relationships", []):
        if relationship_strength(rel) != "advisory":
            continue
        if rel.get("type") == "regional_shift":
            advisory.append(regional_advisory(native_map, domains, rel))
        else:
            advisory.append(
                {
                    "id": rel["id"],
                    "type": rel.get("type"),
                    "strength": "advisory",
                    "status": "UNSUPPORTED_ADVISORY",
                }
            )

    nodes = {}
    for name, values in domains.items():
        nodes[name] = {
            "initial_candidate_count": initial_counts[name],
            "final_candidate_count": len(values),
            "candidates": [f"0x{x:08X}" for x in values],
            "resolved_rva": f"0x{values[0]:08X}" if len(values) == 1 else None,
            "proof_relations": proof_relations[name],
            "support_relations": support_relations[name],
        }
    return {
        "engine": "ANCHOR_GRAPH_V2",
        "consistent": not final_contradictions,
        "nodes": nodes,
        "hard_edge_audit": audit,
        "contradictions": final_contradictions,
        "advisory": advisory,
    }
