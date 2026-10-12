#!/usr/bin/env python3
"""Exact original WH3 member-packet constructors: bounded direct-E8 xrefs.

All executable sections; only call instructions verified by owner-function
objdump boundaries. Bounded 180-byte *same native function* signature match
DOES NOT prove runtime execution, uniquely identify an indirect caller,
or authorize a Native Patch.
"""
import argparse
import json
import re
import struct
from pathlib import Path

from audit_wh3_full_native_chain import StrictPE

CONSTRUCTORS={
 0x02F5F8DC:"generic_packet_ctor",
 0x02F5F868:"A_packet_ctor",
 0x02F5F964:"alternate_packet_ctor",
}
SIGNATURE=[
 ("clear_packet51_bit0",bytes.fromhex("806531fe")),
 ("clear_packet50_bit2",bytes.fromhex("24fb")),
 ("zero_packet44_low_dword",bytes.fromhex("894d24")),
 ("member_v368_dispatch",bytes.fromhex("ff9068030000")),
]

def bounded_signature_offsets(buf):
    offsets={name:buf.find(pat) for name,pat in SIGNATURE}
    ordered=(all(v>=0 for v in offsets.values()) and
             all(offsets[SIGNATURE[i][0]]<offsets[SIGNATURE[i+1][0]]
                 for i in range(len(SIGNATURE)-1)))
    return ordered,{k:(v if v>=0 else None) for k,v in offsets.items()}

def audit(exe):
    pe=StrictPE(exe)  # SHA256, x64 PE, image base and read-only mmap
    try:
        candidates=[]
        for _name,start,raw_size,_offset,_virtual,flags in pe.sections:
            if not(flags&0x20000000) or not raw_size:continue
            code=pe.read(start,raw_size,True)
            i=0
            while (i:=code.find(b"\xe8",i))>=0:
                if i+5>len(code):break
                site=start+i
                target=site+5+struct.unpack_from("<i",code,i+1)[0]
                i+=1
                if target not in CONSTRUCTORS:continue
                span=pe.function(site)
                if not span:continue
                candidates.append((site,target,span))
        cache={};confirmed=[]
        for site,target,owner in candidates:
            if owner not in cache:
                asm=pe.disasm(owner[0],owner[1]-owner[0])
                starts=set()
                for line in asm.splitlines():
                    match=re.match(r"^\s*([0-9a-f]+):\s+.*\tcall\s+",line)
                    if match:starts.add(int(match.group(1),16))
                cache[owner]=starts
            if site not in cache[owner]:continue
            remaining=owner[1]-site
            ordered,offsets=bounded_signature_offsets(
                pe.read(site,min(180,remaining),True))
            confirmed.append({
             "site":hex(site),"target":hex(target),"owner_function":hex(owner[0]),
             "bounded_same_function_signature":ordered,
             "relative_offsets":offsets,
            })
        counts={hex(k):sum(int(x["target"]==hex(k)) for x in confirmed)
                for k in CONSTRUCTORS}
        matches=[x for x in confirmed if
                 x["target"]==hex(0x02F5F8DC) and x["bounded_same_function_signature"]]
        return {
          "schema":"bsc.n1.native_packet_constructor_bounded_xrefs.v1",
          "exe_sha256":pe.sha,"grade":"EXACT_EXE_STATIC_XREF_ONLY",
          "verified_all_native_constructor_E8":len(confirmed),
          "constructor_groups":counts,
          "generic_ctor_post_rewrite_4_stage_signature_count":len(matches),
          "signature_matches":matches,
          "candidate_callsites":confirmed,
          "runtime_caller_in_historical_trace":None,
          "safe_native_patch_authorized":False,
          "scope_note":"Only direct E8, only within 180 bytes of each original call inside its unwind-owned function; virtual or longer-distance producers not exhausted.",
        }
    finally:pe.close()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    if a.exe.resolve()==a.out.resolve():ap.error("NEVER_OVERWRITE_EXE")
    report=audit(a.exe)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("EXACT STATIC PASS",report["verified_all_native_constructor_E8"],
          "E8 ctor callers,",report["generic_ctor_post_rewrite_4_stage_signature_count"],
          "bounded rewrites; NO NATIVE PATCH")

if __name__=="__main__":main()
