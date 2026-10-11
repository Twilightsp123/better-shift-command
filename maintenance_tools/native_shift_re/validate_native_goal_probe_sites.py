#!/usr/bin/env python3
"""Refuse native trace hooks in the middle of an x64 instruction.

Strict original EXE SHA, all JS pin bytes, PE unwind function ownership and
objdump instruction starts must match. Read-only, static: NOT WH3 gameplay.
"""
import argparse
import json
import re
import shutil
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE, EXPECTED_SHA

PIN=re.compile(r'\[0x([0-9a-fA-F]+),\s*[\x27\x22]([0-9a-fA-F]+)[\x27\x22]\]')

def parse_probe(path):
    text=Path(path).read_text(encoding='utf-8')
    matches=list(PIN.finditer(text))
    if len(matches)<6:raise ValueError('PROBE_HAS_TOO_FEW_GUARDS')
    pins={}
    for m in matches:
        site=int(m.group(1),16)
        if site in pins:raise ValueError('DUPLICATE_HOOK_SITE:'+hex(site))
        pins[site]=m.group(2).lower()
    return pins

def starts_from_asm(asm):
    starts=set()
    for line in asm.splitlines():
        m=re.match(r'^\s*([0-9a-f]+):\s+(.+)$',line)
        if not m:continue
        fields=m.group(2).split('\t')
        # Wrapped disassembly byte continuations are NOT instruction starts.
        if len(fields)>=2 and re.match(r'^\s*[a-z][a-z0-9_.]*\b',fields[-1]):
            starts.add(int(m.group(1),16))
    return starts

def audit(exe,probe):
    if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
    pins=parse_probe(probe)
    pe=StrictPE(exe)  # hash and ImageBase are pinned by existing auditor
    try:
        if pe.sha!=EXPECTED_SHA:raise ValueError('WRONG_SHA')
        checked=[];cache={}
        for site,expected in sorted(pins.items()):
            got=pe.read(site,len(expected)//2,True).hex()
            if got!=expected:
                raise ValueError(f'OPCODE_MISMATCH:{site:#x}:got={got}:want={expected}')
            owner=pe.function(site)
            if owner is None:raise ValueError('NO_PE_UNWIND_OWNER:'+hex(site))
            if owner not in cache:
                cache[owner]=starts_from_asm(pe.disasm(owner[0],owner[1]-owner[0]))
            if site not in cache[owner]:
                raise ValueError('NOT_X64_INSTRUCTION_BOUNDARY:'+hex(site))
            checked.append({'rva':hex(site),'bytes':expected,'owner_rva':hex(owner[0])})
        return {'schema':'bsc.n1.native_hook_site_guard.v1',
                'exe_sha256':pe.sha,'pin_count':len(checked),'checked':checked,
                'grade':'EXACT_EXE_STATIC_OPCODE_AND_BOUNDARY',
                'windows_frida_attach_tested':False,'native_fix_authorized':False}
    finally:pe.close()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--probe',type=Path,default=Path(__file__).with_name('one_shot_goal_branch_v2.js'))
    ap.add_argument('--out',type=Path)
    a=ap.parse_args()
    if a.out and a.out.resolve()==a.exe.resolve():ap.error('NO_EXE_OVERWRITE')
    try:
        result=audit(a.exe,a.probe)
        if a.out:
            a.out.parent.mkdir(parents=True,exist_ok=True)
            a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print('PASS',result['pin_count'],'original opcode guards AND instruction boundaries')
    except (ValueError,OSError) as e:
        print('PROBE_SITE_REFUSED:',e)
        return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
