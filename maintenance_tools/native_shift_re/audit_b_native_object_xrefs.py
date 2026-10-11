#!/usr/bin/env python3
"""Exact-WH3-BSC native cross-reference census for B route and member task objects.

This tool does NOT patch the EXE, inject a DLL, or infer runtime participation.
It scans ALL original executable section bytes for *candidates*, then requires
an objdump-confirmed instruction boundary in a PE unwind-owned function.
It is a focused complement to the frozen 175-node selected-function call graph.
"""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import sys
from pathlib import Path

from audit_wh3_full_native_chain import StrictPE, read_manifest, from_hex

VTABLE_ROOTS = {
    0x03905D98: "conditional_bit7_consumer_task",
    0x03905D18: "negative_control_task",
    0x03905E18: "separate_deferred_packet_task",
    0x03AE0128: "B_group_route_task",
    0x03914618: "separate_member_status_action",
}
DIRECT_TARGETS = {
    0x02F6EF4C: "conditional_member_task_constructor",
    0x03263AB0: "B_group_task_constructor",
    0x02F87684: "bit7_consumer_virtual_method",
    0x03071E04: "main_member_goal_record_replace",
    0x0311954C: "member_motor_goal_writer",
    0x030F65AC: "B_route_cache_destructor",
}
# These sites are already original-EXE guarded by full_chain_manifest.json.
# The same number +0x70 in unrelated owners is NEVER an object identity proof.
TYPED_ANCHORS = {
    "node_geometry_write": 0x030ECBA2,
    "route_manager_geometry_write": 0x03129097,
    "node_geometry_destroy_read": 0x030F65D2,
    "B_task_stored_node_read": 0x03281454,
    "B_member_bit7_write": 0x03263C0A,
    "member_bit7_task_vtable_install": 0x02F6EFDE,
    "member_goal_writer_commit": 0x0311963A,
}


def scan_blob(blob: bytes, start: int, rip_targets: set[int],
              call_targets: set[int]) -> list[dict]:
    """Return untrusted x86 RIP-relative / E8 byte-pattern candidates.

    A candidate must subsequently pass the independent instruction-boundary
    check to be reported as a native instruction. No generic +0x70 aliasing.
    """
    output = []
    for i in range(len(blob)):
        address = start + i
        if i + 7 <= len(blob) and blob[i] in (0x48, 0x4C) and (
                blob[i+1] in (0x8D, 0x8B)) and blob[i+2] & 0xC7 == 0x05:
            target = address + 7 + struct.unpack_from("<i", blob, i+3)[0]
            if target in rip_targets:
                output.append({
                    "site": address, "target": target,
                    "kind": "rip_lea" if blob[i+1] == 0x8D else "rip_mov",
                    "bytes": blob[i:i+7].hex(),
                })
        if i + 5 <= len(blob) and blob[i] == 0xE8:
            target = address + 5 + struct.unpack_from("<i", blob, i+1)[0]
            if target in call_targets:
                output.append({
                    "site": address, "target": target,
                    "kind": "direct_call", "bytes": blob[i:i+5].hex(),
                })
    return output


def instruction_starts(pe: StrictPE, rva: int, cache: dict) -> set[int]:
    owner = pe.function(rva)
    if owner is None:
        return set()  # no unwind owner means not validated, not a proof
    if owner not in cache:
        start, end = owner
        asm = pe.disasm(start, end-start)
        starts = set()
        for line in asm.splitlines():
            head = line.split(":", 1)[0].strip()
            if head and all(c in "0123456789abcdef" for c in head):
                starts.add(int(head, 16))
        cache[owner] = starts
    return cache[owner]


def verified_cross_references(pe: StrictPE) -> dict:
    if shutil.which("objdump") is None:
        raise ValueError("OBJDUMP_REQUIRED_FOR_INSTRUCTION_BOUNDARIES")
    rip_targets = set(VTABLE_ROOTS)
    call_targets = set(DIRECT_TARGETS)
    preliminary = []
    for name, start, raw_size, offset, virtual, flags in pe.sections:
        if flags & 0x20000000 and raw_size:
            preliminary.extend(scan_blob(
                pe.read(start, raw_size, True), start, rip_targets, call_targets))
    cache = {}
    confirmed = []
    rejected = []
    for hit in preliminary:
        owner = pe.function(hit["site"])
        if owner and hit["site"] in instruction_starts(pe, hit["site"], cache):
            confirmed.append({
                **{k: (hex(v) if k in ("site", "target") else v)
                   for k, v in hit.items()},
                "function": hex(owner[0]),
                "label": (VTABLE_ROOTS if hit["kind"] != "direct_call"
                          else DIRECT_TARGETS)[hit["target"]],
                "evidence_level": "EXACT_EXE_DISASSEMBLED_INSTRUCTION",
            })
        else:
            rejected.append({"site": hex(hit["site"]),
                             "reason": "NO_VERIFIED_INSTRUCTION_BOUNDARY"})
    return {
        "confirmed": sorted(confirmed, key=lambda x: int(x["site"], 16)),
        "rejected_candidates": rejected,
        "scanned_code_sections": sum(1 for s in pe.sections if s[5] & 0x20000000),
        "disassembled_owner_functions": len(cache),
    }


# B subcontroller and motor probes have DIFFERENT objects. This deliberately
# collects the full instruction+operand before any alleged dataflow join.
FOCUSED_FUNCTIONS = {
    0x03281444: "B_task_node_reference_check",
    0x03121ABC: "B_route_node_lookup",
    0x030ECB10: "B_node_construct_and_cache",
    0x03128E80: "group_route_context_tick",
    0x03109D78: "route_node_recycle",
    0x030F65AC: "route_node_geometry_release",
    0x030FDA9C: "shared_geometry_generator",
    0x030D5490: "A_group_to_member_fanout",
    0x03071E04: "member_goal_replace",
    0x0311954C: "member_motor_writer",
}


def displacement_candidates(pe: StrictPE) -> list[dict]:
    """List bounded native operands, without falsely merging object owners.

    Full disassembly of these ten original unwind functions is independently
    obtained at runtime. A memory operand ending +0x70 is NOT necessarily a
    B node. Provenance still requires walking the base register's origin.
    """
    import re
    relevant = re.compile(r"\[[^\]]*\+0x(?:70|58|2d0|2d8|b10)\]")
    results = []
    for target, label in FOCUSED_FUNCTIONS.items():
        owner = pe.function(target)
        if owner is None:
            raise ValueError("FOCUS_FUNCTION_NOT_UNWIND_OWNED:" + hex(target))
        instructions = pe.disasm(owner[0], owner[1]-owner[0]).splitlines()
        for i, line in enumerate(instructions):
            if not relevant.search(line.lower()):
                continue
            match = re.match(r"^\s*([0-9a-f]+):", line)
            if not match:
                continue
            results.append({
                "site": "0x" + match.group(1),
                "function": hex(owner[0]),
                "focus": label,
                "disassembly": line.strip(),
                "previous_line": instructions[i-1].strip() if i else "",
                "next_line": instructions[i+1].strip()
                             if i+1 < len(instructions) else "",
                "base_pointer_owner_proven": False,
                "grade": "EXACT_DISASSEMBLY_OPERAND_NOT_OBJECT_ALIAS",
            })
    return results


def run(exe: Path, manifest: Path) -> dict:
    m = read_manifest(manifest)
    pe = StrictPE(exe)  # SHA256 and PE ImageBase checked before any scan
    try:
        pinned = {from_hex(g["site"]): g for g in m["guard_sites"]}
        for name, site in TYPED_ANCHORS.items():
            if site not in pinned:
                raise ValueError("MISSING_FROZEN_NATIVE_ANCHOR:" + name)
            guard = pinned[site]
            actual = pe.read(site, len(bytes.fromhex(guard["pattern"])), True)
            if actual.hex() != guard["pattern"]:
                raise ValueError("NATIVE_ANCHOR_CHANGED:" + name)
        # Independent vtable-slot guard. These are implementation pointers,
        # not assertions about which task instance ran during V3.
        for slot, implementation in ((0x03905D98+0x78, 0x02F87684),
                                     (0x03905D18+0x78, 0x011287FC),
                                     (0x03AE0128+0x10, 0x03281408)):
            observed = struct.unpack("<Q", pe.read(slot, 8))[0]
            if observed != pe.base + implementation:
                raise ValueError("TASK_VTABLE_IDENTITY_CHANGED:" + hex(slot))
        xrefs = verified_cross_references(pe)
        memory_operands = displacement_candidates(pe)
        return {
            "schema": "bsc.n1.native_object_xref.v1",
            "exe_sha256": pe.sha,
            "proof_level": "STATIC_EXACT_EXE_XREF_ONLY",
            "inherited_manifest_guards": len(TYPED_ANCHORS),
            "typed_anchor_sites": {name: hex(site)
                                   for name, site in TYPED_ANCHORS.items()},
            "xrefs": xrefs,
            "focused_route_to_motor_operand_candidates": memory_operands,
            "specific_unproven_edges": [
                "B node+0x70 -> per-member goal +0x7F8/+0x818 or +0x1E0: no type-verified edge yet",
                "0x03905D98 task constructor -> concrete live per-member task in V3: not recorded",
                "RMB/Shift -> target installation latency of each member in V3: not recorded",
            ],
            "warning": (
                "RIP address/callsite xref is not an instance owner chain. "
                "A raw +0x70 match must NEVER be labelled B-route consumption."
            ),
            "patch_authorized": False,
            "game_verified": False,
        }
    finally:
        pe.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", required=True, type=Path)
    ap.add_argument("--manifest", type=Path,
                    default=Path(__file__).with_name("full_chain_manifest.json"))
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    if args.exe.resolve() == args.out.resolve():
        ap.error("REFUSE_EXE_OVERWRITE")
    try:
        report = run(args.exe, args.manifest)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
        print("STATIC XREF", len(report["xrefs"]["confirmed"]),
              "verified sites; NO PATCH; V3 UNOBSERVED")
        return 0
    except (OSError, ValueError, KeyError, struct.error) as error:
        print("NATIVE_XREF_AUDIT_BLOCKED:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
