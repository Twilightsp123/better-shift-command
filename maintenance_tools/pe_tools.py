#!/usr/bin/env python3
"""Shared read-only PE/x64 helpers for the WH3 address-maintenance pipeline.

No third-party Python packages are required. The helpers intentionally keep
runtime promotion fail-closed: heuristic call scanning/fingerprints are evidence
for relocation ranking, never a substitute for final byte guards/runtime smoke.
"""
from __future__ import annotations

import bisect
import hashlib
import struct
from dataclasses import dataclass
from typing import Any, Iterable


IMAGE_SCN_MEM_EXECUTE = 0x20000000


@dataclass(frozen=True)
class RuntimeFunction:
    begin: int
    end: int
    unwind: int

    @property
    def size(self) -> int:
        return self.end - self.begin


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
        if machine != 0x8664 or not 1 <= section_count <= 96:
            raise ValueError("requires sane x64 PE")

        opt = pe_off + 24
        need(opt, opt_size)
        if opt_size < 112 or struct.unpack_from("<H", data, opt)[0] != 0x20B:
            raise ValueError("requires PE32+")

        self.timestamp = timestamp
        self.image_base = struct.unpack_from("<Q", data, opt + 24)[0]
        self.image_size = struct.unpack_from("<I", data, opt + 56)[0]
        self.headers_size = struct.unpack_from("<I", data, opt + 60)[0]
        number_of_dirs = struct.unpack_from("<I", data, opt + 108)[0]

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

        self._runtime_functions: list[RuntimeFunction] = []
        if number_of_dirs > 3 and opt_size >= 112 + 8 * 4:
            exception_rva, exception_size = struct.unpack_from("<II", data, opt + 112 + 3 * 8)
            exception_off = self.rva_to_file(exception_rva, exception_size) if exception_size else None
            if exception_off is not None and exception_size % 12 == 0:
                for i in range(exception_size // 12):
                    begin, end, unwind = struct.unpack_from("<III", data, exception_off + i * 12)
                    if begin and end > begin and end <= self.image_size:
                        self._runtime_functions.append(RuntimeFunction(begin, end, unwind))
        self._runtime_functions.sort(key=lambda f: f.begin)
        self._runtime_starts = [f.begin for f in self._runtime_functions]

    def file_to_rva(self, file_offset: int) -> int | None:
        if 0 <= file_offset < min(self.headers_size, len(self.data)):
            return file_offset
        for section in self.sections:
            raw_offset = int(section["raw_offset"])
            raw_size = int(section["raw_size"])
            if raw_offset <= file_offset < raw_offset + raw_size:
                return int(section["rva"]) + file_offset - raw_offset
        return None

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

    def read_rva(self, rva: int, size: int) -> bytes | None:
        off = self.rva_to_file(rva, size)
        if off is None:
            return None
        return bytes(self.data[off : off + size])

    def executable_ranges(self) -> Iterable[tuple[int, int, str]]:
        for section in self.sections:
            if int(section["flags"]) & IMAGE_SCN_MEM_EXECUTE:
                start = int(section["raw_offset"])
                end = start + int(section["raw_size"])
                if end > start:
                    yield start, end, str(section["name"])

    def runtime_function(self, rva: int) -> RuntimeFunction | None:
        if not self._runtime_starts:
            return None
        i = bisect.bisect_right(self._runtime_starts, rva) - 1
        if i < 0:
            return None
        f = self._runtime_functions[i]
        return f if f.begin <= rva < f.end else None

    def runtime_function_at(self, rva: int) -> RuntimeFunction | None:
        f = self.runtime_function(rva)
        return f if f and f.begin == rva else None

    def runtime_functions(self) -> tuple[RuntimeFunction, ...]:
        return tuple(self._runtime_functions)


def parse_rva(value: str | int) -> int:
    return value if isinstance(value, int) else int(value, 0)


def exact_occurrences(data: Any, pe: PE, needle: bytes, cap: int = 4096) -> list[int]:
    rows: list[int] = []
    for start, end, _ in pe.executable_ranges():
        pos = start
        while len(rows) < cap:
            hit = data.find(needle, pos, end)
            if hit < 0:
                break
            rva = pe.file_to_rva(hit)
            if rva is not None:
                rows.append(rva)
            pos = hit + 1
        if len(rows) >= cap:
            break
    return rows


def compile_mask(length: int, ranges: Iterable[Iterable[int]]) -> bytes:
    mask = bytearray(b"\x01" * length)
    for pair in ranges:
        start, end = (int(x) for x in pair)
        if start < 0 or end < start or end > length:
            raise ValueError(f"invalid mask range {start}:{end} for length {length}")
        for i in range(start, end):
            mask[i] = 0
    return bytes(mask)


def masked_occurrences(
    data: Any,
    pe: PE,
    pattern: bytes,
    mask: bytes,
    cap: int = 4096,
) -> list[int]:
    if len(pattern) != len(mask) or not pattern:
        raise ValueError("pattern/mask length mismatch")

    runs: list[tuple[int, int]] = []
    i = 0
    while i < len(mask):
        while i < len(mask) and not mask[i]:
            i += 1
        start = i
        while i < len(mask) and mask[i]:
            i += 1
        if i > start:
            runs.append((start, i))
    if not runs:
        raise ValueError("mask removes every byte")
    seed_start, seed_end = max(runs, key=lambda p: p[1] - p[0])
    seed = pattern[seed_start:seed_end]

    rows: list[int] = []
    for section_start, section_end, _ in pe.executable_ranges():
        pos = section_start
        while len(rows) < cap:
            hit = data.find(seed, pos, section_end)
            if hit < 0:
                break
            candidate = hit - seed_start
            if candidate >= section_start and candidate + len(pattern) <= section_end:
                buf = data[candidate : candidate + len(pattern)]
                if all((not mask[j]) or buf[j] == pattern[j] for j in range(len(pattern))):
                    rva = pe.file_to_rva(candidate)
                    if rva is not None:
                        rows.append(rva)
            pos = hit + 1
        if len(rows) >= cap:
            break
    return rows


def rip_target(data: Any, pe: PE, site_rva: int, disp_offset: int, instruction_end_offset: int) -> int | None:
    raw = pe.read_rva(site_rva + disp_offset, 4)
    if raw is None:
        return None
    disp = struct.unpack("<i", raw)[0]
    return site_rva + instruction_end_offset + disp


def direct_rel32_targets(data: Any, pe: PE, function: RuntimeFunction) -> list[dict[str, int]]:
    """Collect plausible E8 rel32 targets from a runtime-function byte range.

    This is deliberately a heuristic evidence source. It scans raw bytes rather
    than pretending to be a full x64 decoder; callers should require an exact
    target match plus independent evidence before promotion.
    """
    raw = pe.read_rva(function.begin, function.size)
    if raw is None:
        return []
    rows: list[dict[str, int]] = []
    for i in range(0, max(0, len(raw) - 4)):
        if raw[i] != 0xE8:
            continue
        disp = struct.unpack_from("<i", raw, i + 1)[0]
        target = function.begin + i + 5 + disp
        if 0 <= target < pe.image_size:
            rows.append({"call_rva": function.begin + i, "target_rva": target})
    return rows


def function_fingerprint(data: Any, pe: PE, site_rva: int) -> dict | None:
    function = pe.runtime_function(site_rva)
    if function is None:
        return None
    raw = pe.read_rva(function.begin, function.size)
    if raw is None:
        return None
    calls = direct_rel32_targets(data, pe, function)
    return {
        "begin": f"0x{function.begin:08X}",
        "end": f"0x{function.end:08X}",
        "size": function.size,
        "site_offset": site_rva - function.begin,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "entry32": raw[:32].hex(),
        "direct_rel32_call_count_heuristic": len(calls),
        "direct_rel32_targets_heuristic": [f"0x{x['target_rva']:08X}" for x in calls],
        "unwind_rva": f"0x{function.unwind:08X}",
    }
