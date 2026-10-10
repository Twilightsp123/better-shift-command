#!/usr/bin/env python3
"""Exact-SHA, read-only WH3 9.0.3 Native MOVE -> member fanout evidence.
No game modification or runtime patch promotion.
"""
import argparse
import json
import mmap
from pathlib import Path

from audit_903_formation_entry import TARGET_SHA256, digest_file, pe_sections, read_executable, e8_target

INSTRUCTION_GUARDS = """
03032965 e8dab1ffff
0302dbc4 e8b34cfeff
0302dbc9 488b8570020000
0302dbd3 488b5018
0302dbd7 488b5270
0302dbdb e8b0780a00
030d54a2 4c8b99300b0000
030d54af e878c5ffff
030d54bc 448b4f24
030d54ca 41ff5248
030d54d0 397724
030d54d5 488b4728
030d54d9 4c8d0476
030d54dd 49c1e004
030d54e6 4c03442440
030d54f0 488b1cf0
030d54f7 450fb74822
030d54fc e867a3e8ff
030d550f ff9068030000
030d5515 ffc6
030d5517 3b7724
030d551a 72b9
030d5522 ff5020
02f5f86e 418b00
02f5f8bd c6435026
03022a66 84d2
03043284 b201
0302db81 488b81483d0000
0302db88 8b9048020000
0302db8e e851ddfeff
0301b924 488bbe88010000
0301b92e 8b8e84010000
0301b93d 488b17
0301b946 e8154b0c00
0301b96d 48899ef8320000
030e047e ff90f8030000
030e04c2 e9596ffeff
030c743e 4883c120
"""
CALL_TARGETS = {
    "MOVE_ISSUER_TO_ROUTE_UPDATE": (0x03032965, 0x0302DB44),
    "ROUTE_UPDATE_TO_ROUTE_CONFIG": (0x0302DBC4, 0x0301287C),
    "ROUTE_UPDATE_TO_GROUP_FANOUT": (0x0302DBDB, 0x030D5490),
    "GROUP_FANOUT_TO_MODE_HELPER": (0x030D54AF, 0x030D1A2C),
    "GROUP_FANOUT_TO_MEMBER_PAYLOAD": (0x030D54FC, 0x02F5F868),
    "SECONDARY_TO_MEMBER_ROUTE_WRAPPER": (0x03022C82, 0x03012A2C),
    "SECONDARY_CALLER_TO_SECONDARY": (0x03043289, 0x03022A4C),
    "ROUTE_UPDATE_TO_GROUP_BUILDER": (0x0302DB8E, 0x0301B8E4),
    "GROUP_BUILDER_TO_MEMBER_INSERT": (0x0301B946, 0x030E0460),
}

def verify(path: Path):
    sha = digest_file(path)
    if sha != TARGET_SHA256:
        raise ValueError("EXE_SHA256_MISMATCH")
    rows = [(int(a, 16), bytes.fromhex(b)) for a, b in (
        line.split() for line in INSTRUCTION_GUARDS.strip().splitlines()
    )]
    with path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        sections = pe_sections(mm)
        for site, expected in rows:
            if read_executable(mm, sections, site, len(expected)) != expected:
                raise ValueError("ORIGINAL_INSTRUCTION_MISMATCH_" + hex(site))
        for name, (site, target) in CALL_TARGETS.items():
            got = e8_target(site, read_executable(mm, sections, site, 5))
            if got != target:
                raise ValueError("DIRECT_CALL_MISMATCH_" + name)
    return {
        "schema": "bsc.n1.903.original_move_member_fanout.static.v1",
        "exe_sha256": sha,
        "opcode_guards": len(rows),
        "direct_call_edges": len(CALL_TARGETS),
        "group_stride_bytes": 0x30,
        "member_issue_virtual_offset": 0x368,
        "payload_constructor_rva": "0x02F5F868",
        "limitations": [
            "Group elements not independently confirmed to be rendered soldier models",
            "Virtual +0x368 concrete implementation and per-model completion unknown",
            "Observed call path does not alone distinguish Shift append versus RMB",
            "Not proof of physical motion, arrival or collision behavior",
        ],
        "runtime_patch_authorized": False,
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    if args.exe.resolve() == args.report.resolve():
        p.error("report cannot overwrite the EXE")
    report = verify(args.exe)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("STATIC ONLY", report["opcode_guards"], "guards",
          report["direct_call_edges"], "calls; no patch")

if __name__ == "__main__":
    main()
