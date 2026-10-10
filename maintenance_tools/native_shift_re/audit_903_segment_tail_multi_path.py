#!/usr/bin/env python3
"""WH3 9.0.3 exact-SHA read-only audit: route-segment fallback and alternate issuer.

This proves instruction and vtable facts, NOT game execution nor patch safety.
"""
from __future__ import annotations
import argparse,hashlib,json,mmap,struct,sys
from pathlib import Path

TARGET="518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
BASE=0x140000000
E8={
 "task_to_group_dispatch":(0x02f56404,0x03279e40),
 "group_dispatch_to_adapter":(0x03279eb3,0x030d554c),
 "adapter_to_group_fanout":(0x030d5603,0x030d5490),
 "adapter_to_segment_builder":(0x030d55f5,0x030fda9c),
 "group_fanout_copies_member_payload":(0x030d54fc,0x02f5f868),
 "mode0_to_segment_emitter":(0x030c9b18,0x030dbfd4),
 "repeat_last_record_append48":(0x030d1f82,0x030be544),
 "unit_alt_target_generation_1":(0x0301385e,0x030c9a64),
 "unit_alt_target_generation_2":(0x03013b5c,0x030c9a64),
 "unit_alt_member_submit_1":(0x0301389e,0x02e0afdc),
 "unit_alt_member_submit_2":(0x03013b9c,0x02e0afdc),
 "unit_alt_member_dispatch_1":(0x030138ad,0x02ded114),
 "unit_alt_member_dispatch_2":(0x03013bab,0x02ded114),
}
GUARDS={
 "remaining_quota_gate":(0x030dc075,"85db740e"),
 "repeat_sink_v20":(0x030dc079,"498b06498bceff5020"),
 "decrement_remaining_quota":(0x030dc082,"83c3ff75f2"),
 "vector_last_count":(0x030d1f68,"418b400c"),
 "vector_index_sub_one":(0x030d1f70,"ffc8"),
 "vector_stride_48":(0x030d1f76,"488d144048c1e204"),
 "group_member_index_record":(0x030d54d9,"4c8d047649c1e004"),
 "copy_occurs_before_member_send":(0x030d54fc,"e867a3e8ff"),
 "first_unitroot_vtable_install":(0x03009471,"488d05a0f28f00"),
 "second_unitroot_vtable_install":(0x0300a54e,"488d05c3e18f00"),
}
FALLBACK_SLOTS=(0x03acfc60,0x03acfd18,0x03acfd40,0x03acfd68,0x03acfdb8,0x03acfde0)
VIRTUAL={
 "unit_v248":(0x03908718+0x248,0x030135e0),
 "mode0_group_v48":(0x0390f558+0x48,0x030c9a64),
 "mode0_sink_v0":(0x03acfd48,0x030dc5a0),
 "kind0_v38":(0x0390f2b0+0x38,0x030dc0a0),
 "kind1_v38":(0x0390f330+0x38,0x030dc304),
}
def read(mm,sections,rva,n,execute=False):
 if rva<0 or n<1:raise ValueError("INVALID_RVA")
 for start,size,raw,x in sections:
  if start<=rva and rva+n<=start+size:
   if execute and not x:raise ValueError("NOT_EXECUTABLE:"+hex(rva))
   return bytes(mm[raw+rva-start:raw+rva-start+n])
 raise ValueError("RVA_NOT_RAW_MAPPED:"+hex(rva))

def verify(path):
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 if digest!=TARGET:raise ValueError("EXE_SHA_MISMATCH")
 with path.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
  if mm[:2]!=b"MZ":raise ValueError("INVALID_MZ")
  nt=struct.unpack_from("<I",mm,0x3c)[0]
  if mm[nt:nt+4]!=b"PE\0\0":raise ValueError("INVALID_PE")
  machine,count=struct.unpack_from("<HH",mm,nt+4)
  opt=nt+24;osz=struct.unpack_from("<H",mm,nt+20)[0]
  if machine!=0x8664 or not 1<=count<=96 or struct.unpack_from("<H",mm,opt)[0]!=0x20b:raise ValueError("NOT_X64")
  if struct.unpack_from("<Q",mm,opt+24)[0]!=BASE:raise ValueError("UNEXPECTED_IMAGE_BASE")
  secs=[]
  for i in range(count):
   q=opt+osz+40*i
   _,rva,size,raw=struct.unpack_from("<IIII",mm,q+8)
   x=bool(struct.unpack_from("<I",mm,q+36)[0]&0x20000000)
   if size and raw+size>len(mm):raise ValueError("TRUNCATED_PE")
   secs.append((rva,size,raw,x))
  edges=[]
  for name,(site,dest) in E8.items():
   b=read(mm,secs,site,5,True)
   if b[0]!=0xe8 or site+5+struct.unpack_from("<i",b,1)[0]!=dest:raise ValueError("E8_MISMATCH:"+name)
   edges.append({"name":name,"site":hex(site),"dest":hex(dest)})
  for name,(rva,hx) in GUARDS.items():
   if read(mm,secs,rva,len(hx)//2,True)!=bytes.fromhex(hx):raise ValueError("OPCODE_MISMATCH:"+name)
  for name,(slot,target) in VIRTUAL.items():
   q=struct.unpack("<Q",read(mm,secs,slot,8))[0]-BASE
   if q!=target:raise ValueError("VTABLE_MISMATCH:"+name)
  for slot in FALLBACK_SLOTS:
   if struct.unpack("<Q",read(mm,secs,slot,8))[0]-BASE!=0x030d1f60:raise ValueError("SHARED_TAIL_VTABLE_MISMATCH")
 return {"grade":"EXACT_SHA_STATIC_ONLY","binary_sha256":digest,"verified_direct_edges":edges,
    "verified_byte_guards":len(GUARDS),"shared_tail_vtables":[hex(x-0x20) for x in FALLBACK_SLOTS],
    "unitroot_v248":"0x030135e0","mode0_strategy":"0x030c9a64",
    "native_fallback":"append exact last 48-byte record if segment generators return remaining quota",
    "disposition":"global 0x030d1f60 detour is NOT safe; affects >=6 sink classes",
    "not_proven":["whether V3 used these conditional branches","actual target/steering collision cause","Hook ABI/lifetime"],
    "runtime_patch_authorized":False,"windows_tested":False,"wh3_tested":False}

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--exe",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args(argv)
 if a.exe.resolve()==a.out.resolve():p.error("report cannot overwrite EXE")
 try:
  result=verify(a.exe)
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(result,indent=2)+"\n")
 except (OSError,ValueError,struct.error) as e:
  print("FAIL_CLOSED:",e,file=sys.stderr);return 2
 print("STATIC PASS:",len(E8),"E8,",len(GUARDS),"opcodes,",len(FALLBACK_SLOTS),"sink variants; NO HOOK")
 return 0
if __name__=="__main__":sys.exit(main())
