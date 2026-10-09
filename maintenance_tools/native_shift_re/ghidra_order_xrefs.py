#@category BSC.Native Shift Research
# coding: utf-8
"""Ghidra Jython script: locate *candidate* original queue field accesses.

Run in a fully analyzed 9.0.3 PE project with an original EXE on disk.
This is NOT a proof of a native OrderHead writer, ABI, or safe patch point.

Example headless postScript arguments:
  -postScript ghidra_order_xrefs.py --exe=C:/WH3/Warhammer3.exe \
      --expected-sha256=<exact-new-9.0.3-hash> --output=C:/WH3/n1_903_xrefs.json

No imports from BSC runtime, no changes to currentProgram, no EXE writes.
"""
import hashlib
import json
import os
import re
from ghidra.program.model.address import AddressSet
from ghidra.program.model.scalar import Scalar

# Hypotheses from 9.0.2 ONLY. 9.0.3 offsets must be re-established by dataflow.
FIELD_CANDIDATES = {0x2F88: "legacy_OrderCount", 0x2F8C: "legacy_OrderHead"}
MAX_MATCHES = 10000


def args_map(args):
    out = {}
    for arg in args:
        if not arg.startswith("--") or "=" not in arg:
            raise ValueError("expected --key=value argument: %s" % arg)
        k, v = arg[2:].split("=", 1)
        if k in out or not v:
            raise ValueError("duplicate or empty argument %s" % k)
        out[k] = v
    for required in ("exe", "expected-sha256", "output"):
        if required not in out:
            raise ValueError("missing required --%s" % required)
    if set(out) - set(("exe", "expected-sha256", "output")):
        raise ValueError("unknown arguments")
    if not re.match(r"^[0-9a-fA-F]{64}$", out["expected-sha256"]):
        raise ValueError("expected-sha256 must be 64 hex characters")
    return out


def file_hashes(path):
    sha = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    with open(path, "rb") as handle:
        while True:
            data = handle.read(4 * 1024 * 1024)
            if not data:
                break
            sha.update(data)
            md5.update(data)
            size += len(data)
    return sha.hexdigest(), md5.hexdigest(), size


def to_rva(addr, base):
    if addr is None:
        return None
    try:
        n = addr.subtract(base)
        if n < 0:
            return None
        return "0x%X" % n
    except Exception:
        return None


def bytes_hex(instr):
    try:
        return "".join("%02x" % (int(byte) & 0xff) for byte in instr.getParsedBytes())
    except Exception:
        return None


def read_write_hint(instr, index):
    # This ref-type is for the whole operand, not proven to be the queue field.
    try:
        rt = instr.getOperandRefType(index)
        if rt is None:
            return "UNKNOWN"
        reads, writes = rt.isRead(), rt.isWrite()
        if reads and writes:
            return "READ_WRITE_HINT"
        if writes:
            return "WRITE_HINT"
        if reads:
            return "READ_HINT"
    except Exception:
        pass
    return "UNKNOWN"


def candidate_operands(instr):
    result = []
    for idx in range(instr.getNumOperands()):
        values = []
        try:
            objects = instr.getOpObjects(idx)
            for o in objects:
                if isinstance(o, Scalar):
                    values.append(int(o.getSignedValue()))
        except Exception:
            continue
        for offset, field in FIELD_CANDIDATES.items():
            if offset in values or -offset in values:
                result.append({
                    "candidate_field_name": field,
                    "legacy_field_offset": "0x%X" % offset,
                    "operand_index": idx,
                    "access_hint": read_write_hint(instr, idx),
                    "displacement_not_root_proven": True,
                })
    return result


def function_meta(listing, instr, base):
    func = listing.getFunctionContaining(instr.getAddress())
    if func is None:
        return {"name": None, "entry_rva": None}
    return {"name": str(func.getName()), "entry_rva": to_rva(func.getEntryPoint(), base)}


def collect(current_program, monitor_obj):
    listing = current_program.getListing()
    memory = current_program.getMemory()
    image_base = current_program.getImageBase()
    records = []
    scanned = 0
    truncated = False
    for block in memory.getBlocks():
        if not block.isExecute():
            continue
        iterator = listing.getInstructions(AddressSet(block.getStart(), block.getEnd()), True)
        while iterator.hasNext():
            monitor_obj.checkCanceled()
            ins = iterator.next()
            scanned += 1
            candidates = candidate_operands(ins)
            if not candidates:
                continue
            if len(records) >= MAX_MATCHES:
                truncated = True
                break
            pcode = []
            try:
                pcode = sorted(set(str(op.getMnemonic()) for op in ins.getPcode()))
            except Exception:
                pass
            records.append({
                "rva": to_rva(ins.getAddress(), image_base),
                "instruction": str(ins),
                "bytes": bytes_hex(ins),
                "containing_function": function_meta(listing, ins, image_base),
                "candidate_operands": candidates,
                "instruction_pcode_kinds": pcode,
                "engine_root_proven": False,
                "actual_field_access_proven": False,
                "is_safe_patch_site": False,
            })
            if scanned % 100000 == 0:
                monitor_obj.setMessage("BSC queue-field scout scanned %d decoded instructions" % scanned)
        if truncated:
            break
    return records, scanned, truncated


def main():
    settings = args_map(getScriptArgs())
    exe = settings["exe"]
    if not os.path.isfile(exe):
        raise ValueError("EXE file not found: %s" % exe)
    sha, md5, size = file_hashes(exe)
    if sha.lower() != settings["expected-sha256"].lower():
        raise ValueError("EXE SHA256 mismatch: refusing cross-build analysis")
    imported_md5 = currentProgram.getExecutableMD5()
    if not imported_md5 or str(imported_md5).lower() != md5.lower():
        raise ValueError("Ghidra import MD5 differs from requested EXE: refusing report")
    if currentProgram.getDefaultPointerSize() != 8:
        raise ValueError("Ghidra project is not 64-bit")
    entries, scanned, truncated = collect(currentProgram, monitor)
    doc = {
        "schema": "bsc.native_shift_ghidra_order_xrefs.v1",
        "research_build": "9.0.3",
        "exe_sha256": sha,
        "exe_md5": md5,
        "exe_size_bytes": size,
        "ghidra_import_md5_verified": True,
        "program": str(currentProgram.getName()),
        "image_base": str(currentProgram.getImageBase()),
        "decoded_instructions_scanned": scanned,
        "results_truncated": truncated,
        "status": "PARTIAL_CANDIDATE_EXPORT" if truncated else "COMPLETE_SCOUT_CANDIDATE_EXPORT",
        "candidates": entries,
        "note": "Only scalar-operand offset matches. No root-object provenance, no ABI, no proven OrderHead writer/queue progression. Optimized aliases may not match scalar offsets.",
        "patch_authorized": False,
    }
    output = settings["output"]
    if os.path.realpath(output) == os.path.realpath(exe):
        raise ValueError("refusing to overwrite input executable")
    parent = os.path.dirname(os.path.abspath(output))
    if not os.path.isdir(parent):
        os.makedirs(parent)
    with open(output, "w") as handle:
        json.dump(doc, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("BSC Ghidra xref candidates: %d in %d decoded instructions; %s" %
          (len(entries), scanned, output))


# Ghidra executes the script at top level with currentProgram/getScriptArgs/monitor.
# Importing for tests is not supported outside Ghidra.
main()
