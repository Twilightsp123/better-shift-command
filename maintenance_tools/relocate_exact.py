#!/usr/bin/env python3
"""Exact byte relocation for Better Shift Command WH3 native maps.

Phase 2 of the address-maintenance pipeline:
- verifies the old RVA first;
- scans executable PE sections for the exact guard bytes when an RVA moved;
- treats optional sites as non-blocking;
- can emit an exact-relocated candidate map only when every mandatory core site
  is resolved without ambiguity.

This tool never modifies the EXE and never enables runtime hooks.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mmap
import struct
from pathlib import Path
from typing import Any, Iterable

IMAGE_SCN_MEM_EXECUTE = 0x20000000


class PE:
    def __init__(self, data: Any):
        self.data = data

        def need(offset: int, size: int) -> None:
            if offset < 0 or size < 0 or offset + size > len(data):
                raise ValueError("truncated PE")

        need(0, 64)
        if data[:2] != b"MZ":
            raise ValueError("not MZ")
        pe_off = struct.unpack_from("<I", data, 0x3C)[0]
        need(pe_off, 24)
        if data[pe_off : pe_off + 4] != b"PE\0\0":
            raise ValueError("not PE")

        machine, section_count, timestamp, _, _, opt_size, _ = struct.unpack_from(
            "<HHIIIHH", data, pe_off + 4
        )
        if machine != 0x8664:
            raise ValueError("requires x64 PE")
        if not 1 <= section_count <= 96:
            raise ValueError("invalid PE section count")

        opt = pe_off + 24
        need(opt, opt_size)
        if opt_size < 112 or struct.unpack_from("<H", data, opt)[0] != 0x20B:
            raise ValueError("requires PE32+")

        self.timestamp = timestamp
        self.image_base = struct.unpack_from("<Q", data, opt + 24)[0]
        self.image_size = struct.unpack_from("<I", data, opt + 56)[0]
        self.headers_size = struct.unpack_from("<I", data, opt + 60)[0]
        self.sections: list[dict[str, int | str]] = []

        need(opt + opt_size, section_count * 40)
        for i in range(section_count):
            off = opt + opt_size + i * 40
            name = data[off : off + 8].split(b"\0")[0].decode("ascii", "replace")
            virtual_size, rva, raw_size, raw_offset = struct.unpack_from("<IIII", data, off + 8)
            flags = struct.unpack_from("<I", data, off + 36)[0]
            if raw_size:
                need(raw_offset, raw_size)
            self.sections.append(
                {
                    "name": name,
                    "rva": rva,
                    "virtual_size": virtual_size,
                    "raw_size": raw_size,
                    "raw_offset": raw_offset,
                    "flags": flags,
                }
            )

    def rva_to_file(self, rva: int, size: int = 1) -> int | None:
        if 0 <= rva and rva + size <= min(self.headers_size, len(self.data)):
            return rva
        for section in self.sections:
            srva = int(section["rva"])
            raw_size = int(section["raw_size"])
            raw_offset = int(section["raw_offset"])
            if srva <= rva and rva + size <= srva + raw_size:
                return raw_offset + rva - srva
        return None

    def file_to_rva(self, file_offset: int) -> int | None:
        if 0 <= file_offset < min(self.headers_size, len(self.data)):
            return file_offset
        for section in self.sections:
            raw_offset = int(section["raw_offset"])
            raw_size = int(section["raw_size"])
            if raw_offset <= file_offset < raw_offset + raw_size:
                return int(section["rva"]) + file_offset - raw_offset
        return None

    def executable_ranges(self) -> Iterable[tuple[int, int, str]]:
        for section in self.sections:
            if int(section["flags"]) & IMAGE_SCN_MEM_EXECUTE:
                start = int(section["raw_offset"])
                end = start + int(section["raw_size"])
                if end > start:
                    yield start, end, str(section["name"])


def parse_rva(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return int(value, 0)


def load_map(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("unsupported native map schema")
    core = data.get("core")
    optional = data.get("optional")
    if not isinstance(core, dict) or len(core) != 16:
        raise ValueError(f"expected 16 mandatory core sites, got {0 if not isinstance(core, dict) else len(core)}")
    if not isinstance(optional, dict):
        raise ValueError("optional site table missing")
    for group_name, group in (("core", core), ("optional", optional)):
        for name, spec in group.items():
            if "rva" not in spec or "guard" not in spec:
                raise ValueError(f"{group_name}.{name}: missing rva/guard")
            guard = bytes.fromhex(spec["guard"])
            if not guard:
                raise ValueError(f"{group_name}.{name}: empty guard")
    return data


def sha256_mmap(mm: mmap.mmap) -> str:
    return hashlib.sha256(mm).hexdigest()


def exact_occurrences(mm: mmap.mmap, pe: PE, needle: bytes, cap: int = 32) -> list[dict]:
    found: list[dict] = []
    for start, end, section_name in pe.executable_ranges():
        pos = start
        while len(found) < cap:
            hit = mm.find(needle, pos, end)
            if hit < 0:
                break
            rva = pe.file_to_rva(hit)
            if rva is not None:
                found.append(
                    {
                        "rva": f"0x{rva:08X}",
                        "file_offset": f"0x{hit:X}",
                        "section": section_name,
                    }
                )
            pos = hit + 1
        if len(found) >= cap:
            break
    return found


def inspect_site(mm: mmap.mmap, pe: PE, name: str, spec: dict, required: bool) -> dict:
    old_rva = parse_rva(spec["rva"])
    guard = bytes.fromhex(spec["guard"])
    old_off = pe.rva_to_file(old_rva, len(guard))
    old_match = old_off is not None and bytes(mm[old_off : old_off + len(guard)]) == guard

    matches = exact_occurrences(mm, pe, guard)

    if old_match:
        status = "SAME_RVA"
        resolved_rva = old_rva
    elif len(matches) == 1:
        status = "EXACT_UNIQUE_RELOCATED"
        resolved_rva = parse_rva(matches[0]["rva"])
    elif len(matches) == 0:
        status = "EXACT_NOT_FOUND"
        resolved_rva = None
    else:
        status = "EXACT_AMBIGUOUS"
        resolved_rva = None

    return {
        "name": name,
        "required": required,
        "role": spec.get("role"),
        "old_rva": f"0x{old_rva:08X}",
        "guard_bytes": len(guard),
        "old_rva_match": old_match,
        "status": status,
        "resolved_rva": None if resolved_rva is None else f"0x{resolved_rva:08X}",
        "matches": matches,
    }


def classify(expected_sha: str, actual_sha: str, core_rows: list[dict]) -> str:
    statuses = [row["status"] for row in core_rows]
    all_same = all(s == "SAME_RVA" for s in statuses)
    all_resolved = all(s in {"SAME_RVA", "EXACT_UNIQUE_RELOCATED"} for s in statuses)

    if actual_sha == expected_sha and all_same:
        return "CURRENT_BUILD_EXACT"
    if actual_sha != expected_sha and all_same:
        return "HASH_ONLY"
    if all_resolved and any(s == "EXACT_UNIQUE_RELOCATED" for s in statuses):
        return "RVA_ONLY"
    if any(s == "EXACT_AMBIGUOUS" for s in statuses):
        return "PARTIAL_EXACT_AMBIGUOUS"
    return "CODEGEN_OR_SEMANTIC_DRIFT"


def candidate_map(source: dict, actual_sha: str, rows: list[dict], optional_rows: list[dict]) -> dict:
    unresolved = [
        row["name"]
        for row in rows
        if row["status"] not in {"SAME_RVA", "EXACT_UNIQUE_RELOCATED"}
    ]
    if unresolved:
        raise ValueError("cannot emit candidate map; unresolved mandatory sites: " + ", ".join(unresolved))

    out = copy.deepcopy(source)
    old_id = out.get("map_id", "UNKNOWN")
    out["map_id"] = f"CANDIDATE_FROM_{old_id}_{actual_sha[:12]}"
    out["game"]["sha256"] = actual_sha
    out["candidate"] = {
        "stage": "EXACT_RELOCATION_ONLY",
        "release_authorized": False,
        "requires": [
            "normalized/structural review when applicable",
            "static contract validation",
            "Windows build/tests",
            "WH3 runtime smoke",
        ],
    }
    for row in rows:
        out["core"][row["name"]]["rva"] = row["resolved_rva"]

    for row in optional_rows:
        if row["status"] in {"SAME_RVA", "EXACT_UNIQUE_RELOCATED"}:
            out["optional"][row["name"]]["rva"] = row["resolved_rva"]
            out["optional"][row["name"]]["relocation_status"] = row["status"]
        else:
            out["optional"][row["name"]]["relocation_status"] = row["status"]
            out["optional"][row["name"]]["runtime"] = "STAGED_DISABLED_UNRESOLVED"

    return out


def run(exe: Path, map_path: Path) -> dict:
    native_map = load_map(map_path)
    expected_sha = native_map["game"]["sha256"].lower()

    if not exe.is_file() or exe.stat().st_size == 0:
        raise ValueError("EXE missing or empty")

    with exe.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        pe = PE(mm)
        actual_sha = sha256_mmap(mm)
        core_rows = [
            inspect_site(mm, pe, name, spec, True)
            for name, spec in native_map["core"].items()
        ]
        optional_rows = [
            inspect_site(mm, pe, name, spec, False)
            for name, spec in native_map["optional"].items()
        ]

    classification = classify(expected_sha, actual_sha, core_rows)
    return {
        "schema": 1,
        "tool": "relocate_exact",
        "source_map": str(map_path),
        "exe": str(exe),
        "expected_sha256": expected_sha,
        "actual_sha256": actual_sha,
        "sha_match": expected_sha == actual_sha,
        "pe_timestamp": f"0x{pe.timestamp:08X}",
        "image_base": f"0x{pe.image_base:X}",
        "size_of_image": f"0x{pe.image_size:X}",
        "classification": classification,
        "core": core_rows,
        "optional": optional_rows,
        "summary": {
            "core_same_rva": sum(r["status"] == "SAME_RVA" for r in core_rows),
            "core_exact_relocated": sum(r["status"] == "EXACT_UNIQUE_RELOCATED" for r in core_rows),
            "core_ambiguous": sum(r["status"] == "EXACT_AMBIGUOUS" for r in core_rows),
            "core_not_found": sum(r["status"] == "EXACT_NOT_FOUND" for r in core_rows),
            "optional_resolved": sum(
                r["status"] in {"SAME_RVA", "EXACT_UNIQUE_RELOCATED"} for r in optional_rows
            ),
            "optional_total": len(optional_rows),
        },
        "_candidate_map_source": native_map,
    }


def printable(report: dict) -> dict:
    out = dict(report)
    out.pop("_candidate_map_source", None)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--map", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--candidate-map", type=Path)
    args = parser.parse_args()

    report = run(args.exe, args.map)
    clean = printable(report)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.candidate_map:
        cand = candidate_map(
            report["_candidate_map_source"],
            report["actual_sha256"],
            report["core"],
            report["optional"],
        )
        args.candidate_map.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_map.write_text(
            json.dumps(cand, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    print(json.dumps({
        "classification": report["classification"],
        "sha_match": report["sha_match"],
        **report["summary"],
    }))

    if report["classification"] in {"PARTIAL_EXACT_AMBIGUOUS", "CODEGEN_OR_SEMANTIC_DRIFT"}:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
