#!/usr/bin/env python3
"""Stage-4 relocation: mask relocation-dependent x64 operand bytes.

The canonical map owns explicit mask ranges for guards whose rel32/RIP-relative
operands are expected to move between WH3 builds. A normalized match is evidence,
not release authorization; ambiguous matches are handed to Stage 5/6.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
from pathlib import Path

from pe_tools import PE, compile_mask, masked_occurrences, parse_rva, rip_target


def load_map(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("unsupported native map schema")
    return data


def inspect_group(mm: mmap.mmap, pe: PE, group: dict, required: bool) -> list[dict]:
    rows: list[dict] = []
    for name, spec in group.items():
        norm = spec.get("normalization")
        if not norm:
            continue
        if norm.get("kind") != "relocation_mask":
            raise ValueError(f"{name}: unsupported normalization kind")
        pattern = bytes.fromhex(spec["guard"])
        mask = compile_mask(len(pattern), norm.get("mask_ranges", []))
        matches = masked_occurrences(mm, pe, pattern, mask)
        old_rva = parse_rva(spec["rva"])
        row = {
            "name": name,
            "required": required,
            "old_rva": f"0x{old_rva:08X}",
            "mask_ranges": norm.get("mask_ranges", []),
            "match_count": len(matches),
            "matches": [f"0x{x:08X}" for x in matches],
            "status": (
                "NORMALIZED_UNIQUE"
                if len(matches) == 1
                else "NORMALIZED_NOT_FOUND"
                if not matches
                else "NORMALIZED_AMBIGUOUS"
            ),
        }
        rip = norm.get("rip_target")
        if rip:
            row["rip_targets"] = {
                f"0x{x:08X}": (
                    None
                    if (t := rip_target(
                        mm,
                        pe,
                        x,
                        int(rip["disp_offset"]),
                        int(rip["instruction_end_offset"]),
                    ))
                    is None
                    else f"0x{t:08X}"
                )
                for x in matches
            }
        rows.append(row)
    return rows


def run(exe: Path, map_path: Path) -> dict:
    native_map = load_map(map_path)
    with exe.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        pe = PE(mm)
        return {
            "schema": 1,
            "tool": "relocate_normalized",
            "source_map": str(map_path),
            "exe": str(exe),
            "actual_sha256": hashlib.sha256(mm).hexdigest(),
            "core": inspect_group(mm, pe, native_map["core"], True),
            "optional": inspect_group(mm, pe, native_map.get("optional", {}), False),
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
        row["name"]: {"status": row["status"], "matches": row["matches"]}
        for row in report["core"]
    }))


if __name__ == "__main__":
    main()
