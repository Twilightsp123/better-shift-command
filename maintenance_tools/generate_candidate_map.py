#!/usr/bin/env python3
"""Generate a fail-closed WH3 candidate map after Stages 2-6 resolve core sites.

The generated map is maintenance evidence only. It updates guards to bytes from
the new EXE, records .pdata fingerprints, and re-derives Move/Attack
constructor/VTable identity from current top-level call flow.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mmap
from pathlib import Path

from pe_tools import PE, direct_rel32_targets, exact_occurrences, function_fingerprint, parse_rva
from resolve_relations import load_map, run as resolve_run


def ctor_vtable(mm: mmap.mmap, pe: PE, ctor_rva: int) -> int | None:
    raw = pe.read_rva(ctor_rva, 96)
    if raw is None:
        return None
    for i in range(0, len(raw) - 10):
        if raw[i : i + 3] != b"\x48\x8d\x15":
            continue
        disp = int.from_bytes(raw[i + 3 : i + 7], "little", signed=True)
        target = ctor_rva + i + 7 + disp
        tail = raw[i + 7 : i + 14]
        if b"\x48\x89\x17" in tail or b"\x48\x89\x13" in tail:
            return target
    return None


def ctor_base_call(mm: mmap.mmap, pe: PE, ctor_rva: int) -> int | None:
    fn = pe.runtime_function(ctor_rva)
    if fn is None:
        return None
    calls = sorted(direct_rel32_targets(mm, pe, fn), key=lambda x: x["call_rva"])
    return calls[0]["target_rva"] if calls else None


def constructor_after_allocator(
    mm: mmap.mmap,
    pe: PE,
    top_rva: int,
    allocator_rva: int,
) -> int | None:
    fn = pe.runtime_function(top_rva)
    if fn is None:
        return None
    calls = sorted(direct_rel32_targets(mm, pe, fn), key=lambda x: x["call_rva"])
    allocator_calls = [x for x in calls if x["target_rva"] == allocator_rva]
    if not allocator_calls:
        return None
    for alloc in allocator_calls:
        for row in calls:
            if not (alloc["call_rva"] < row["call_rva"] <= alloc["call_rva"] + 96):
                continue
            if ctor_vtable(mm, pe, row["target_rva"]) is not None:
                return row["target_rva"]
    return None


def derive_order_identity(mm: mmap.mmap, pe: PE, native_map: dict, resolved: dict[str, int]) -> dict:
    allocator = resolved["allocator"]
    move_ctor = constructor_after_allocator(mm, pe, resolved["move"], allocator)
    attack_ctor = constructor_after_allocator(mm, pe, resolved["attack"], allocator)
    if move_ctor is None or attack_ctor is None:
        raise ValueError("could not derive Move/Attack constructor after allocator")

    move_vt = ctor_vtable(mm, pe, move_ctor)
    attack_vt = ctor_vtable(mm, pe, attack_ctor)
    move_base = ctor_base_call(mm, pe, move_ctor)
    attack_base = ctor_base_call(mm, pe, attack_ctor)
    if move_vt is None or attack_vt is None or move_base is None or attack_base is None:
        raise ValueError("constructor dataflow incomplete")
    if move_base != attack_base:
        raise ValueError("Move/Attack constructors do not share the same base constructor")

    old_ctors = native_map.get("derived", {}).get("order_constructors", {})
    old_full = parse_rva(old_ctors["full_move"])
    old_simple = parse_rva(old_ctors["simple_intercept_move"])
    sibling_delta = old_full - old_simple
    simple_ctor = move_ctor - sibling_delta
    simple_vt = None
    simple_base = ctor_base_call(mm, pe, simple_ctor)
    if simple_base == move_base:
        simple_vt = ctor_vtable(mm, pe, simple_ctor)

    return {
        "base_constructor": f"0x{move_base:08X}",
        "full_move_constructor": f"0x{move_ctor:08X}",
        "attack_constructor": f"0x{attack_ctor:08X}",
        "full_move_vtable": f"0x{move_vt:08X}",
        "attack_vtable": f"0x{attack_vt:08X}",
        "simple_intercept_move_constructor": (
            f"0x{simple_ctor:08X}" if simple_vt is not None else None
        ),
        "simple_intercept_move_vtable": (
            f"0x{simple_vt:08X}" if simple_vt is not None else None
        ),
        "proof": "ALLOCATOR_TO_CONSTRUCTOR_TO_VTABLE_STATIC_DATAFLOW",
    }


def generate(exe: Path, map_path: Path, game_version: str) -> dict:
    source = load_map(map_path)
    relation_report = resolve_run(exe, map_path)
    if not relation_report["all_core_resolved"]:
        raise ValueError("mandatory core sites are not fully resolved")

    resolved = {
        name: parse_rva(row["resolved_rva"])
        for name, row in relation_report["core"].items()
    }

    with exe.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        pe = PE(mm)
        actual_sha = hashlib.sha256(mm).hexdigest()
        out = copy.deepcopy(source)
        out["map_id"] = f"WH3_{game_version}_{actual_sha[:8]}_CANDIDATE"
        out["game"]["version"] = game_version
        out["game"]["sha256"] = actual_sha
        out["candidate"] = {
            "status": "STATIC_RELOCATION_CANDIDATE",
            "release_authorized": False,
            "source_map_id": source["map_id"],
            "source_sha256": source["game"]["sha256"],
            "required_next_gates": [
                "source/runtime map generation",
                "prebuild contract",
                "Windows native build and CTest",
                "WH3 native smoke",
            ],
        }

        fingerprints = {}
        for name, new_rva in resolved.items():
            spec = out["core"][name]
            old_guard_len = len(bytes.fromhex(spec["guard"]))
            actual = pe.read_rva(new_rva, old_guard_len)
            if actual is None:
                raise ValueError(f"{name}: cannot read new guard")
            spec["rva"] = f"0x{new_rva:08X}"
            spec["guard"] = actual.hex()
            spec["relocation"] = {
                "method": relation_report["core"][name]["method"],
                "source_rva": relation_report["core"][name]["old_rva"],
                "relationship_resolved": True,
            }
            fingerprints[name] = function_fingerprint(mm, pe, new_rva)

        for name, spec in out.get("optional", {}).items():
            pattern = bytes.fromhex(spec["guard"])
            matches = exact_occurrences(mm, pe, pattern)
            if len(matches) == 1:
                new_rva = matches[0]
                actual = pe.read_rva(new_rva, len(pattern))
                spec["rva"] = f"0x{new_rva:08X}"
                spec["guard"] = actual.hex() if actual else spec["guard"]
                spec["relocation_status"] = "EXACT_UNIQUE_RELOCATED"
            else:
                spec["relocation_status"] = (
                    "EXACT_NOT_FOUND" if not matches else "EXACT_AMBIGUOUS"
                )
                spec["runtime"] = "STAGED_DISABLED_UNRESOLVED"

        identity = derive_order_identity(mm, pe, source, resolved)
        out["derived"]["order_constructors"] = {
            "base": identity["base_constructor"],
            "full_move": identity["full_move_constructor"],
            "simple_intercept_move": identity["simple_intercept_move_constructor"],
            "attack": identity["attack_constructor"],
        }
        out["derived"]["full_move_vtable"]["rva"] = identity["full_move_vtable"]
        out["derived"]["full_move_vtable"]["proof"] = "LEVEL-1_STATIC_DATAFLOW_CANDIDATE"
        out["derived"]["attack_vtable"]["rva"] = identity["attack_vtable"]
        out["derived"]["attack_vtable"]["proof"] = "LEVEL-1_STATIC_DATAFLOW_CANDIDATE"
        if identity["simple_intercept_move_vtable"] is not None:
            out["derived"]["simple_intercept_move_vtable"]["rva"] = identity[
                "simple_intercept_move_vtable"
            ]
            out["derived"]["simple_intercept_move_vtable"][
                "proof"
            ] = "SIBLING_CONSTRUCTOR_STATIC_CANDIDATE"

        out["candidate"]["order_identity"] = identity
        out["candidate"]["function_fingerprints"] = fingerprints
        out["candidate"]["relationship_audit"] = relation_report["relationship_audit"]
        return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", required=True, type=Path)
    ap.add_argument("--map", required=True, type=Path)
    ap.add_argument("--game-version", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    result = generate(args.exe, args.map, args.game_version)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "map_id": result["map_id"],
        "sha256": result["game"]["sha256"],
        "core": len(result["core"]),
        "release_authorized": result["candidate"]["release_authorized"],
        "order_identity": result["candidate"]["order_identity"],
    }))


if __name__ == "__main__":
    main()
