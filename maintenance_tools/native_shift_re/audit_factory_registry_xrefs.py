#!/usr/bin/env python3
"""Read-only reverse xrefs for exact WH3 9.0.3 handler registration families.

Finds executable RIP-relative references and aligned static data pointers.
Static xrefs alone never establish MOVE-task identity or RMB/Shift ownership.
Does not write to or hook a game process. No original EXE is distributed.
"""
import argparse
import json
import re
import struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE
import audit_two_handler_factory_origins as factory

TARGETS = {
    0x03D19A88: "A registry pointer location",
    0x03D19C08: "type-check registry candidate (identity unproven)",
    0x03D19C10: "B registry pointer location",
    0x03940ED8: "A descriptor start",
    0x03940EE0: "A descriptor factory callback",
    0x03941400: "B descriptor start",
    0x03941408: "B descriptor factory callback",
    0x039156F8: "A instantiated handler vtable",
    0x03915830: "B instantiated handler vtable",
    0x0390B4F0: "MOVE slot vtable (separate object type)",
}

# Only Mod=0, R/M=5 RIP+disp32 on specified one-byte opcodes.
# This is an explicitly incomplete encoder family, never an exhaustive xref.
RIP_PATTERN = re.compile(
    rb'(?:[\x40-\x4f])?[\x8d\x8b\x89\x39\x3b\xff\x8a\x88]'
    rb'[\x05\x0d\x15\x1d\x25\x2d\x35\x3d][\x00-\xff]{4}', re.DOTALL)
TYPE_PREDICATE_LEAS = {
    0x0327711C: 0x03D19C08,
    0x03277129: 0x03D19C10,
    0x03277168: 0x03D19A88,
    0x03277224: 0x03D19A88,
}

def decode_rip_site(code, site):
    """Return (target RVA, length) for supported encoding; otherwise None."""
    if not RIP_PATTERN.fullmatch(code):
        return None
    disp_at = 3 if 0x40 <= code[0] <= 0x4F else 2
    return site + len(code) + struct.unpack_from('<i', code, disp_at)[0], len(code)

def raw_candidates(pe):
    """Candidate bytes; not yet verified as whole instructions."""
    for name, rva, rawsize, offset, virtual_size, flags in pe.sections:
        if not flags & 0x20000000:
            continue
        data = pe.read(rva, rawsize, True)
        for match in RIP_PATTERN.finditer(data):
            site = rva + match.start()
            decoded = decode_rip_site(match.group(), site)
            if decoded is not None and decoded[0] in TARGETS:
                yield site, decoded[0], match.group().hex()

def instruction_index(pe, owner, cache):
    if owner not in cache:
        asm = pe.disasm(owner[0], owner[1] - owner[0])
        starts = {}
        for line in asm.splitlines():
            match = re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+', line)
            if match:
                starts[int(match.group(1), 16)] = line.strip()
        cache[owner] = starts
    return cache[owner]

def code_xrefs(pe):
    cache = {}
    found = []
    for site, target, raw in raw_candidates(pe):
        owner = pe.function(site)
        if owner is None:
            # Unwind-free leaves require independently established bounds.
            continue
        instruction = instruction_index(pe, owner, cache).get(site)
        if instruction is None:
            continue
        found.append(dict(site=f'0x{site:08X}', owner=f'0x{owner[0]:08X}',
                          target=f'0x{target:08X}', target_label=TARGETS[target],
                          bytes=raw, instruction=instruction,
                          evidence='valid instruction RIP reference; no object identity'))
    return sorted(found, key=lambda x: (x['target'], x['site']))

def pointer_xrefs(pe):
    found = []
    va_to_rva = {pe.base + rva: rva for rva in TARGETS}
    for name, rva, rawsize, offset, virtual_size, flags in pe.sections:
        if flags & 0x20000000:
            continue
        data = pe.read(rva, rawsize)
        for index in range((-rva) % 8, rawsize - 7, 8):
            target = va_to_rva.get(struct.unpack_from('<Q', data, index)[0])
            if target is not None:
                found.append(dict(site=f'0x{rva+index:08X}',
                                  target=f'0x{target:08X}', target_label=TARGETS[target],
                                  section=name, evidence='aligned static pointer; consumer unproven'))
    return sorted(found, key=lambda x: (x['target'], x['site']))

def verify_predicate_targets(pe):
    cache = {}
    for site, expected in TYPE_PREDICATE_LEAS.items():
        pinned = bytes.fromhex(factory.PINS[site])
        if pe.read(site, len(pinned), True) != pinned:
            raise ValueError(f'TYPE_PREDICATE_OPCODE_CHANGED:0x{site:08X}')
        decoded = decode_rip_site(pinned, site)
        if decoded is None or decoded[0] != expected:
            raise ValueError(f'TYPE_PREDICATE_RIP_TARGET_CHANGED:0x{site:08X}')
        owner = pe.function(site)
        if owner is None or site not in instruction_index(pe, owner, cache):
            raise ValueError(f'TYPE_PREDICATE_MID_INSTRUCTION:0x{site:08X}')
    return len(TYPE_PREDICATE_LEAS)

def audit(exe):
    pe = StrictPE(Path(exe))  # exact SHA, PE x64, base and section constraints
    try:
        factory.audit(exe)   # prerequisite typed callback and factory guard
        count = verify_predicate_targets(pe)
        code, pointers = code_xrefs(pe), pointer_xrefs(pe)
        return dict(
            schema='bsc.n1.factory_registry_reverse_xrefs.v1',
            original_exe_sha256=pe.sha, level='EXACT_EXE_STATIC_XREF',
            checked_predicate_lea_targets=count,
            rip_relative_code_xrefs=code, aligned_static_pointer_xrefs=pointers,
            code_xref_count=len(code), pointer_xref_count=len(pointers),
            exact_parent_to_MOVE_task_identity=False,
            player_RMB_or_Shift_to_factory_identity=False,
            native_patch_authorized=False,
            limitations=[
                'RIP decoder covers a subset, not an exhaustive disassembly',
                'Static code xref does not prove call execution or object alias',
                'Data pointers do not prove virtual dispatch',
                'No original EXE or runtime pointer logs are included'])
    finally:
        pe.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.exe.resolve() == args.out.resolve():
        parser.error('NEVER_OVERWRITE_EXE')
    result = audit(args.exe)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n',
                        encoding='utf8')
    print('PASS static xrefs', result['code_xref_count'], 'code',
          result['pointer_xref_count'], 'data; NOT MOVE identity or patch')

if __name__ == '__main__':
    main()
