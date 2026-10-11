#!/usr/bin/env python3
"""Native WH3 directional goal gate, exact-build read-only audit.

Original motor goal member+0x1E0 is decoded by 0x03115C94. The result
(dot((targetX-X,targetZ-Z),heading) < 0) is consumed in 0x03256180.
This is a conditional STATIC dataflow proof, NOT a V3 execution or patch.
"""
import argparse
import hashlib
import json
import math
import mmap
from pathlib import Path
import struct

SHA="518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
BASE=0x140000000
GUARDS={
 0x03115C98:"f6818801000002",
 0x03115CAB:"80b98f01000000",
 0x03115CB4:"f30f10b988000000",
 0x03115CBC:"4c8d89e0010000",
 0x03115CC3:"f30f10b190000000",
 0x03115CD3:"e8fc710000",
 0x03115CE3:"e8e877feff",
 0x03115CFA:"f3410f1002",
 0x03115CFF:"f30f5cce",
 0x03115D03:"f30f5cc7",
 0x03115D07:"f30f594cc804",
 0x03115D0D:"f30f5904c8",
 0x03115D12:"f30f58c8",
 0x03115D16:"0f2f0da36e8000",
 0x03115D1D:"7304",
 0x03115D1F:"b001",
 0x03115D23:"32c0",
 0x032561E4:"488b4908",
 0x032561E8:"8b9110070000",
 0x032561F0:"0f848a000000",
 0x03256204:"e88bfaebff",
 0x03256209:"84c0",
 0x0325620B:"0f845d010000",
 0x03119556:"80b92802000001",
 0x0311963A:"0f1187e0010000",
 0x0306BA5B:"e8683defff",
 0x0306BA60:"e975010000",
 0x03265D3F:"ff9068030000",
 0x0304459D:"ff4618",
}
CALLS={0x03115CD3:0x0311CED4,0x03115CE3:0x030FD4D0,
       0x03256204:0x03115C94,0x0306BA5B:0x02F5F7C8}
CONSTANTS={0x0391CBC0:0.0}

def goal_behind(member_xz,target_xz,heading_xz,guards_enabled=True):
    if not guards_enabled:return False
    x,z=member_xz;tx,tz=target_xz;dx,dz=heading_xz
    if not all(math.isfinite(v) for v in (x,z,tx,tz,dx,dz)):
        raise ValueError("NONFINITE")
    return (tx-x)*dx+(tz-z)*dz<0

def action_branch_conditional(member710,bit188,member18f,behind):
    if not bit188 or member18f!=0:return False
    if member710 in (0,6,7):return True
    return behind

class ExactPE:
    def __init__(self,path):
        self.path=Path(path)
        with self.path.open("rb") as f:
            if hashlib.file_digest(f,"sha256").hexdigest()!=SHA:
                raise ValueError("SHA_MISMATCH")
        self.fd=self.path.open("rb")
        self.mm=mmap.mmap(self.fd.fileno(),0,access=mmap.ACCESS_READ)
        m=self.mm
        if m[:2]!=b"MZ":raise ValueError("INVALID_MZ")
        nt=struct.unpack_from("<I",m,0x3c)[0]
        if m[nt:nt+4]!=b"PE\x00\x00":raise ValueError("INVALID_PE")
        machine,count=struct.unpack_from("<HH",m,nt+4)
        if machine!=0x8664:raise ValueError("INVALID_MACHINE")
        opt=nt+24
        if struct.unpack_from("<Q",m,opt+24)[0]!=BASE:
            raise ValueError("INVALID_IMAGE_BASE")
        optsize=struct.unpack_from("<H",m,nt+20)[0]
        self.sections=[]
        for i in range(count):
            pos=opt+optsize+40*i
            vs,start,size,off=struct.unpack_from("<IIII",m,pos+8)
            flags=struct.unpack_from("<I",m,pos+36)[0]
            self.sections.append((start,size,off,flags))
    def read(self,rva,n,code=False):
        for start,size,off,flags in self.sections:
            if start<=rva and rva+n<=start+size:
                if code and not flags&0x20000000:raise ValueError("NON_CODE_RVA")
                return bytes(self.mm[off+rva-start:off+rva-start+n])
        raise ValueError("UNMAPPED_RVA")
    def close(self):self.mm.close();self.fd.close()

def verify(exe):
    pe=ExactPE(exe)
    try:
        for rva,expected in GUARDS.items():
            if pe.read(rva,len(expected)//2,True).hex()!=expected:
                raise ValueError("ORIGINAL_OPCODE_MISMATCH:"+hex(rva))
        for rva,target in CALLS.items():
            raw=pe.read(rva,5,True)
            if raw[0]!=0xe8 or rva+5+struct.unpack_from("<i",raw,1)[0]!=target:
                raise ValueError("ORIGINAL_CALL_TARGET_CHANGED:"+hex(rva))
        for rva,expected in CONSTANTS.items():
            if struct.unpack("<f",pe.read(rva,4))[0]!=expected:
                raise ValueError("ORIGINAL_CONSTANT_CHANGED")
        return {
          "schema":"bsc.n1.directional_goal_gate.v1",
          "sha256":SHA,"grade":"EXACT_EXE_STATIC_ONLY",
          "machine_guards":len(GUARDS),"native_calls":len(CALLS),
          "checked_float_constants":len(CONSTANTS),
          "goal_reader":"member+0x1E0 -> 0x03115C94 -> 0x03256209 AL",
          "predicate":"dot(goalXYZ-memberXYZ, current native goal heading) < 0",
          "branch":"AL=0 at 0x0325620B skips to 0x0325636E",
          "counterexample":{"old_ahead":goal_behind((0,0),(4,0),(1,0)),
            "new_behind":goal_behind((0,0),(-4,0),(1,0))},
          "caveat":"native heading LUT 0x03E882A0 is zero-filled on disk and runtime-initialized",
          "V3_branch_hit":False,"route_incompatibility_proven":False,
          "physical_collision_proven":False,"patch_authorized":False,
        }
    finally:pe.close()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    if args.exe.resolve()==args.out.resolve():ap.error("REFUSE_OVERWRITE_EXE")
    proof=verify(args.exe)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("STATIC PASS; not a runtime fix:",len(GUARDS),"opcodes",len(CALLS),"calls")
if __name__=="__main__":main()
