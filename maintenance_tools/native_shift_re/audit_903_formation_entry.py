#!/usr/bin/env python3
"""Read-only WH3 9.0.3 formation-entry audit, NOT a patch or model-arrival proof."""
from __future__ import annotations
import argparse
import hashlib
import json
import mmap
import struct
import sys
from pathlib import Path

TARGET_SHA256 = "518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
BASE = 0x140000000
INSTRUCTIONS = {
 "unit_tick_call_member_aggregate": (0x03043722, "e87deaffff"),
 "unit_tick_call_group_target": (0x0304372A, "e8dd76feff"),
 "unit_tick_member_count_gate": (0x0304372F, "39b384010000"),
 "unit_tick_call_queue_processing": (0x03043770, "e8c70b0000"),
 "aggregate_member_ptr_array": (0x030421EC, "488b9188010000"),
 "aggregate_member_count": (0x030421F3, "448b8184010000"),
 "aggregate_load_member": (0x03042203, "488b0a"),
 "aggregate_member_position_x": (0x0304220C, "f30f109988000000"),
 "aggregate_member_position_z": (0x0304221F, "f30f109190000000"),
 "aggregate_member_vs_group_bound": (0x0304222B, "410f2f81d0000000"),
 "aggregate_reset_group_condition": (0x03042266, "4488979c3e0000"),
 "aggregate_member_counter_read": (0x0304226D, "44039904070000"),
 "aggregate_group_counter_write": (0x03042274, "44899f143c0000"),
 "group_target_load_pointer": (0x0302AE10, "488b81f8320000"),
 "group_target_load_mode": (0x0302AE1F, "440fb790700b0000"),
 "group_target_call_coord_provider": (0x0302AE27, "e8d8960000"),
 "group_target_dest_subobject": (0x0302AE32, "498d93383c0000"),
 "group_target_call_update": (0x0302AE4C, "e873f7ffff"),
 "coord_provider_load_group": (0x03034508, "488b89f8320000"),
 "coord_provider_group_subobject": (0x03034512, "4881c1100c0000"),
 "coord_provider_call_helper": (0x0303451E, "e8a98b0e00"),
 "coord_provider_write_output_second": (0x03034528, "41894104"),
 "coord_provider_write_output_first": (0x0303452F, "418909"),
}
DIRECT_CALLS = {
 "unit_tick_to_member_aggregate": (0x03043722, 0x030421A4),
 "unit_tick_to_group_target": (0x0304372A, 0x0302AE0C),
 "unit_tick_to_queue_processing": (0x03043770, 0x0304433C),
 "group_target_to_coord_provider": (0x0302AE27, 0x03034504),
 "group_target_to_update": (0x0302AE4C, 0x0302A5C4),
 "coord_provider_to_helper": (0x0303451E, 0x0311D0CC),
}

def digest_file(path: Path) -> str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024), b""): h.update(b)
 return h.hexdigest()

def pe_sections(mm):
 if len(mm)<0x100 or mm[:2]!=b"MZ":raise ValueError("INVALID_DOS_HEADER")
 nt=struct.unpack_from("<I",mm,0x3c)[0]
 if nt+24>len(mm) or mm[nt:nt+4]!=b"PE\0\0":raise ValueError("INVALID_NT_HEADERS")
 machine,count=struct.unpack_from("<HH",mm,nt+4)
 optsz=struct.unpack_from("<H",mm,nt+20)[0]
 opt=nt+24
 if machine!=0x8664 or count<1 or count>96 or optsz<64:raise ValueError("NOT_AMD64_PE")
 if opt+optsz+40*count>len(mm):raise ValueError("TRUNCATED_PE")
 if struct.unpack_from("<H",mm,opt)[0]!=0x20b:raise ValueError("NOT_PE32_PLUS")
 if struct.unpack_from("<Q",mm,opt+24)[0]!=BASE:raise ValueError("IMAGE_BASE_MISMATCH")
 sections=[]
 for i in range(count):
  off=opt+optsz+40*i
  name=bytes(mm[off:off+8]).split(b"\0",1)[0].decode("ascii","replace")
  _,rv,sz,raw=struct.unpack_from("<IIII",mm,off+8)
  flags=struct.unpack_from("<I",mm,off+36)[0]
  if sz and raw+sz>len(mm):raise ValueError("SECTION_OUT_OF_FILE")
  sections.append((name,rv,sz,raw,bool(flags&0x20000000)))
 return sections

def read_executable(mm,sections,rva,length):
 if rva<0 or length<1:raise ValueError("BAD_RVA_OR_LENGTH")
 for name,start,sz,raw,execute in sections:
  if rva>=start and rva+length<=start+sz:
   if not execute:raise ValueError("NON_EXECUTABLE_SECTION")
   off=raw+rva-start
   return bytes(mm[off:off+length])
 raise ValueError("RVA_NOT_MAPPED")

def e8_target(site,instruction):
 if len(instruction)!=5 or instruction[0]!=0xE8:raise ValueError("NOT_AN_E8_CALL")
 return site+5+struct.unpack_from("<i",instruction,1)[0]

def verify(path:Path):
 sha=digest_file(path)
 if sha!=TARGET_SHA256:raise ValueError("EXE_SHA256_MISMATCH:"+sha)
 with path.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
  sections=pe_sections(mm)
  checked=[]
  for name,(rva,hx) in INSTRUCTIONS.items():
   expected=bytes.fromhex(hx)
   actual=read_executable(mm,sections,rva,len(expected))
   if actual!=expected:raise ValueError("INSTRUCTION_MISMATCH:"+name)
   checked.append({"label":name,"rva":hex(rva),"bytes":actual.hex()})
  edges=[]
  for name,(site,target) in DIRECT_CALLS.items():
   if e8_target(site,read_executable(mm,sections,site,5))!=target:
    raise ValueError("CALL_TARGET_MISMATCH:"+name)
   edges.append({"label":name,"call_rva":hex(site),"target_rva":hex(target)})
 return {
  "schema":"bsc.n1_formation_903_entry.v1",
  "exe_sha256":sha, "game_version_resource_verified":False,
  "grade":"EXACT_BINARY_STATIC_INSTRUCTION_GUARDS",
  "instructions_verified":checked,"direct_calls_verified":edges,
  "facts":[
   "The observed native unit update calls a member-position aggregation function, then a separate group coordinate function, then order processing.",
   "root+0x188 is a pointer array with root+0x184 element count; member-like objects contribute position-like fields +0x88/+0x90 to group aggregates.",
   "Another native function reads root+0x32f8 and passes root+0x3c38 to a group-coordinate processing function."],
  "unproven":[
   "Members of root+0x188 are not independently proven individual soldiers or formation slots.",
   "No model-specific movement target writer, arrival, turn criterion or formation-desynchronization cause is proven.",
   "No ABI, threading or runtime patch lifetime safety has been established."],
  "runtime_patch_authorized":False
 }

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--exe",required=True,type=Path)
 p.add_argument("--report",required=True,type=Path)
 args=p.parse_args(argv)
 if args.exe.resolve()==args.report.resolve():p.error("report may not overwrite EXE")
 try:
  result=verify(args.exe)
  args.report.parent.mkdir(parents=True,exist_ok=True)
  args.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 except (ValueError,OSError,struct.error) as ex:
  print("N1_STATIC_AUDIT_FAILED:",ex,file=sys.stderr)
  return 2
 print("STATIC_ONLY:",len(result["instructions_verified"]),"instructions;",len(result["direct_calls_verified"]),"edges; no hook")
 return 0
if __name__=="__main__":
 sys.exit(main())
