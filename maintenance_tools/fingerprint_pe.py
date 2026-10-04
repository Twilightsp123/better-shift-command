#!/usr/bin/env python3
"""Stage-5 WH3 .pdata/runtime-function fingerprint inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
from pathlib import Path

from pe_tools import PE, function_fingerprint, parse_rva


def load_map(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("unsupported native map schema")
    return data


def run(exe: Path, map_path: Path) -> dict:
    native_map = load_map(map_path)
    with exe.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        pe = PE(mm)
        def group(rows: dict) -> dict:
            out = {}
            for name, spec in rows.items():
                rva = parse_rva(spec["rva"])
                out[name] = {
                    "site_rva": f"0x{rva:08X}",
                    "fingerprint": function_fingerprint(mm, pe, rva),
                }
            return out
        return {
            "schema": 1,
            "tool": "fingerprint_pe",
            "actual_sha256": hashlib.sha256(mm).hexdigest(),
            "runtime_function_count": len(pe.runtime_functions()),
            "core": group(native_map["core"]),
            "optional": group(native_map.get("optional", {})),
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
    compact = {}
    for name, row in report["core"].items():
        fp = row["fingerprint"]
        compact[name] = None if fp is None else {
            "begin": fp["begin"], "size": fp["size"], "site_offset": fp["site_offset"]
        }
    print(json.dumps(compact))


if __name__ == "__main__":
    main()
