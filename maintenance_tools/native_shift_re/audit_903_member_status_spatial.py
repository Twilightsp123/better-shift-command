#!/usr/bin/env python3
"""Only read exact-WH3-build x64 instruction guards for member status/spatial code.

This is NOT a mod, hook, or proof of per-soldier Shift waypoint arrival.
"""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
from audit_903_formation_entry import pe_sections, read_executable, e8_target

SHA = "518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
GUARDS = """
301c0ce 488b9070020000
301c0ee e83dfb0000
302bc56 448b8284010000
302bc6b 488b8270020000
302bd09 e85abdffff
302bd41 e8366bfeff
302bde4 488b8888010000
302bdeb 488b04d9
302bdf1 83606cfe
302bdf5 836070fe
3033a69 44398084010000
3033a72 488b8088010000
3033a7f 488b14c8
3033a83 834a6c01
3033bfc 488b8088010000
3033c0a 4183486c03
3018f97 83486c01
3018fa8 83606cfe
3057b7c ff5058
3057b8d 8b90640b0000
3057b97 488b88680b0000
3057ba3 f6426c02
3057ba9 f30f108290000000
3057bb9 f30f108a88000000
3057bd5 f30f51c0
3057bd9 f30f5882a0000000
3057be1 f30f5fc6
3058f40 e823ecffff
3058f78 e8ebebffff
3058f92 e8d1ebffff
3058fa6 e8bdebffff
3058fbb 440f2fc0
3086ad5 e83223fdff
3086b7e e88922fdff
30885bf e8f4dfffff
30885cd e83ee3ffff
3086640 e82315fdff
3086654 e80f15fdff
"""
EDGES = {
  0x301c0ee: 0x302bc30,
  0x302bd09: 0x3027a68,
  0x302bd41: 0x301287c,
  0x3058f40: 0x3057b68,
  0x3058f78: 0x3057b68,
  0x3058f92: 0x3057b68,
  0x3058fa6: 0x3057b68,
  0x3086ad5: 0x3058e0c,
  0x3086b7e: 0x3058e0c,
  0x30885bf: 0x30865b8,
  0x30885cd: 0x3086910,
  0x3086640: 0x3057b68,
  0x3086654: 0x3057b68,
}

def sha256(path):
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def verify(path):
    digest=sha256(path)
    if digest != SHA:
        raise ValueError("EXE_SHA256_MISMATCH")
    guards=[(int(site,16),bytes.fromhex(code)) for site,code in
            (line.split() for line in GUARDS.strip().splitlines())]
    with path.open("rb") as source,mmap.mmap(source.fileno(),0,access=mmap.ACCESS_READ) as mm:
        sections=pe_sections(mm)
        for site,expected in guards:
            if read_executable(mm,sections,site,len(expected))!=expected:
                raise ValueError("INSTRUCTION_GUARD_MISMATCH: "+hex(site))
        for site,target in EDGES.items():
            if e8_target(site,read_executable(mm,sections,site,5))!=target:
                raise ValueError("DIRECT_CALL_MISMATCH: "+hex(site))
    return {"schema":"bsc.n1.903.member_status_spatial.static",
            "exe_sha256":digest,"verified_instruction_guards":len(guards),
            "verified_direct_call_edges":len(EDGES),
            "proven":"shared unit-route task and full A-member status reset; separate member spatial comparison graph",
            "unknown":"no verified ordinary Shift→spatial geometry call, member bit meanings, or per-model leg/facing writer",
            "runtime_patch_authorized":False}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.exe.resolve()==a.out.resolve():p.error("cannot overwrite EXE")
    report=verify(a.exe)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("STATIC ONLY",report["verified_instruction_guards"],"guards",
          report["verified_direct_call_edges"],"edges; NO HOOK")
