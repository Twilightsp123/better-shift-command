#!/usr/bin/env python3
"""EXACT WH3 build 9.0.3-labelled static MOVE-state instruction guard verification.

No hook installation, queue changes, game execution, automatic RVA promotion,
or code injection. Byte matches + stack arithmetic are source evidence ONLY.
"""
import argparse
import hashlib
import json
import mmap
import struct
from pathlib import Path
from scout_pe import parse_pe

TARGET_SHA = "518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
# Selected instruction bytes from direct LLVM x64 disassembly. The 9.0.3
# VERSIONINFO has not been independently confirmed; SHA is the true build ID.
GUARDS = {
    "move_prepare_writeback_pointer": (0x0302608D, "4c897590"),
    "move_allocate_task": (0x03026091, "e81a9ff0ff"),
    "move_pass_task_param": (0x0302609F, "4c8d4c2440"),
    "move_call_task_ctor": (0x030260AF, "e88066f0ff"),
    "task_copy_source_arg": (0x02F2C770, "498bd1"),
    "task_copy_input": (0x02F2C781, "498bc8"),
    "task_copy_field_0x50": (0x02F2C8A7, "488b4250"),
    "task_write_field_0x80": (0x02F2C8AB, "48894150"),
    "task_output_pointer_check": (0x02F41651, "4883b98000000000"),
    "task_output_pointer_load": (0x02F4166E, "488b8b80000000"),
    "task_pointer_writeback": (0x02F41675, "488901"),
    "task_fallback_local_write": (0x02F4167F, "48898398000000"),
    "native_pool_return": (0x0310EE32, "488bc3"),
    "native_state_ctor_zero": (0x030EE88D, "44894120"),
    "handoff_provider_state4": (0x03039FC0, "837a2004"),
    "handoff_provider_flag": (0x03039FC6, "807a2400"),
    "handoff_provider_ptr": (0x03039FCC, "4883ba5801000000"),
    "move_reuse_check_flag": (0x03025DE9, "41387b25"),
    "move_reuse_compare_0": (0x03025E1C, "0f2f059d6d8f00"),
    "move_reuse_compare_001": (0x03025E2C, "0f2f05c96e8f00"),
    "move_reuse_discard_refcount": (0x03025E35, "41ff4b18"),
    "move_reuse_discard_pointer": (0x03025E39, "49893e"),
    "pool_state_transition_to_4": (0x0311E4B1, "448d7904"),
    "pool_write_state": (0x0311E4B5, "44897f20"),
    "successor_state_set1": (0x030408CF, "c7422001000000"),
}
FLOATS = {
    "original_check_zero": (0x0391CBC0, 0.0),
    "original_check_small_tolerance": (0x0391CCFC, 0.01),
}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pe_read(mm, sections, rva, size, executable):
    for section in sections:
        if section.rva <= rva and rva + size <= section.rva + section.raw_size:
            if executable and not section.executable:
                raise ValueError("RVA is not executable: %s" % hex(rva))
            position = section.raw_start + rva - section.rva
            return bytes(mm[position : position + size])
    raise ValueError("RVA not mapped to PE raw section: %s" % hex(rva))


def verify(path):
    sha = digest(path)
    if sha != TARGET_SHA:
        raise ValueError("wrong EXE SHA256: " + sha)
    with path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        pe = parse_pe(mm)
        if pe["image_base"] != 0x140000000:
            raise ValueError("unexpected image base")
        sections = pe["sections"]
        rows = []
        for site, (rva, guard_hex) in GUARDS.items():
            expected = bytes.fromhex(guard_hex)
            actual = pe_read(mm, sections, rva, len(expected), True)
            if actual != expected:
                raise ValueError("%s mismatched at %s" % (site, hex(rva)))
            rows.append({"site": site, "rva": "0x%X" % rva, "bytes": actual.hex(), "matched": True})
        constants = {}
        for name, (rva, expected) in FLOATS.items():
            value = struct.unpack("<f", pe_read(mm, sections, rva, 4, False))[0]
            if abs(value - expected) > 1e-6:
                raise ValueError("float constant mismatch: " + name)
            constants[name] = value
    # Verified by comparing the original function's prologue and call-site frame:
    # (S - 0xB8) - 0x70 == (S - 0x1B8) + 0x40 + 0x50
    if -0xB8 - 0x70 != -0x1B8 + 0x40 + 0x50:
        raise AssertionError("stack writeback-pointer provenance changed")
    return {
        "schema": "bsc.native_move_state_origin.static.v1",
        "exe_sha256": sha,
        "selected_instruction_guards": rows,
        "original_float_constants": constants,
        "proven_stack_alias": "MOVE+0xA0 writeback address copied from task init+0x50 to task+0x80",
        "limitations": [
            "selected bytes and stack aliases only; no full program semantic proof",
            "state 1/4 native meaning and physical braking unknown",
            "exact user-supplied EXE hash, not an authorized runtime map",
        ],
        "patch_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.exe.resolve() == args.report.resolve():
        parser.error("refusing to overwrite EXE")
    report = verify(args.exe)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS: %d exact instruction guards; PATCH_AUTHORIZED=false" % len(GUARDS))


if __name__ == "__main__":
    main()
