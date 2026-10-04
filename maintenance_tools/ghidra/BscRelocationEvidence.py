# Ghidra headless post-script: export exact function/callgraph evidence for BSC.
# Arguments: <unresolved.json> <output.json>
# Kept Jython-compatible on purpose: no f-strings/type annotations/pathlib.

import json
from ghidra.program.model.block import BasicBlockModel

args = getScriptArgs()
if len(args) < 2:
    raise Exception("expected unresolved.json and output.json")
input_path = args[0]
output_path = args[1]

with open(input_path, "r") as f:
    payload = json.load(f)

base_addr = currentProgram.getImageBase()
base = base_addr.getOffset()
fm = currentProgram.getFunctionManager()
listing = currentProgram.getListing()
blocks = BasicBlockModel(currentProgram)


def rva(addr):
    if addr is None:
        return None
    return int(addr.getOffset() - base)


def hx(value):
    if value is None:
        return None
    return "0x%08X" % (value & 0xffffffffffffffff)


def function_evidence(site_rva):
    addr = toAddr(base + site_rva)
    fn = fm.getFunctionContaining(addr)
    if fn is None:
        fn = fm.getFunctionAt(addr)
    if fn is None:
        return {
            "site_rva": hx(site_rva),
            "function_found": False,
        }

    entry = fn.getEntryPoint()
    body = fn.getBody()
    calls = []
    mnemonics = {}
    instruction_count = 0
    it = listing.getInstructions(body, True)
    while it.hasNext():
        ins = it.next()
        instruction_count += 1
        mnem = str(ins.getMnemonicString())
        mnemonics[mnem] = mnemonics.get(mnem, 0) + 1
        try:
            if ins.getFlowType().isCall():
                flows = ins.getFlows()
                for target in flows:
                    calls.append({
                        "site_offset": int(ins.getAddress().getOffset() - entry.getOffset()),
                        "call_rva": hx(rva(ins.getAddress())),
                        "target_rva": hx(rva(target)),
                    })
        except Exception:
            pass

    caller_rvas = []
    callee_rvas = []
    try:
        for other in fn.getCallingFunctions(monitor):
            caller_rvas.append(hx(rva(other.getEntryPoint())))
    except Exception:
        pass
    try:
        for other in fn.getCalledFunctions(monitor):
            callee_rvas.append(hx(rva(other.getEntryPoint())))
    except Exception:
        pass

    block_count = 0
    edge_count = 0
    try:
        bit = blocks.getCodeBlocksContaining(body, monitor)
        while bit.hasNext():
            block = bit.next()
            block_count += 1
            try:
                edge_count += int(block.getNumDestinations(monitor))
            except Exception:
                pass
    except Exception:
        block_count = -1
        edge_count = -1

    return {
        "site_rva": hx(site_rva),
        "function_found": True,
        "function_name": str(fn.getName(True)),
        "entry_rva": hx(rva(entry)),
        "site_offset": int((base + site_rva) - entry.getOffset()),
        "body_min_rva": hx(rva(body.getMinAddress())),
        "body_max_rva": hx(rva(body.getMaxAddress())),
        "instruction_count": instruction_count,
        "basic_block_count": block_count,
        "flow_edge_count": edge_count,
        "mnemonic_histogram": mnemonics,
        "direct_calls": calls,
        "callers": sorted(set(caller_rvas)),
        "callees": sorted(set(callee_rvas)),
    }


def label(addr, name):
    try:
        createLabel(addr, name, True)
    except Exception:
        pass


def add_record(records, key, site_rva, label_name):
    addr = toAddr(base + site_rva)
    label(addr, label_name)
    records[key] = function_evidence(site_rva)


records = {}
resolved = payload.get("resolved_core", {})
for name, text_rva in resolved.items():
    if not text_rva:
        continue
    value = int(text_rva, 16)
    add_record(records, "anchor:" + name, value, "BSC_anchor_" + name)

for site, item in payload.get("sites", {}).items():
    for idx, candidate in enumerate(item.get("candidates", []), 1):
        value = int(candidate["rva"], 16)
        add_record(
            records,
            "candidate:%s:%d" % (site, idx),
            value,
            "BSC_candidate_%s_%d" % (site, idx),
        )

    # When Stage 6 has no byte candidate, enumerate functions near the projected
    # location. This is evidence only; no automatic address promotion occurs here.
    window = item.get("search_window")
    if item.get("candidates") or not window:
        continue
    start = int(window["start_rva"], 16)
    end = int(window["end_rva"], 16)
    projected = int(window["projected_rva"], 16)
    found = []
    try:
        fit = fm.getFunctions(toAddr(base + start), True)
        while fit.hasNext():
            fn = fit.next()
            er = rva(fn.getEntryPoint())
            if er is None or er > end:
                break
            if er >= start:
                found.append((abs(er - projected), er))
    except Exception:
        found = []
    found.sort()
    for idx, pair in enumerate(found[:64], 1):
        value = pair[1]
        add_record(
            records,
            "window:%s:%d" % (site, idx),
            value,
            "BSC_window_%s_%d" % (site, idx),
        )

try:
    exe_sha = str(currentProgram.getExecutableSHA256())
except Exception:
    exe_sha = None

out = {
    "schema": 1,
    "tool": "BscRelocationEvidence",
    "program": str(currentProgram.getName()),
    "image_base": hx(base),
    "exe_sha256": exe_sha,
    "records": records,
}
with open(output_path, "w") as f:
    json.dump(out, f, indent=2, sort_keys=True)
    f.write("\n")
print("BSC Ghidra evidence records: %d" % len(records))
