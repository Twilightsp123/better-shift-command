#!/usr/bin/env python3
"""SHA-gated WH3 9.0.3 layout-vs-waypoint static evidence; no game writes."""
import argparse, json, mmap, struct
from pathlib import Path
from audit_903_formation_entry import TARGET_SHA256, digest_file, pe_sections, read_executable

BASE=0x140000000
GUARDS="""
30d54a2 4c8b99300b0000
30d54ca 41ff5248
30d54d0 397724
30d54d9 4c8d0476
30d550f ff9068030000
30d5522 ff5020
302bc48 488b5118
302bc5d 488b88300b0000
302bc67 4c8b4820
302bc72 f30f104840
302bca2 4439b7b8000000
302bdc4 4489b7b8000000
302bdf1 83606cfe
8f7750 418bc00f57c00f57c9f3480f2ac0f30f51c8f3480f2cc1c3
30d1a08 b80d000000443bc0410f46c0c3
8f7770 488b05f1a06603418bc88b0488ffc0c3
30d19a4 f30f580d08b48400b801000000f30f5c4910f30f5e4918f3480f2cd1ffc23bd00f43c2413bc0440f42c0443b4130440f434130418bc0c3
30d1a18 4883ec28418bd0e820c400008b004883c428c3
306bad7 8b8704010000ffc8f30f1155c083f801f30f1145c4f30f114dc8
306bb0e 41ff9300010000
306bb44 41ff93e8000000
315f52c f20f118788000000
315f53e 898790000000
315f54c 66899fb0000000
3056f28 4c8b8b30090000
3056fb7 48898330090000
"""
STRATEGIES=[
 (0x30c2e9b,0x390f4b8,0x30d19a4,0x30c9b3c),
 (0x30c7daa,0x390f0c8,0x30d1a18,0x30cad9c),
 (0x30c7e1e,0x390f180,0x8f7750,0x30ca218),
 (0x30c7e47,0x390f388,0x8f7700,0x30c9c44),
 (0x30c7ef5,0x390f558,0x305ffdc,0x30c9a64),
 (0x30c7ff8,0x390f030,0x8f7780,0x30cafcc),
 (0x30c8027,0x390f218,0x30d1a08,0x30ca140),
 (0x30c8056,0x390ef98,0x8f7770,0x30caf04),
]
GROUP_VTABLE=0x390f5f0
GROUP_AFTER_FANOUT=0x30e0aa8

def read_any(mm,sec,rva,n):
    for name,start,size,raw,executable in sec:
        if start<=rva and rva+n<=start+size:
            return bytes(mm[raw+rva-start:raw+rva-start+n])
    raise ValueError("RVA_UNMAPPED")

def qword(mm,sec,rva):
    return struct.unpack("<Q",read_any(mm,sec,rva,8))[0]

def verify(exe):
    sha=digest_file(exe)
    if sha!=TARGET_SHA256:raise ValueError("EXE_SHA256_MISMATCH")
    with exe.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        sec=pe_sections(mm)
        for line in GUARDS.strip().splitlines():
            addr,hx=line.split()
            expected=bytes.fromhex(hx)
            if read_executable(mm,sec,int(addr,16),len(expected))!=expected:
                raise ValueError("BAD_GUARD_"+addr)
        out=[]
        for ctor,vt,fn20,fn48 in STRATEGIES:
            ins=read_executable(mm,sec,ctor,7)
            if ins[:3] not in (b"\x48\x8d\x05",b"\x48\x8d\x0d",b"\x4c\x8d\x05"):
                raise ValueError("WRONG_LEA_"+hex(ctor))
            if ctor+7+struct.unpack("<i",ins[3:])[0]!=vt:
                raise ValueError("BAD_CTOR_REF")
            if qword(mm,sec,vt+0x20)-BASE!=fn20:
                raise ValueError("BAD_LAYOUT_METHOD")
            if qword(mm,sec,vt+0x48)-BASE!=fn48:
                raise ValueError("BAD_GROUP_GENERATOR")
            read_executable(mm,sec,fn20,1)
            read_executable(mm,sec,fn48,1)
            out.append({"vtable":hex(vt),"layout_count_method":hex(fn20),
                        "member_generator":hex(fn48)})
        grouppost=qword(mm,sec,GROUP_VTABLE+0x20)-BASE
        if grouppost!=GROUP_AFTER_FANOUT:
            raise ValueError("GROUP_TYPE_CONFUSION")
        read_executable(mm,sec,grouppost,1)
    return {
      "sha256":sha,"exact_opcode_guards":len(GUARDS.strip().splitlines()),
      "verified_strategy_tables":out,"distinct_group_postprocess":hex(grouppost),
      "conclusion":"Strategy +0x20 returns integer formation layout cardinality computed from member count/route scalar; it is not proven to be member waypoint arrival. Strategy +0x48 generates member payloads once before group fanout. Member +0x104 selects two action paths.",
      "unknown":["real per-model route-leg advancement",
                 "effect of slot geometry/steering on observed crowding",
                 "safe Win64 patch ABI and original movement-phase predicate"],
      "patch_authorized":False}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.exe.resolve()==a.out.resolve():p.error("refusing to overwrite EXE")
    result=verify(a.exe)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("STATIC",result["exact_opcode_guards"],"guards and",
          len(result["verified_strategy_tables"]),"strategies PASS; no runtime patch")
