#!/usr/bin/env python3
"""Normalized + structural relocation for BSC's WH3 native map.

Pipeline stages implemented here:
4. explicit relocation-dependent byte masks for codegen drift;
5. Windows x64 .pdata runtime-function fingerprints;
6. anchor relationships/callgraph scoring and Move/Attack dataflow proof.

All output is a CANDIDATE only. Runtime Native remains static/fail-closed and
must not consume a candidate map until source/build/runtime validation passes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mmap
from pathlib import Path
from typing import Any

from pe_tools import (
    PE,
    compile_mask,
    direct_rel32_targets,
    exact_occurrences,
    function_fingerprint,
    masked_occurrences,
    parse_rva,
    rip_target,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "native_maps" / "wh3_9.0.1_6c104a63.json"
DEFAULT_REPORT_ROOT = ROOT / "reports" / "wh3_updates"


def load_map(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("unsupported native map schema")
    if len(data.get("core", {})) != 16:
        raise ValueError("canonical map must contain exactly 16 mandatory core sites")
    return data


def hexrva(value: int | None) -> str | None:
    return None if value is None else f"0x{value:08X}"


def candidate_inventory(mm: Any, pe: PE, native_map: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for group_name in ("core", "optional"):
        required = group_name == "core"
        for name, spec in native_map.get(group_name, {}).items():
            guard = bytes.fromhex(spec["guard"])
            exact = exact_occurrences(mm, pe, guard)
            mode = "EXACT"
            hits = exact
            if not hits and spec.get("normalization"):
                ranges = spec["normalization"].get("mask_ranges", [])
                mask = compile_mask(len(guard), ranges)
                hits = masked_occurrences(mm, pe, guard, mask)
                mode = "NORMALIZED"
            out[name] = {
                "name": name,
                "group": group_name,
                "required": required,
                "old_rva": parse_rva(spec["rva"]),
                "mode": mode,
                "candidates": sorted(set(hits)),
                "scores": {},
                "proofs": {},
                "resolved": None,
                "resolution": None,
            }
            if len(hits) == 1:
                out[name]["resolved"] = hits[0]
                out[name]["resolution"] = "EXACT_UNIQUE" if mode == "EXACT" else "NORMALIZED_UNIQUE"
    return out


def calls_to(mm: Any, pe: PE, caller_rva: int, target_rva: int) -> list[int]:
    function = pe.runtime_function(caller_rva)
    if function is None:
        return []
    return [
        row["call_rva"]
        for row in direct_rel32_targets(mm, pe, function)
        if row["target_rva"] == target_rva
    ]


def add_score(row: dict, candidate: int, weight: int, proof: dict) -> None:
    row["scores"][candidate] = row["scores"].get(candidate, 0) + int(weight)
    row["proofs"].setdefault(candidate, []).append(proof)


def score_relationships(mm: Any, pe: PE, native_map: dict, inv: dict[str, dict]) -> None:
    for rel in native_map.get("relationships", []):
        kind = rel.get("type")
        weight = int(rel.get("weight", 1))
        rid = rel.get("id", kind)

        if kind == "rva_delta":
            left, right = inv[rel["left"]], inv[rel["right"]]
            expected = int(rel["expected_delta"])
            tolerance = int(rel.get("tolerance", 0))
            if right["resolved"] is not None and left["resolved"] is None:
                rr = int(right["resolved"])
                for cand in left["candidates"]:
                    actual = cand - rr
                    if abs(actual - expected) <= tolerance:
                        add_score(left, cand, weight, {
                            "relationship": rid,
                            "type": kind,
                            "actual_delta": actual,
                            "expected_delta": expected,
                        })
            if left["resolved"] is not None and right["resolved"] is None:
                lr = int(left["resolved"])
                for cand in right["candidates"]:
                    actual = lr - cand
                    if abs(actual - expected) <= tolerance:
                        add_score(right, cand, weight, {
                            "relationship": rid,
                            "type": kind,
                            "actual_delta": actual,
                            "expected_delta": expected,
                        })

        elif kind == "calls":
            caller, callee = inv[rel["caller"]], inv[rel["callee"]]
            if caller["resolved"] is not None and callee["resolved"] is None:
                cr = int(caller["resolved"])
                for cand in callee["candidates"]:
                    callsites = calls_to(mm, pe, cr, cand)
                    if callsites:
                        add_score(callee, cand, weight, {
                            "relationship": rid,
                            "type": kind,
                            "caller": hexrva(cr),
                            "callsites": [hexrva(x) for x in callsites],
                        })
            if callee["resolved"] is not None and caller["resolved"] is None:
                tr = int(callee["resolved"])
                for cand in caller["candidates"]:
                    callsites = calls_to(mm, pe, cand, tr)
                    if callsites:
                        add_score(caller, cand, weight, {
                            "relationship": rid,
                            "type": kind,
                            "callee": hexrva(tr),
                            "callsites": [hexrva(x) for x in callsites],
                        })

        elif kind == "rip_target_delta":
            left, right = inv[rel["left"]], inv[rel["right"]]
            lspec = native_map[left["group"]][left["name"]].get("normalization", {})
            rspec = native_map[right["group"]][right["name"]].get("normalization", {})
            lip = lspec.get("rip_target")
            rip = rspec.get("rip_target")
            if not lip or not rip:
                continue
            expected = int(rel["expected_delta"])
            tolerance = int(rel.get("tolerance", 0))
            lcands = [left["resolved"]] if left["resolved"] is not None else left["candidates"]
            rcands = [right["resolved"]] if right["resolved"] is not None else right["candidates"]
            for lc in lcands:
                lt = rip_target(mm, pe, int(lc), int(lip["disp_offset"]), int(lip["instruction_end_offset"]))
                if lt is None:
                    continue
                for rc in rcands:
                    rt = rip_target(mm, pe, int(rc), int(rip["disp_offset"]), int(rip["instruction_end_offset"]))
                    if rt is None:
                        continue
                    actual = lt - rt
                    if abs(actual - expected) <= tolerance:
                        if left["resolved"] is None:
                            add_score(left, int(lc), weight, {
                                "relationship": rid,
                                "type": kind,
                                "actual_delta": actual,
                                "peer": hexrva(int(rc)),
                            })
                        if right["resolved"] is None:
                            add_score(right, int(rc), weight, {
                                "relationship": rid,
                                "type": kind,
                                "actual_delta": actual,
                                "peer": hexrva(int(lc)),
                            })


def promote_unique_scores(inv: dict[str, dict]) -> bool:
    changed = False
    for row in inv.values():
        if row["resolved"] is not None or not row["candidates"] or not row["scores"]:
            continue
        ranked = sorted(
            ((row["scores"].get(c, 0), c) for c in row["candidates"]),
            reverse=True,
        )
        top_score, top = ranked[0]
        second_score = ranked[1][0] if len(ranked) > 1 else -1
        if top_score > 0 and top_score > second_score:
            row["resolved"] = top
            row["resolution"] = "STRUCTURAL_RELATIONSHIP"
            changed = True
    return changed


def resolve_iteratively(mm: Any, pe: PE, native_map: dict, inv: dict[str, dict]) -> None:
    for _ in range(12):
        score_relationships(mm, pe, native_map, inv)
        if not promote_unique_scores(inv):
            break


def validate_resolved_relationships(mm: Any, pe: PE, native_map: dict, inv: dict[str, dict]) -> list[dict]:
    checks: list[dict] = []
    for rel in native_map.get("relationships", []):
        kind = rel.get("type")
        rid = rel.get("id", kind)
        if kind == "rva_delta":
            l, r = inv[rel["left"]], inv[rel["right"]]
            if l["resolved"] is None or r["resolved"] is None:
                continue
            actual = int(l["resolved"]) - int(r["resolved"])
            expected = int(rel["expected_delta"])
            tolerance = int(rel.get("tolerance", 0))
            checks.append({
                "id": rid,
                "type": kind,
                "pass": abs(actual - expected) <= tolerance,
                "actual_delta": actual,
                "expected_delta": expected,
                "tolerance": tolerance,
            })
        elif kind == "calls":
            caller, callee = inv[rel["caller"]], inv[rel["callee"]]
            if caller["resolved"] is None or callee["resolved"] is None:
                continue
            callsites = calls_to(mm, pe, int(caller["resolved"]), int(callee["resolved"]))
            checks.append({
                "id": rid,
                "type": kind,
                "pass": bool(callsites),
                "caller": hexrva(int(caller["resolved"])),
                "callee": hexrva(int(callee["resolved"])),
                "callsites": [hexrva(x) for x in callsites],
            })
        elif kind == "rip_target_delta":
            l, r = inv[rel["left"]], inv[rel["right"]]
            if l["resolved"] is None or r["resolved"] is None:
                continue
            lspec = native_map[l["group"]][l["name"]]["normalization"]["rip_target"]
            rspec = native_map[r["group"]][r["name"]]["normalization"]["rip_target"]
            lt = rip_target(mm, pe, int(l["resolved"]), int(lspec["disp_offset"]), int(lspec["instruction_end_offset"]))
            rt = rip_target(mm, pe, int(r["resolved"]), int(rspec["disp_offset"]), int(rspec["instruction_end_offset"]))
            if lt is None or rt is None:
                continue
            actual = lt - rt
            expected = int(rel["expected_delta"])
            tolerance = int(rel.get("tolerance", 0))
            checks.append({
                "id": rid,
                "type": kind,
                "pass": abs(actual - expected) <= tolerance,
                "left_target": hexrva(lt),
                "right_target": hexrva(rt),
                "actual_delta": actual,
                "expected_delta": expected,
            })
    return checks


def derive_order_dataflow(mm: Any, pe: PE, top_rva: int, allocator_rva: int) -> dict | None:
    function = pe.runtime_function(top_rva)
    if function is None:
        return None
    calls = sorted(direct_rel32_targets(mm, pe, function), key=lambda x: x["call_rva"])
    alloc_indexes = [i for i, row in enumerate(calls) if row["target_rva"] == allocator_rva]
    if len(alloc_indexes) != 1:
        return None
    i = alloc_indexes[0]
    following = [row for row in calls[i + 1 :] if row["call_rva"] - calls[i]["call_rva"] <= 0x80]
    if len(following) < 2:
        return None
    destructor = following[0]
    constructor = following[1]
    ctor_function = pe.runtime_function(constructor["target_rva"])
    if ctor_function is None:
        return None
    raw = pe.read_rva(ctor_function.begin, min(ctor_function.size, 0x100))
    if raw is None:
        return None

    vtable = None
    vtable_instruction = None
    for pos in range(0, max(0, len(raw) - 7)):
        if raw[pos : pos + 3] == b"\x48\x8d\x15":
            disp = int.from_bytes(raw[pos + 3 : pos + 7], "little", signed=True)
            vtable = ctor_function.begin + pos + 7 + disp
            vtable_instruction = ctor_function.begin + pos
            break

    ctor_calls = sorted(direct_rel32_targets(mm, pe, ctor_function), key=lambda x: x["call_rva"])
    return {
        "top_level": hexrva(top_rva),
        "allocator_call": hexrva(calls[i]["call_rva"]),
        "allocator": hexrva(allocator_rva),
        "destructor_call": hexrva(destructor["call_rva"]),
        "destructor": hexrva(destructor["target_rva"]),
        "constructor_call": hexrva(constructor["call_rva"]),
        "constructor": hexrva(constructor["target_rva"]),
        "constructor_function": {
            "begin": hexrva(ctor_function.begin),
            "end": hexrva(ctor_function.end),
            "size": ctor_function.size,
        },
        "base_constructor": hexrva(ctor_calls[0]["target_rva"]) if ctor_calls else None,
        "vtable_instruction": hexrva(vtable_instruction),
        "vtable": hexrva(vtable),
        "constructor_direct_calls_heuristic": [
            {"call": hexrva(x["call_rva"]), "target": hexrva(x["target_rva"])}
            for x in ctor_calls
        ],
    }


def serialize_inventory(mm: Any, pe: PE, inv: dict[str, dict]) -> list[dict]:
    rows = []
    for name, row in inv.items():
        resolved = row["resolved"]
        candidates = []
        for cand in row["candidates"]:
            candidates.append({
                "rva": hexrva(cand),
                "score": row["scores"].get(cand, 0),
                "proofs": row["proofs"].get(cand, []),
                "function": function_fingerprint(mm, pe, cand),
            })
        rows.append({
            "name": name,
            "group": row["group"],
            "required": row["required"],
            "old_rva": hexrva(row["old_rva"]),
            "mode": row["mode"],
            "resolution": row["resolution"],
            "resolved_rva": hexrva(resolved),
            "candidate_count": len(row["candidates"]),
            "candidates": candidates,
            "resolved_function": function_fingerprint(mm, pe, int(resolved)) if resolved is not None else None,
        })
    return rows


def build_candidate_map(mm: Any, pe: PE, native_map: dict, inv: dict[str, dict], actual_sha: str, dataflow: dict) -> dict:
    unresolved = [name for name, row in inv.items() if row["required"] and row["resolved"] is None]
    if unresolved:
        raise ValueError("mandatory sites unresolved: " + ", ".join(unresolved))

    out = copy.deepcopy(native_map)
    old_id = out.get("map_id", "UNKNOWN")
    out["map_id"] = f"CANDIDATE_STRUCTURAL_FROM_{old_id}_{actual_sha[:12]}"
    out["game"]["sha256"] = actual_sha
    out["game"]["version"] = "UNKNOWN_NEW_BUILD_REQUIRES_MAINTAINER_LABEL"
    out["candidate"] = {
        "stage": "NORMALIZED_PDATA_RELATIONSHIP_RELOCATION",
        "release_authorized": False,
        "proof_levels": {
            "exact_unique": "L1_BYTE_MATCH",
            "normalized_unique": "L2_NORMALIZED_MATCH",
            "structural_relationship": "L3_STRUCTURAL_MATCH",
            "order_dataflow": "L4_DATAFLOW_DERIVED",
            "runtime": "NOT_RUN",
        },
        "requires": [
            "maintainer static review",
            "generated-source contract update",
            "Windows build/tests",
            "WH3 runtime smoke",
        ],
    }

    for group_name in ("core", "optional"):
        for name, spec in out.get(group_name, {}).items():
            row = inv[name]
            if row["resolved"] is None:
                spec["relocation_status"] = "UNRESOLVED_STAGED_DISABLED"
                if group_name == "optional":
                    spec["runtime"] = "STAGED_DISABLED_UNRESOLVED"
                continue
            rva = int(row["resolved"])
            guard_len = len(bytes.fromhex(spec["guard"]))
            current = pe.read_rva(rva, guard_len)
            if current is None:
                raise ValueError(f"cannot read relocated guard for {name}")
            spec["rva"] = hexrva(rva)
            spec["guard"] = current.hex()
            spec["relocation_status"] = row["resolution"]

    move_df = dataflow.get("move") or {}
    attack_df = dataflow.get("attack") or {}
    if move_df.get("vtable"):
        out["derived"]["full_move_vtable"]["rva"] = move_df["vtable"]
        out["derived"]["full_move_vtable"]["proof"] = "L4_DATAFLOW_DERIVED_CANDIDATE"
    if attack_df.get("vtable"):
        out["derived"]["attack_vtable"]["rva"] = attack_df["vtable"]
        out["derived"]["attack_vtable"]["proof"] = "L4_DATAFLOW_DERIVED_CANDIDATE"
    if move_df.get("constructor"):
        out["derived"]["order_constructors"]["full_move"] = move_df["constructor"]
    if attack_df.get("constructor"):
        out["derived"]["order_constructors"]["attack"] = attack_df["constructor"]
    if move_df.get("base_constructor") and move_df.get("base_constructor") == attack_df.get("base_constructor"):
        out["derived"]["order_constructors"]["base"] = move_df["base_constructor"]

    out["source_of_truth"]["candidate_parent_map"] = native_map.get("map_id")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    args = parser.parse_args()

    native_map = load_map(args.map)
    with args.exe.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        pe = PE(mm)
        actual_sha = hashlib.sha256(mm).hexdigest()
        inv = candidate_inventory(mm, pe, native_map)
        resolve_iteratively(mm, pe, native_map, inv)
        relationship_checks = validate_resolved_relationships(mm, pe, native_map, inv)

        dataflow = {}
        if inv["allocator"]["resolved"] is not None:
            allocator = int(inv["allocator"]["resolved"])
            for name in ("move", "attack"):
                if inv[name]["resolved"] is not None:
                    dataflow[name] = derive_order_dataflow(mm, pe, int(inv[name]["resolved"]), allocator)

        rows = serialize_inventory(mm, pe, inv)
        unresolved_core = [
            row["name"] for row in rows if row["required"] and row["resolved_rva"] is None
        ]
        failed_relationships = [x for x in relationship_checks if not x["pass"]]
        classification = (
            "STRUCTURAL_RELOCATION_COMPLETE"
            if not unresolved_core and not failed_relationships
            else "MANUAL_REVIEW_REQUIRED"
        )
        report = {
            "schema": 1,
            "tool": "relocate_structural",
            "source_map": str(args.map),
            "exe": str(args.exe),
            "actual_sha256": actual_sha,
            "classification": classification,
            "runtime_function_count": len(pe.runtime_functions()),
            "sites": rows,
            "relationship_checks": relationship_checks,
            "order_dataflow": dataflow,
            "unresolved_core": unresolved_core,
            "failed_relationships": failed_relationships,
        }

        out_dir = args.report_root / actual_sha[:12]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "structural_relocation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        if not unresolved_core:
            candidate = build_candidate_map(mm, pe, native_map, inv, actual_sha, dataflow)
            (out_dir / "candidate_map_structural.json").write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    print(json.dumps({
        "classification": classification,
        "resolved_core": 16 - len(unresolved_core),
        "unresolved_core": unresolved_core,
        "failed_relationships": [x["id"] for x in failed_relationships],
        "report_dir": str(out_dir),
    }))
    if classification != "STRUCTURAL_RELOCATION_COMPLETE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
