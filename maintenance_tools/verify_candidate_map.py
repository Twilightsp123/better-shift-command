#!/usr/bin/env python3
"""Static candidate-map verifier against the matching WH3 executable."""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
from pathlib import Path

from pe_tools import PE, direct_rel32_targets, parse_rva


def first_vtable_target(pe: PE, rva: int) -> int | None:
    fn = pe.runtime_function(rva)
    if fn is None:
        return None
    raw = pe.read_rva(fn.begin, min(fn.size, 0x100))
    if raw is None:
        return None
    for i in range(max(0, len(raw) - 7)):
        if raw[i:i + 3] == b"\x48\x8d\x15":
            disp = int.from_bytes(raw[i + 3:i + 7], "little", signed=True)
            return fn.begin + i + 7 + disp
    return None


def direct_calls(pe: PE, mm: mmap.mmap, rva: int) -> list[dict[str, int]]:
    fn = pe.runtime_function(rva)
    if fn is None:
        return []
    return sorted(direct_rel32_targets(mm, pe, fn), key=lambda row: row["call_rva"])


def verify(exe: Path, native_map: dict) -> dict:
    if native_map.get("schema") != 1:
        raise ValueError("schema != 1")
    if len(native_map.get("core", {})) != 16:
        raise ValueError("core count != 16")
    if set(native_map.get("optional", {})) != {"contact_pair", "smart_guard"}:
        raise ValueError("optional site set")
    if native_map.get("candidate", {}).get("release_authorized") is not False:
        raise ValueError("candidate must remain release_authorized=false")
    if native_map.get("policy", {}).get("optional_sites_are_release_gates") is not False:
        raise ValueError("optional sites became release gates")

    with exe.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        pe = PE(mm)
        sha = hashlib.sha256(mm).hexdigest()
        if sha.lower() != native_map["game"]["sha256"].lower():
            raise ValueError(
                f"SHA mismatch actual={sha} expected={native_map['game']['sha256']}"
            )

        checked = []
        for group_name in ("core", "optional"):
            for name, spec in native_map[group_name].items():
                rva = parse_rva(spec["rva"])
                expected = bytes.fromhex(spec["guard"])
                actual = pe.read_rva(rva, len(expected))
                if actual != expected:
                    raise ValueError(
                        f"{group_name}.{name} guard mismatch @0x{rva:08X}"
                    )
                checked.append(f"{group_name}.{name}")

        derived = native_map["derived"]
        ctors = derived["order_constructors"]
        base = parse_rva(ctors["base"])
        ctor_rows = [
            ("full_move", parse_rva(ctors["full_move"]), parse_rva(derived["full_move_vtable"]["rva"])),
            ("attack", parse_rva(ctors["attack"]), parse_rva(derived["attack_vtable"]["rva"])),
            (
                "simple_intercept_move",
                parse_rva(ctors["simple_intercept_move"]),
                parse_rva(derived["simple_intercept_move_vtable"]["rva"]),
            ),
        ]
        for name, ctor, vtable in ctor_rows:
            targets = {row["target_rva"] for row in direct_calls(pe, mm, ctor)}
            if base not in targets:
                raise ValueError(f"{name} constructor does not call base constructor")
            if first_vtable_target(pe, ctor) != vtable:
                raise ValueError(f"{name} VTable install mismatch")

        allocator = parse_rva(native_map["core"]["allocator"]["rva"])
        for top_name, ctor_key in (("move", "full_move"), ("attack", "attack")):
            top = parse_rva(native_map["core"][top_name]["rva"])
            ctor = parse_rva(ctors[ctor_key])
            calls = direct_calls(pe, mm, top)
            allocator_calls = [row for row in calls if row["target_rva"] == allocator]
            if not allocator_calls:
                raise ValueError(f"{top_name} top-level does not call mapped allocator")
            if not any(
                alloc["call_rva"] < call["call_rva"] <= alloc["call_rva"] + 0x80
                and call["target_rva"] == ctor
                for alloc in allocator_calls
                for call in calls
            ):
                raise ValueError(f"{top_name} constructor not observed after allocator")

        full_move = parse_rva(derived["full_move_vtable"]["rva"])
        simple_move = parse_rva(derived["simple_intercept_move_vtable"]["rva"])
        if full_move == simple_move:
            raise ValueError("Full Move and Simple/Intercept VTables collapsed")
        if derived["simple_intercept_move_vtable"].get("release_use") is not False:
            raise ValueError("Simple/Intercept release_use must remain false")

        return {
            "schema": 1,
            "tool": "verify_candidate_map",
            "sha256": sha,
            "core_guards": "16/16",
            "optional_guards": "2/2",
            "constructors": "3/3",
            "vtable_relationships": "3/3",
            "top_level_order_dataflow": "2/2",
            "release_authorized": False,
            "checked_sites": checked,
        }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", required=True, type=Path)
    ap.add_argument("--map", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    native_map = json.loads(args.map.read_text(encoding="utf-8"))
    report = verify(args.exe, native_map)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS")
    print("sha=" + report["sha256"])
    print("core=" + report["core_guards"])
    print("optional=" + report["optional_guards"])
    print("constructors=" + report["constructors"])
    print("vtable_relationships=" + report["vtable_relationships"])
    print("top_level_order_dataflow=" + report["top_level_order_dataflow"])
    print("release_authorized=false")


if __name__ == "__main__":
    main()
