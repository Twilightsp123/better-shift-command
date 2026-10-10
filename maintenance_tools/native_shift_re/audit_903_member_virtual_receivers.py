#!/usr/bin/env python3
"""WH3 9.0.3 pinned-SHA native member vtable resolver. Read-only, no Hook."""
import argparse
import collections
import hashlib
import json
import mmap
import struct
from pathlib import Path
from audit_903_formation_entry import pe_sections, read_executable

SHA="518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
IMAGE_BASE=0x140000000
GETTER=0x008F37B0
RECEIVERS={0x0306B9F0,0x0306B9CC,0x03117CE0}
GUARDS={
 "group_getter":(0x008F37B0,"488b8100030000c3"),
 "member_wrapper":(0x0306B9CC,"488bc1488b89"),
 "common_member_receiver":(0x0306B9F0,"48895c2410"),
 "member_context":(0x0306BA08,"488b4158"),
 "native_payload_flag":(0x0306BA2F,"f6425020"),
 "native_payload_coord_flag":(0x0306BA65,"f6425102"),
 "member_virtual_fanout":(0x030D550F,"ff9068030000"),
 "get_member_group_virtual":(0x030E047E,"ff90f8030000"),
 "clear_member_group_backlink":(0x030E0495,"4883a30003000000"),
 "member_virtual_100":(0x0306BB0E,"41ff9300010000"),
 "member_virtual_e8":(0x0306BB44,"41ff93e8000000"),
 "member_100_calls_coord_writer":(0x03073571,"e86abf0e00"),
 "member_coordinate_pair_write":(0x0315F52C,"f20f118788000000"),
 "member_other_coordinate_write":(0x0315F53E,"898790000000"),
 "member_angle_like_write":(0x0315F54C,"66899fb0000000"),
 "local_route_cache_write":(0x03056FB7,"48898330090000"),
}

def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()

def rip_refs(mm,sections,targets):
 found=collections.defaultdict(list)
 for name,rva,size,raw,is_exec in sections:
  if not is_exec:continue
  b=mm[raw:raw+size]
  for prefix in (b"\x48\x8d\x05",b"\x48\x8d\x0d",b"\x48\x8d\x15",b"\x4c\x8d\x05",b"\x4c\x8d\x0d"):
   start=0
   while True:
    pos=b.find(prefix,start)
    if pos<0:break
    start=pos+1
    delta=struct.unpack_from("<i",b,pos+3)[0]
    dst=rva+pos+7+delta
    if dst in targets:found[dst].append(rva+pos)
 return found

def verify(path):
 if sha256(path)!=SHA:raise ValueError("EXE_SHA256_MISMATCH")
 with path.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
  sections=pe_sections(mm)
  for name,(rva,hexbytes) in GUARDS.items():
   expected=bytes.fromhex(hexbytes)
   if read_executable(mm,sections,rva,len(expected))!=expected:
    raise ValueError("ORIGINAL_INSTRUCTION_MISMATCH: "+name)
  rdata=next((section for section in sections if section[0]==".xdata"),None)
  if rdata is None:raise ValueError("MISSING_SECTION")
  name,start,sz,raw,_=rdata
  candidates={}
  for i in range(0,sz-0x400,8):
   getter=struct.unpack_from("<Q",mm,raw+i+0x3F8)[0]
   if getter!=IMAGE_BASE+GETTER:continue
   recv=struct.unpack_from("<Q",mm,raw+i+0x368)[0]-IMAGE_BASE
   if recv not in RECEIVERS:continue
   def method(offset):
    return hex(struct.unpack_from("<Q",mm,raw+i+offset)[0]-IMAGE_BASE)
   candidates[start+i]={"receiver":hex(recv),"virtual_e8":method(0xE8),
                         "virtual_100":method(0x100),"group_getter":hex(GETTER)}
  refs=rip_refs(mm,sections,set(candidates))
  verified={hex(base):dict(entry,constructor_rip_lea_sites=[hex(x) for x in refs.get(base,[])])
            for base,entry in candidates.items() if refs.get(base)}
  cnt=collections.Counter(item["receiver"] for item in verified.values())
  if len(verified)!=38 or cnt!={"0x306b9f0":36,"0x3117ce0":1,"0x306b9cc":1}:
   raise ValueError("VTABLE_CENSUS_MISMATCH: "+str(cnt))
 return {"exe_sha256":SHA,"selected_opcode_guards":len(GUARDS),"verified_vtable_count":len(verified),
         "receiver_counts":dict(cnt),"constructor_backed_vtables":verified,
         "not_proven":["per-member independent Shift waypoint arrival","actual steering and target semantics",
                       "safe runtime Hook ABI or formation fix"],"runtime_patch_authorized":False}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--exe",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 a=p.parse_args()
 if a.exe.resolve()==a.out.resolve():p.error("cannot overwrite EXE")
 data=verify(a.exe)
 a.out.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
 print("STATIC ONLY",data["verified_vtable_count"],"real vtables; patch=false")

if __name__=="__main__":main()
