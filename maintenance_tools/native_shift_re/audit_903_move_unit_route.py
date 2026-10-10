#!/usr/bin/env python3
"""Read-only, exact-SHA WH3 9.0.3 native MOVE -> UnitRoot route proof."""
import argparse
import hashlib
import json
import mmap
from pathlib import Path

TARGET_SHA256 = "518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
GUARDS = {
 "move_mode_a_issues_native_config":(0x03025E91,"e8e6c9feff"),
 "move_mode_b_issues_native_config":(0x03026022,"e855c8feff"),
 "config_root_group_accessor":(0x03012897,"488b4138"),
 "config_group_status_check":(0x030128AB,"4180b89400000000"),
 "config_A_count_gate":(0x030128B9,"83b98401000000"),
 "config_clear_subobject_3260":(0x030128DC,"488d8f60320000"),
 "config_clear_subobject_3280":(0x030128E8,"488d8f80320000"),
 "config_unit_group_pointer":(0x03012902,"488b87f8320000"),
 "config_A_member_count":(0x0301290C,"448b8784010000"),
 "config_group_b30_subobject":(0x03012913,"488b88300b0000"),
 "config_unit_scalar":(0x0301291F,"f30f108fd0010000"),
 "config_descriptor_constructor":(0x03012945,"e866a10d00"),
 "config_original_route_creator":(0x03012982,"e80d5fffff"),
 "config_store_heap_route":(0x03012987,"48898770020000"),
 "config_direct_destination_x":(0x030129BB,"8b06894120"),
 "config_direct_destination_z":(0x030129C0,"8b4604894124"),
 "config_direct_destination_third":(0x030129C6,"8b4608894128"),
 "config_write_orientation_scalar":(0x030129E0,"f30f117140"),
 "config_store_inline_route":(0x030129E5,"48898f70020000"),
 "descriptor_copy_original_move_context":(0x030ECABC,"488911"),
 "descriptor_store_scalar_one":(0x030ECAF0,"f30f11413c"),
 "descriptor_store_scalar_two":(0x030ECAF5,"f30f114944"),
 "descriptor_store_mode_flag":(0x030ECAFA,"6644894938"),
}
CALLS={
 "move_mode_a_to_config":(0x03025E91,0x0301287C),
 "move_mode_b_to_config":(0x03026022,0x0301287C),
 "config_clear_3260":(0x030128E3,0x0301989C),
 "config_clear_3280":(0x030128EF,0x0301989C),
 "config_group_scalar":(0x0301291A,0x030D1980),
 "config_descriptor_constructor":(0x03012945,0x030ECAB0),
 "config_route_creator":(0x03012982,0x03008894),
}

def file_digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def verify(exe):
    from audit_903_formation_entry import pe_sections,read_executable,e8_target
    actual=file_digest(exe)
    if actual!=TARGET_SHA256:
        raise ValueError("EXE_SHA256_MISMATCH")
    checked=[];calls=[]
    with exe.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        sections=pe_sections(mm)
        for name,(rva,hx) in GUARDS.items():
            expected=bytes.fromhex(hx)
            if read_executable(mm,sections,rva,len(expected))!=expected:
                raise ValueError("GUARD_MISMATCH:"+name)
            checked.append({"name":name,"rva":hex(rva),"bytes":hx})
        for name,(site,target) in CALLS.items():
            got=e8_target(site,read_executable(mm,sections,site,5))
            if got!=target:
                raise ValueError("CALL_TARGET_MISMATCH:"+name)
            calls.append({"name":name,"site":hex(site),"target":hex(target)})
    return {
        "schema":"bsc.n1_903_native_move_unit_route.v1",
        "exe_sha256":actual,
        "exact_instruction_guards":checked,
        "exact_direct_call_targets":calls,
        "proven":["two original native MOVE worker callsites both reach unit route configurator 0x0301287C",
                  "unit route configuration either stores original allocated descriptor or inline destination at root+0x270"],
        "not_proven":["per-soldier Shift queues or model-level target assignment",
                      "the reason for models turning asynchronously and crowding",
                      "thread safety, ABI or any safe native patch"],
        "runtime_patch_authorized":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    if args.exe.resolve()==args.report.resolve():
        p.error("report cannot replace exe")
    report=verify(args.exe)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("STATIC PASS",len(report["exact_instruction_guards"]),"guards",len(report["exact_direct_call_targets"]),"calls; patch=false")

if __name__=="__main__":main()
