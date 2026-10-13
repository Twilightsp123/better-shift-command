#!/usr/bin/env python3
"""Exact WH3 9.0.3 third-handler constructor postcall audit (read-only).

For 16 typed constructor sites, checks the bounded path to virtual+8.
It does NOT claim other callbacks cannot write object+0x88, nor identify
this object with MOVE slot+0xA0. No original EXE or pointer logs are stored.
"""
import argparse, json, re, shutil, struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE
from audit_third_handler_type_lineage import CONSTRUCTOR_CALL_SITES

ORIGINAL_SHA = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
VTABLE = 0x03ADE428
VTABLE_PLUS_8 = VTABLE + 8
EMPTY_METHOD = 0x008D3280
POSTCALL_V8 = {
    0x030D3011: (0x030D3023, '48ff6008'),
    0x030D312D: (0x030D313F, '48ff6008'),
    0x030D3379: (0x030D33A0, '48ff6008'),
    0x030DCCE7: (0x030DCCF7, 'ff5008'),
    0x03275385: (0x032753AE, '48ff6008'),
    0x03275549: (0x03275557, 'ff5008'),
    0x032756AB: (0x032756B9, 'ff5008'),
    0x03275815: (0x03275832, '48ff6008'),
    0x03275943: (0x0327595B, '48ff6008'),
    0x03275A86: (0x03275A99, '48ff6008'),
    0x03275BD6: (0x03275BE9, '48ff6008'),
    0x03275CDF: (0x03275CF1, '48ff6008'),
    0x03275E08: (0x03275E1B, '48ff6008'),
    0x03275F38: (0x03275F4B, '48ff6008'),
    0x03276279: (0x0327629E, '48ff6008'),
    0x032830AD: (0x032830BB, 'ff5008'),
}
DTOR_PINS = {
    0x03266FD1:'488d0550748700',
    0x03266FDB:'488d053e758700',
    0x03266FED:'488b8b98000000',
    0x03267024:'488b8b80000000',
}
LINE_RE = re.compile(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+(.+)$')

def decoded_lines(pe, start, end):
    rows = []
    for line in pe.disasm(start, end-start).splitlines():
        match = LINE_RE.match(line)
        if match:
            rows.append((int(match.group(1), 16), match.group(2)))
    return rows

def verify(pe):
    if pe.sha != ORIGINAL_SHA:
        raise ValueError('SHA_MISMATCH')
    if not shutil.which('objdump'):
        raise ValueError('OBJDUMP_REQUIRED')
    if set(POSTCALL_V8) != set(CONSTRUCTOR_CALL_SITES) or len(POSTCALL_V8) != 16:
        raise ValueError('CONSTRUCTOR_COVERAGE_DRIFT')
    target = struct.unpack('<Q', pe.read(VTABLE_PLUS_8, 8))[0]
    if target != pe.base + EMPTY_METHOD:
        raise ValueError('VTABLE_PLUS8_NO_LONGER_EMPTY:'+hex(target))
    if pe.read(EMPTY_METHOD, 3, True) != bytes.fromhex('c20000'):
        raise ValueError('VIRTUAL_PLUS8_METHOD_CHANGED')
    findings = []
    jumps = 0
    calls = 0
    for ctor_site, (dispatch_site, guard) in POSTCALL_V8.items():
        owner = pe.function(ctor_site)
        if owner is None or pe.function(dispatch_site) != owner:
            raise ValueError('DIFFERENT_FUNCTION_OWNER:'+hex(ctor_site))
        rows = decoded_lines(pe, *owner)
        starts = {site for site, _ in rows}
        if ctor_site not in starts or dispatch_site not in starts:
            raise ValueError('NOT_DECODED_INSTRUCTION_START:'+hex(ctor_site))
        code = pe.read(ctor_site, 5, True)
        if code[0] != 0xE8 or ctor_site + 5 + struct.unpack_from('<i', code, 1)[0] != 0x0326581C:
            raise ValueError('CONSTRUCTOR_CALL_DRIFT:'+hex(ctor_site))
        if pe.read(dispatch_site, len(guard)//2, True).hex() != guard:
            raise ValueError('VIRTUAL_PLUS8_CALL_DRIFT:'+hex(dispatch_site))
        if dispatch_site <= ctor_site:
            raise ValueError('WRONG_CALL_ORDER:'+hex(ctor_site))
        span = [(addr, text) for addr, text in rows if ctor_site < addr <= dispatch_site]
        if not span or span[-1][0] != dispatch_site:
            raise ValueError('MISSING_POSTCALL_SEGMENT:'+hex(ctor_site))
        # Scoped negative only. This cannot exclude writes via alias/callee.
        if any(re.search(r'\+0x88\]', text) for _, text in span):
            raise ValueError('POSTCALL_PLUS88_OPERAND:'+hex(ctor_site))
        if not any(re.search(r'mov\s+rax,QWORD PTR \[(?:rbx|rsi|rcx|r9|r10)\]', text) for _, text in span):
            raise ValueError('UNVERIFIED_VTABLE_SOURCE:'+hex(ctor_site))
        if 'jmp ' in span[-1][1]:
            jumps += 1
            kind = 'tailjmp'
        elif 'call ' in span[-1][1]:
            calls += 1
            kind = 'call'
        else:
            raise ValueError('NOT_VIRTUAL_DISPATCH:'+hex(dispatch_site))
        findings.append({
            'constructor_call_site':f'0x{ctor_site:08X}',
            'virtual_plus_8_site':f'0x{dispatch_site:08X}',
            'function_owner':f'0x{owner[0]:08X}',
            'dispatch_kind':kind,
        })
    dtor_owner = pe.function(0x03266FC0)
    if dtor_owner is None:
        raise ValueError('DESTRUCTOR_UNWIND_MISSING')
    dtor_rows = decoded_lines(pe, *dtor_owner)
    dtor_starts = {site for site, _ in dtor_rows}
    for site, hexcode in DTOR_PINS.items():
        if site not in dtor_starts or pe.read(site, len(hexcode)//2, True).hex() != hexcode:
            raise ValueError('DESTRUCTOR_OPCODE_OR_BOUNDARY_DRIFT:'+hex(site))
    if any(re.search(r'\+0x88\]', text) for _, text in dtor_rows):
        raise ValueError('DESTRUCTOR_PLUS88_OPERAND_ADDED')
    return {
        'schema':'bsc.n1.third_handler_postconstructor_virtual8.v1',
        'exe_sha256':pe.sha,
        'proof_grade':'EXACT_ORIGINAL_EXE_STATIC',
        'constructor_call_sites':len(findings),
        'post_ctor_virtual_plus_8_dispatches':len(findings),
        'tail_jumps':jumps, 'direct_calls':calls,
        'vtable_plus_8_method':'0x008D3280',
        'vtable_plus_8_bytes':'c2 00 00 (ret 0)',
        'checked_destructor_opcodes':len(DTOR_PINS),
        'post_ctor_plus88_direct_accesses_in_scoped_spans':0,
        'destructor_plus88_direct_accesses':0,
        'postcall_sites':findings,
        'other_paths_may_write_plus88':True,
        'MOVE_slot_plus_A0_pointer_alias_proven':False,
        'native_patch_authorized':False,
    }

def audit(exe):
    pe = StrictPE(Path(exe))
    try:
        return verify(pe)
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
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf8')
    print('PASS', result['post_ctor_virtual_plus_8_dispatches'],
          'typed post-ctor dispatches;', result['checked_destructor_opcodes'],
          'destructor pins; NO GAME PATCH')

if __name__ == '__main__':
    main()
