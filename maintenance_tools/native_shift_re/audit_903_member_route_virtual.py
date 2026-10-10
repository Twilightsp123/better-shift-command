#!/usr/bin/env python3
"""Read-only WH3 9.0.3 route/member virtual-dispatch audit; never modifies game."""
import argparse,hashlib,json,mmap
from pathlib import Path
from audit_903_formation_entry import pe_sections,read_executable,e8_target

TARGET_SHA256="518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
GUARDS={
 "wrapper_to_member_path":(0x03012A4E,"e819000000"),
 "member_container_A":(0x03012AD1,"488b9f88010000"),
 "member_related_pointer":(0x03012AE8,"488b5b20"),
 "member_pos_X":(0x03012AF5,"f30f108388000000"),
 "member_pos_Z":(0x03012B02,"f30f108b90000000"),
 "unit_route_pointer":(0x03012BED,"488b8670020000"),
 "member_virtual_receiver":(0x03012C02,"488bcb"),
 "member_virtual_0xC8":(0x03012C1E,"ff90c8000000"),
 "member_to_unit_route":(0x03012C42,"e835fcffff"),
}
CALLS={"wrapper_to_member":(0x03012A4E,0x03012A6C),
       "member_to_unit_route":(0x03012C42,0x0301287C)}

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(4*1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def verify(exe):
    sha=digest(exe)
    if sha!=TARGET_SHA256:
        raise ValueError("EXE_SHA256_MISMATCH")
    with exe.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        secs=pe_sections(mm)
        for key,(rva,hx) in GUARDS.items():
            raw=bytes.fromhex(hx)
            if read_executable(mm,secs,rva,len(raw))!=raw:
                raise ValueError("GUARD_MISMATCH:"+key)
        for key,(site,dest) in CALLS.items():
            if e8_target(site,read_executable(mm,secs,site,5))!=dest:
                raise ValueError("EDGE_MISMATCH:"+key)
    return {"schema":"bsc.n1_9_0_3_member_route_virtual.v1",
            "exe_sha256":sha,
            "verified_opcode_guards":len(GUARDS),
            "verified_direct_calls":len(CALLS),
            "member_related_virtual":{"site_rva":"0x3012c1e","vtable_offset":"0xC8"},
            "unit_route_pointer_offset":"0x270",
            "not_proven":["individual soldier type", "virtual +0xC8 gameplay meaning",
                          "full native MOVE worker call path into this member routine",
                          "different soldier models owning different high-level Shift commands"],
            "runtime_patch_authorized":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe",required=True,type=Path)
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args()
    if a.exe.resolve()==a.report.resolve():
        p.error("report may not overwrite EXE")
    output=verify(a.exe)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    print("STATIC_ONLY:",len(GUARDS),"guards",len(CALLS),"edges; patch=false")

if __name__=="__main__":main()
