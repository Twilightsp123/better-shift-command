#!/usr/bin/env python3
"""Read-only exact-binary WH3 9.0.3 route-gate evidence; never patches game."""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import struct
from pathlib import Path
from scout_pe import parse_pe

PINNED_EXE_SHA256 = "518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
# Each row is an RVA:exact original machine bytes. 9.0.3-labelled user EXE only.
# Instruction sites include route-building side effects and callback gate instructions.
ORIGINAL_GUARDS = """
0310F560:488bc4
0310F58C:4489a970010000
0310F596:4489a984010000
0310F5B6:e861cd0000
0310F5C0:32c0
0310F6DB:f30f7f83b4010000
0310F728:e8a3b0fdff
0310F7CF:e820affdff
0310F880:e84baffdff
0310F8DC:e8efaefdff
0310FA8B:e840adfdff
0310FB02:4c89ab98010000
0310FB09:4c89aba0010000
0310FB48:8ac1
030EA7D0:48895c2410
030EA8F9:e852a10300
030EA919:e8aadfffff
030E88C8:4c8bdc
030E8A31:f30f5c4510
030E8A3B:f30f59c0
030E8A43:f30f58c1
030E8A47:f30f51f0
030E8A52:f3410f59742448
030E8A67:83780802
030E8A71:0f8380000000
030E8A80:f30f117018
0311E891:33ff
0311EAC7:e8940affff
0311EACC:448ac0
0311EAD4:84c0
0311EAD6:7411
0311EAD8:398be4040000
0311EADE:7309
0311EAE0:448d49ff
0311EAE4:418ad1
0311EAE9:408ad7
0311EB04:4584c0
0311EB07:7407
0311EB09:84d2
0311EB0B:7503
0311EB0D:418af9
0311EB10:40887e24
0311EB14:413af9
0311EB17:0f85bb000000
0311EBC2:894e20
0311EC0E:c7462004000000
"""
CALL_EDGES = {
    "callback_route": (0x0311EAC7, 0x0310F560),
    "gate_clone1": (0x0310F728, 0x030EA7D0),
    "gate_construct": (0x0310F7CF, 0x030EA6F4),
    "gate_clone2": (0x0310F880, 0x030EA7D0),
    "gate_clone3": (0x0310F8DC, 0x030EA7D0),
    "clone_recalculate": (0x030EA919, 0x030E88C8),
}


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_executable_rva(mm, sections, rva, length):
    for s in sections:
        if s.rva <= rva and rva + length <= s.rva + s.raw_size:
            if not s.executable:
                raise ValueError("RVA_NOT_EXECUTABLE")
            offset = s.raw_start + rva - s.rva
            return bytes(mm[offset:offset + length])
    raise ValueError("RVA_NOT_IN_RAW_EXECUTABLE_SECTION")


def decode_e8_target(site_rva, raw):
    if len(raw) != 5 or raw[0] != 0xE8:
        raise ValueError("NOT_A_DIRECT_E8_CALL")
    return site_rva + 5 + struct.unpack_from("<i", raw, 1)[0]


def branch_flag_result(return_al, mode_field):
    """Only native callback segment after xor edi,edi, NOT global WH3 behavior."""
    return int(bool(return_al) and mode_field >= 2)


def verify(exe: Path) -> dict:
    digest = _hash_file(exe)
    if digest != PINNED_EXE_SHA256:
        raise ValueError("EXE_SHA256_MISMATCH")
    with exe.open("rb") as file, mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        pe = parse_pe(mm)
        if pe["image_base"] != 0x140000000:
            raise ValueError("EXE_BASE_MISMATCH")
        rows = []
        for row in ORIGINAL_GUARDS.strip().splitlines():
            addr, hexdigits = row.strip().split(":")
            site = int(addr, 16)
            expected = bytes.fromhex(hexdigits)
            observed = read_executable_rva(mm, pe["sections"], site, len(expected))
            if observed != expected:
                raise ValueError("GUARD_MISMATCH_AT_" + addr)
            rows.append({"rva": "0x" + addr, "bytes": hexdigits})
        calls = {}
        for name, (site, target) in CALL_EDGES.items():
            actual = decode_e8_target(
                site, read_executable_rva(mm, pe["sections"], site, 5)
            )
            if actual != target:
                raise ValueError("CALL_EDGE_MISMATCH_" + name)
            calls[name] = {"from": hex(site), "to": hex(target)}
    return {
        "schema": "bsc.n1.route_gate.static.v1",
        "exe_sha256": digest,
        "version_label_proven_by_exe_resource": False,
        "guard_count": len(rows),
        "machine_instruction_guards": rows,
        "verified_direct_call_edges": calls,
        "callback_segment_truth_table": [
            {"AL": value, "mode": mode, "flag": branch_flag_result(value, mode)}
            for value in (0, 1) for mode in (0, 1, 2, 3)
        ],
        "limitations": [
            "AL and mode gameplay meaning unknown",
            "flag condition is local to this callback branch",
            "terminal braking and speed writes not identified",
        ],
        "runtime_patch_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.exe.resolve() == args.out.resolve():
        parser.error("output must not overwrite input EXE")
    output = verify(args.exe)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print("STATIC_ONLY", output["guard_count"], "guards and",
          len(CALL_EDGES), "calls; patch=false")


if __name__ == "__main__":
    main()
