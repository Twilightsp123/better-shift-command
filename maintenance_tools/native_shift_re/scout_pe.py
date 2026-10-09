#!/usr/bin/env python3
"""Read-only PE build gate and historical signature scout for WH3 9.0.3.

A historical byte-pattern match is a SEARCH LEAD, never a verified 9.0.3 RVA,
ABI, queue-consumer function, or approval to install a hook.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import os
import re
import struct
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

IMAGE_FILE_MACHINE_AMD64 = 0x8664
IMAGE_SCN_MEM_EXECUTE = 0x20000000
PE32_PLUS = 0x20B
MAX_SECTIONS = 96
OLD_902_SHA = "fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785"
DEFAULT_LEGACY_MAP = Path(__file__).resolve().parents[2] / "native_maps" / "candidates" / "wh3_9.0.2_fec656f4.json"


class InvalidPE(ValueError):
    """Untrusted binary is not a safely parseable AMD64 PE32+ executable."""


@dataclass(frozen=True)
class Section:
    name: str
    rva: int
    virtual_size: int
    raw_start: int
    raw_size: int
    executable: bool


def _need_range(length: int, off: int, size: int, label: str) -> None:
    if size < 0 or off < 0 or off > length or size > length - off:
        raise InvalidPE("out-of-bounds " + label)


def parse_pe(buf: mmap.mmap) -> Dict[str, Any]:
    """Read PE header/sections without trusting a raw-offset/RVA identity."""
    length = len(buf)
    _need_range(length, 0, 0x40, "DOS header")
    if buf[:2] != b"MZ":
        raise InvalidPE("not an MZ executable")
    pe_off = struct.unpack_from("<I", buf, 0x3C)[0]
    _need_range(length, pe_off, 24, "PE/COFF header")
    if buf[pe_off : pe_off + 4] != b"PE\0\0":
        raise InvalidPE("invalid PE signature")
    machine, sections_count = struct.unpack_from("<HH", buf, pe_off + 4)
    if machine != IMAGE_FILE_MACHINE_AMD64:
        raise InvalidPE("not Windows AMD64")
    if not 1 <= sections_count <= MAX_SECTIONS:
        raise InvalidPE("unreasonable section count")
    optional_size = struct.unpack_from("<H", buf, pe_off + 20)[0]
    optional_off = pe_off + 24
    _need_range(length, optional_off, optional_size, "optional header")
    if optional_size < 64 or struct.unpack_from("<H", buf, optional_off)[0] != PE32_PLUS:
        raise InvalidPE("not PE32+ or truncated optional header")
    image_base = struct.unpack_from("<Q", buf, optional_off + 24)[0]
    image_size = struct.unpack_from("<I", buf, optional_off + 56)[0]
    if image_base == 0 or image_size == 0:
        raise InvalidPE("invalid image base/size")
    table_off = optional_off + optional_size
    _need_range(length, table_off, 40 * sections_count, "section table")
    sections: List[Section] = []
    raw_ranges = []
    for index in range(sections_count):
        off = table_off + 40 * index
        name = bytes(buf[off : off + 8]).split(b"\0", 1)[0].decode("ascii", "replace")
        virtual_size, rva, raw_size, raw_start = struct.unpack_from("<IIII", buf, off + 8)
        flags = struct.unpack_from("<I", buf, off + 36)[0]
        if raw_size:
            _need_range(length, raw_start, raw_size, "section %s raw extent" % name)
            if rva >= image_size or raw_size > image_size - rva + 0x1000:
                raise InvalidPE("section has implausible mapped RVA")
            raw_ranges.append((raw_start, raw_start + raw_size))
        sections.append(Section(name, rva, virtual_size, raw_start, raw_size, bool(flags & IMAGE_SCN_MEM_EXECUTE)))
    raw_ranges.sort()
    if any(raw_ranges[i][1] > raw_ranges[i + 1][0] for i in range(len(raw_ranges) - 1)):
        raise InvalidPE("overlapping raw sections")
    if not any(s.executable and s.raw_size for s in sections):
        raise InvalidPE("no raw executable section")
    return {"image_base": image_base, "size_of_image": image_size, "sections": sections}


def _hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _guard_pattern(guard: Dict[str, Any]):
    hx = guard.get("guard", "")
    if not isinstance(hx, str) or not re.fullmatch(r"(?:[a-fA-F0-9]{2})+", hx):
        raise ValueError("invalid guard hex")
    pattern = bytes.fromhex(hx)
    mask = bytearray(b"\x01" * len(pattern))
    for bounds in guard.get("normalization", {}).get("mask_ranges", []):
        if not isinstance(bounds, list) or len(bounds) != 2:
            raise ValueError("invalid mask pair")
        a, b = bounds
        if not isinstance(a, int) or not isinstance(b, int) or a < 0 or b <= a or b > len(pattern):
            raise ValueError("mask range outside guard")
        mask[a:b] = b"\x00" * (b - a)
    best_start, best_length = 0, 0
    i = 0
    while i < len(mask):
        if mask[i] == 0:
            i += 1
            continue
        j = i
        while j < len(mask) and mask[j]:
            j += 1
        if j - i > best_length:
            best_start, best_length = i, j - i
        i = j
    if best_length < 5:
        raise ValueError("guard has no selective unmasked anchor")
    return pattern, bytes(mask), best_start, pattern[best_start : best_start + best_length]


def scout_legacy_guards(buf: mmap.mmap, sections: Sequence[Section], old_map: Dict[str, Any]):
    """Only exact/masked raw-byte similarity; no opcode, ABI, or hook inference."""
    result: Dict[str, Any] = {}
    sites = dict(old_map.get("core", {}))
    sites.update({"optional/" + k: v for k, v in old_map.get("optional", {}).items()})
    for name, spec in sorted(sites.items()):
        pattern, mask, anchor_off, anchor = _guard_pattern(spec)
        matches = []
        for section in sections:
            if not section.executable or not section.raw_size:
                continue
            start = section.raw_start
            end = start + section.raw_size
            pos = buf.find(anchor, start, end)
            while pos != -1:
                origin = pos - anchor_off
                if origin >= start and origin + len(pattern) <= end:
                    candidate = buf[origin : origin + len(pattern)]
                    if all(not mask[i] or candidate[i] == pattern[i] for i in range(len(pattern))):
                        matches.append({"rva": "0x%X" % (section.rva + origin - start), "section": section.name})
                pos = buf.find(anchor, pos + 1, end)
        result[name] = {
            "legacy_rva": spec.get("rva"),
            "legacy_guard_role": spec.get("role"),
            "historical_similarity_matches": matches,
            "match_count": len(matches),
            "interpretation": "BYTE_SIMILARITY_ONLY_NOT_A_VERIFIED_9_0_3_HOOK",
        }
    return result


def inspect(exe: Path, legacy_map: Dict[str, Any], expected_sha256: Optional[str] = None,
            target_version: str = "9.0.3") -> Dict[str, Any]:
    if expected_sha256 is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("expected sha256 must have 64 hexadecimal characters")
    sha = _hash_file(exe)
    old_sha = str(legacy_map.get("game", {}).get("sha256", "")).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", old_sha):
        raise ValueError("legacy map missing valid game sha256")
    with exe.open("rb") as fd, mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_READ) as buf:
        pe = parse_pe(buf)
        matches = scout_legacy_guards(buf, pe["sections"], legacy_map)
    is_old_build = target_version == "9.0.3" and sha == old_sha
    hash_confirmed = expected_sha256 is not None and sha == expected_sha256.lower()
    if is_old_build:
        status = "REJECTED_HISTORICAL_9_0_2_BINARY"
    elif expected_sha256 is not None and not hash_confirmed:
        status = "REJECTED_EXPECTED_SHA_MISMATCH"
    elif not hash_confirmed:
        status = "UNVERIFIED_BUILD_SHA_DISCOVERY_ONLY"
    else:
        status = "SHA_VERIFIED_BINARY_RESEARCH_ONLY"
    return {
        "schema": "bsc.native_shift_pe_scout.v1",
        "target_version": target_version,
        "exe_name": exe.name,
        "exe_size_bytes": exe.stat().st_size,
        "exe_sha256": sha,
        "expected_sha256": expected_sha256.lower() if expected_sha256 else None,
        "expected_hash_matches": hash_confirmed,
        "game_version_proven": False,  # File SHA alone cannot prove a version label.
        "historical_exe_sha256": old_sha,
        "status": status,
        "image_base": "0x%X" % pe["image_base"],
        "size_of_image": "0x%X" % pe["size_of_image"],
        "sections": [asdict(section) for section in pe["sections"]],
        "legacy_byte_similarity": matches,
        "queue_completion_function": None,
        "queue_head_writer_function": None,
        "move_braking_function": None,
        "successor_activation_function": None,
        "runtime_patch_authorized": False,
        "warnings": [
            "Historical guard match is only a reverse-engineering lead, not an engine callgraph or ABI proof.",
            "No function addresses, VTables, native queue writes or patch sites are promoted automatically.",
        ],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True, help="Unmodified user-owned Warhammer3.exe")
    parser.add_argument("--legacy-map", type=Path, default=DEFAULT_LEGACY_MAP)
    parser.add_argument("--target-version", default="9.0.3")
    parser.add_argument("--expected-sha256", help="Verified build hash; without one results are discovery-only")
    parser.add_argument("--report", type=Path, required=True, help="Output JSON; never writes the EXE")
    args = parser.parse_args(argv)
    try:
        if args.report.resolve() in (args.exe.resolve(), args.legacy_map.resolve()):
            raise ValueError("report path may not overwrite the EXE or historical map")
        old_map = json.loads(args.legacy_map.read_text(encoding="utf-8"))
        result = inspect(args.exe, old_map, args.expected_sha256, args.target_version)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print("%s: %s" % (result["status"], args.report))
        return 3 if result["status"].startswith("REJECTED_") else 0
    except (ValueError, OSError, struct.error, InvalidPE, json.JSONDecodeError) as exc:
        print("SCOUT_FAILED: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
