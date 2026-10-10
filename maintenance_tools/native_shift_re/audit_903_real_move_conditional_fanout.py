#!/usr/bin/env python3
"""Exact WH3 9.0.3 binary: read-only proof of conditional MOVE/member fanout.

These original calls are statically reachable, NOT proven taken in V3 battle.
No patch, Hook, executable modification, or runtime claim is made.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import mmap
import struct
import bisect
import sys
from pathlib import Path

EXE_SHA="518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
IMAGE_BASE=0x140000000
E8={
 "move_route":(0x03025E91,0x0301287C),
 "move_construct_task":(0x030260AF,0x02F2C734),
 "task_conditional_group_dispatch":(0x02F56404,0x03279E40),
 "dispatch_to_group_adapter":(0x03279EB3,0x030D554C),
 "adapter_to_record_fanout":(0x030D5603,0x030D5490),
 "fanout_to_per_member_payload_copy":(0x030D54FC,0x02F5F868),
 "member_type_mode0_to_pose_handler":(0x0307328B,0x0315EC98),
 "member_tick_to_pose_rate_writer":(0x0306091D,0x0315C1E4),
 "controller_install_to_member_tick":(0x0306EDC5,0x03060700),
 "mode0_formation_strategy_delegate":(0x030C9B18,0x030DBFD4),
 "distance_updater_to_mean_distance":(0x030D5705,0x030D572C),
 "group_cohesion_query":(0x03024C1F,0x030D5628),
}
BYTES={
 "group_v48_target_generator":(0x030D54CA,"41ff5248"),
 "fanout_member_v368":(0x030D550F,"ff9068030000"),
 "postprocess_runs_after_task_copy":(0x030D5522,"ff5020"),
 "member_mode0_dispatch_vE8":(0x0306BB44,"41ff93e8000000"),
 "member_controller_2e0_install":(0x0306EDD4,"4889bbe0020000"),
 "native_queue_zero_gate":(0x03024C06,"443988882f0000"),
 "cohesion_recent_stamp_comparison":(0x030D5663,"3b91980000000f97c0"),
 "native_context_modes_0_3_5":(0x02DC2E04,"8b412883f805770db9290000000fa3c17303b001c332c0c3"),
}
FUNCTIONS={
 "move":0x03025D70,
 "move_task_tick":0x02F561E8,
 "group_dispatch":0x03279E40,
 "member_target_adapter":0x030D554C,
 "member_target_fanout":0x030D5490,
 "member_receiver":0x0306B9F0,
 "member_mode0_handler":0x03073224,
 "member_controller_install":0x0306EDA0,
 "member_local_tick":0x03060700,
 "pose_rate_writer":0x0315C1E4,
}

def e8_target(site,b):
 if len(b)!=5 or b[0]!=0xe8:raise ValueError("NOT_E8:"+hex(site))
 return site+5+struct.unpack_from("<i",b,1)[0]

def get_owner(rows,starts,site):
 i=bisect.bisect_right(starts,site)-1
 if i<0 or not rows[i][0]<=site<rows[i][1]:return None
 return rows[i]

class OriginalPE:
 def __init__(self,b):
  self.b=b
  if len(b)<0x100 or b[:2]!=b"MZ":raise ValueError("NOT_MZ")
  nt=struct.unpack_from("<I",b,0x3c)[0]
  if nt+24>len(b) or b[nt:nt+4]!=b"PE\0\0":raise ValueError("NOT_PE")
  machine,n=struct.unpack_from("<HH",b,nt+4)
  osz=struct.unpack_from("<H",b,nt+20)[0]
  opt=nt+24
  if machine!=0x8664 or not 1<=n<=96 or opt+osz+n*40>len(b):raise ValueError("NOT_AMD64_PE")
  if struct.unpack_from("<H",b,opt)[0]!=0x20b or osz<144:raise ValueError("NOT_PE32_PLUS")
  if struct.unpack_from("<Q",b,opt+24)[0]!=IMAGE_BASE:raise ValueError("WRONG_IMAGE_BASE")
  self.exrva,self.exsize=struct.unpack_from("<II",b,opt+112+3*8)
  self.sections=[]
  for i in range(n):
   q=opt+osz+40*i
   name=bytes(b[q:q+8]).split(b"\0")[0].decode("ascii","replace")
   _,rva,nraw,raw=struct.unpack_from("<IIII",b,q+8)
   execute=bool(struct.unpack_from("<I",b,q+36)[0]&0x20000000)
   if nraw and (raw>len(b) or nraw>len(b)-raw):raise ValueError("TRUNCATED_SECTION")
   self.sections.append((name,rva,nraw,raw,execute))
 def read(self,rva,n,exec_required=False):
  for name,base,length,offset,execute in self.sections:
   if base<=rva and rva+n<=base+length:
    if exec_required and not execute:raise ValueError("NOT_EXEC:"+hex(rva))
    return bytes(self.b[offset+rva-base:offset+rva-base+n])
  raise ValueError("NOT_RAW_MAPPED:"+hex(rva))
 def ptr(self,rva):
  return struct.unpack("<Q",self.read(rva,8))[0]-IMAGE_BASE
 def exceptions(self):
  if not self.exsize or self.exsize%12:raise ValueError("BAD_EXCEPTION_SIZE")
  rows=list(struct.iter_unpack("<III",self.read(self.exrva,self.exsize)))
  if any(rows[i][0]>=rows[i+1][0] for i in range(len(rows)-1)):
   raise ValueError("UNSORTED_FUNCTION_TABLE")
  return rows

def inspect(exe):
 h=hashlib.sha256()
 with exe.open("rb") as f:
  for chunk in iter(lambda:f.read(4<<20),b""):h.update(chunk)
 if h.hexdigest()!=EXE_SHA:raise ValueError("SHA256_MISMATCH")
 with exe.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
  pe=OriginalPE(data)
  funcs=pe.exceptions(); starts=[t[0] for t in funcs]
  edges=[]
  for label,(site,dest) in E8.items():
   got=e8_target(site,pe.read(site,5,True))
   if got!=dest:raise ValueError("CALL_MISMATCH:"+label)
   parent=get_owner(funcs,starts,site)
   if parent is None:raise ValueError("CALL_NO_FUNCTION:"+label)
   edges.append(dict(label=label,site=hex(site),dest=hex(dest),function=hex(parent[0])))
  for label,(site,raw) in BYTES.items():
   if pe.read(site,len(raw)//2,True)!=bytes.fromhex(raw):
    raise ValueError("OPCODE_MISMATCH:"+label)
  boundaries={}
  for label,site in FUNCTIONS.items():
   own=get_owner(funcs,starts,site)
   if own is None or own[0]!=site:raise ValueError("FUNCTION_START_MISMATCH:"+label)
   boundaries[label]=dict(begin=hex(own[0]),end=hex(own[1]))
  if pe.ptr(0x0390B4F0+8)!=0x03025D70:raise ValueError("MOVE_VTABLE_WRONG")
  if pe.ptr(0x03ABBE18+0x10)!=0x02F561E8:raise ValueError("MOVE_TASK_VTABLE_WRONG")
  seen={}
  for name,s,nraw,raw,execute in pe.sections:
   if execute or nraw<0x400:continue
   buf=data[raw:raw+nraw];needle=struct.pack("<Q",IMAGE_BASE+0x0306B9F0)
   offset=0
   while True:
    hit=buf.find(needle,offset)
    if hit<0:break
    offset=hit+8;vtable=s+hit-0x368
    if vtable<s or vtable+0x400>s+nraw or vtable%8:continue
    if pe.ptr(vtable+0x3f8)!=0x008F37B0:continue
    seen[vtable]=pe.ptr(vtable+0xe8)
  if len(seen)!=36:raise ValueError("COMMON_MEMBER_VTABLES_NOT_36:"+str(len(seen)))
  modes={}
  for target in seen.values():
   key=hex(target);modes[key]=modes.get(key,0)+1
 return dict(schema="bsc.n1_903.conditional_member_fanout.v1",
   original_sha256=EXE_SHA,exception_functions=len(funcs),verified_calls=edges,
   exact_opcode_guards=len(BYTES),native_boundaries=boundaries,
   common_member_vtables=len(seen),mode0_method_frequency=modes,
   state_gate_values=[0,3,5],
   known_limitations=[
    "Indirect per-member dispatch is conditional; older V3 capture reported zero hook hits",
    "actor mode +0x104 is not formation strategy selector",
    "local controller+0x2e0 producer is not yet linked conclusively to active group target",
    "no patch predicate, ABI, Windows runtime or WH3 repair has been demonstrated"],
   runtime_patch_authorized=False)

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--exe",required=True,type=Path)
 ap.add_argument("--out",required=True,type=Path)
 a=ap.parse_args()
 if a.exe.resolve()==a.out.resolve():ap.error("refusing to overwrite exe")
 try:
  data=inspect(a.exe)
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(data,indent=2)+"\n",encoding="utf8")
  print("STATIC CONDITIONAL CHAIN PASS",len(data["verified_calls"]),"E8;",
        data["common_member_vtables"],"member tables; NO PATCH")
  return 0
 except (OSError,ValueError,struct.error) as e:
  print("N1_AUDIT_FAIL:",e,file=sys.stderr)
  return 2

if __name__=="__main__":sys.exit(main())
