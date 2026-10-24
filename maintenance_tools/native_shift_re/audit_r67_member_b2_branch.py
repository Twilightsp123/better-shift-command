#!/usr/bin/env python3
"""R67: read-only B2 recipient branch provenance. Offline only; no Hook or patch."""
from __future__ import annotations
import hashlib
import json
import os
import struct
import sys
from pathlib import Path
IMAGE_BASE=0x140000000
EXE_SHA="9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496"
EXE_LENGTH=232531920
PINS=json.loads(Path(__file__).with_name("r67_member_b2_pins.json").read_text())["instruction_pins"]
CALLS={0x03070b54:0x0312214c,0x03070b6f:0x0312214c,
       0x030782b0:0x0307ae84,0x030782cf:0x03163dc4,
       0x030785b5:0x0316460c,0x03087349:0x03059bc8,
       0x03087351:0x0308d830,0x030592f8:0x03146ff0,
       0x030592ff:0x0310006c,0x0310014c:0x03146ff0,
       0x03100247:0x03121f54}
VTABLES={
 0x03912950:{0x18:0x03086f04,0x20:0x030592bc,0xe8:0x03078268,0x100:0x030785ac},
 0x03ad3360:{0x18:0x03086224,0x20:0x03058d2c,0xe8:0x03077ee4,0x100:0x030785ac}}
VIRTUAL={0x03070b66:0x100,0x03070b9c:0xe8}
def sections(data):
 if data[:2]!=b"MZ":raise ValueError("NOT_MZ")
 p=struct.unpack_from("<I",data,0x3c)[0]
 if data[p:p+4]!=b"PE\\0\\0":raise ValueError("NOT_PE")
 if struct.unpack_from("<H",data,p+4)[0]!=0x8664 or struct.unpack_from("<H",data,p+24)[0]!=0x20b:raise ValueError("NOT_AMD64_PE32PLUS")
 if struct.unpack_from("<Q",data,p+48)[0]!=IMAGE_BASE:raise ValueError("BAD_IMAGEBASE")
 n=struct.unpack_from("<H",data,p+6)[0]; opt=struct.unpack_from("<H",data,p+20)[0]
 out=[]
 for k in range(n):
  j=p+24+opt+40*k
  _,rva,length,raw=struct.unpack_from("<IIII",data,j+8)
  if raw+length>len(data):raise ValueError("BAD_SECTION")
  out.append((rva,length,raw))
 return out
def fileoff(rva,n,s):
 for start,length,raw in s:
  if start<=rva and rva+n<=start+length:return raw+rva-start
 raise ValueError("RVA_OUT_OF_BOUNDS")
def verify(data, require_sha=True):
 if require_sha and (len(data)!=EXE_LENGTH or hashlib.sha256(data).hexdigest()!=EXE_SHA):
  raise ValueError("FAIL_CLOSED_EXE_SHA_OR_SIZE")
 s=sections(data)
 for key,b in PINS.items():
  r=int(key,16);v=bytes.fromhex(b);o=fileoff(r,len(v),s)
  if data[o:o+len(v)]!=v:raise ValueError("PIN_DRIFT_"+key)
 for r,t in CALLS.items():
  b=bytes.fromhex(PINS[f"{r:08x}"])
  if len(b)!=5 or b[0]!=0xe8 or r+5+struct.unpack_from("<i",b,1)[0]!=t:
   raise ValueError("CALL_MISMATCH_"+hex(r))
 for r,expected in VIRTUAL.items():
  b=bytes.fromhex(PINS[f"{r:08x}"])
  if b[:3]!=bytes.fromhex("41ff93") or len(b)!=7 or struct.unpack_from("<I",b,3)[0]!=expected:
   raise ValueError("VIRTUAL_MISMATCH_"+hex(r))
 for base,methods in VTABLES.items():
  for off,expected in methods.items():
   x=struct.unpack_from("<Q",data,fileoff(base+off,8,s))[0]
   if x!=IMAGE_BASE+expected:raise ValueError("VTABLE_DRIFT_"+hex(base+off))
 return {"evidence_grade":"EXACT_EXE_STATIC_ONLY","instruction_pins":len(PINS),
         "e8_edges":len(CALLS),"virtual_sites":len(VIRTUAL),
         "typed_vtable_entries":sum(map(len,VTABLES.values())),
         "ordinary_member_state_1_2":"vtable+0x100 direct-position path",
         "ordinary_member_other_state":"vtable+0xE8 distinct action path",
         "runtime_shift_hit_proven":False,"root_cause_proven":False,
         "gameplay_patch_authorized":False}
if __name__=="__main__":
 if len(sys.argv)!=2:raise SystemExit("usage: python audit_r67_member_b2_branch.py matching_Warhammer3.exe")
 try:
  result=verify(Path(sys.argv[1]).read_bytes())
 except (ValueError,OSError,struct.error) as e:
  print("FAIL_CLOSED",str(e));raise SystemExit(2)
 print(json.dumps(result,indent=2))
