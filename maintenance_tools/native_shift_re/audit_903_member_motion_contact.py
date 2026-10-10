#!/usr/bin/env python3
"""Read-only 9.0.3 WH3 member-motion/contact split; NO NATIVE PATCH.

Different actor types reuse field offsets. Pose differencing and contact
bitsets are NOT proven desired velocity or a same-unit steering controller.
Original EXE must match SHA256, machine instructions, E8 edges and VTables.
"""
import argparse
import collections
import hashlib
import json
import mmap
import struct
import sys
from pathlib import Path
from audit_903_formation_entry import TARGET_SHA256, digest_file, pe_sections, read_executable, e8_target

BASE=0x140000000
FAMILY={
 0x03081EB4:10, 0x02F854AC:9, 0x02F83F44:8,
 0x02F566DC:4, 0x02DD70A4:3,
 0x03128D98:1, 0x02F854B4:1, 0x030811D4:1, 0x03129948:1,
}
GUARDS={
 "same_owner_load":(0x03084996,"488b8780000000"),
 "same_owner_cmp":(0x0308499D,"48398380000000"),
 "same_owner_skip":(0x030849A4,"0f84b3010000"),
 "pair_again_load":(0x030C67C2,"488b8680000000"),
 "pair_again_cmp":(0x030C67C9,"48398380000000"),
 "pair_again_skip":(0x030C67D0,"0f84b2010000"),
 "contact_bitmap_a":(0x030C68D9,"09548720"),
 "contact_bitmap_b":(0x030C691A,"099487e0610000"),
 "child_path_fraction":(0x02F8411F,"f30f11b3cc0b0000"),
 "other_type_matrix_write":(0x0308B798,"0f1183c80b0000"),
 "other_type_matrix_read":(0x0308B7DE,"f3440f108bcc0b0000"),
 "subtype_child_pointer":(0x02F846D6,"488b8b180c0000"),
 "common_child_rcx":(0x0306586A,"498bcf"),
 "common_parent_rcx":(0x03082162,"488bcf"),
 "native_member_copy":(0x030D54FC,"e867a3e8ff"),
 "old_contact_count":(0x030D3DE9,"8b83b0c30000"),
 "roll_count_stamp":(0x030D3DF3,"8983b4c30000"),
 "clear_contact_count":(0x030D3E24,"44899bb0c30000"),
}
CALLS={
 "class_tick_to_common":(0x02F84070,0x03081EB4),
 "common_to_contact_screen":(0x030824A6,0x0308489C),
 "contact_screen_to_recorder":(0x03084B2C,0x030C6788),
 "direction_screen_to_recorder":(0x03086C37,0x030C6788),
 "directional_parent_to_pair":(0x030885CD,0x03086910),
 "class_child_pose":(0x02F846E4,0x0315C1E4),
 "common_to_child_update":(0x03082165,0x03065584),
 "child_update_to_pose_rate":(0x03065871,0x0315C1E4),
 "follower_to_pose_rate":(0x0306091D,0x0315C1E4),
 "follower_tick_to_pose_rate":(0x0306A763,0x0315C1E4),
 "target_set_to_pose_input":(0x0307328B,0x0315EC98),
 "spline_sample":(0x02F84152,0x0143623C),
 "spline_target_build_a":(0x02F655B4,0x02F64CF4),
 "spline_target_build_b":(0x02F80F60,0x02F64CF4),
 "group_update_contact_roll":(0x030E0C9F,0x030D3D7C),
 "roll_clear_bitmap_a":(0x030D3E0C,0x02DB09D4),
 "roll_clear_bitmap_b":(0x030D3E18,0x02DB09D4),
}
RECEIVERS={0x0306B9F0,0x0306B9CC,0x03117CE0}

def pe_raw(mm,sec,rva,n):
 for name,rv,size,off,executable in sec:
  if rv<=rva and rva+n<=rv+size:return bytes(mm[off+rva-rv:off+rva-rv+n])
 raise ValueError("RVA_NOT_FILE_BACKED:"+hex(rva))

def p_rva(mm,sec,rva):
 p=struct.unpack("<Q",pe_raw(mm,sec,rva,8))[0]
 if p<BASE:raise ValueError("NOT_BASE_RELOCATED_POINTER")
 return p-BASE

def scan_vtables(mm,sec):
 needle=struct.pack("<Q",BASE+0x008F37B0)
 found={}
 for name,rva,length,raw,exe in sec:
  if exe or not length:continue
  buf=mm[raw:raw+length]
  at=0
  while 1:
   at=buf.find(needle,at)
   if at<0:break
   vt=rva+at-0x3f8;at+=1
   if vt<rva or vt%8 or vt+0x400>rva+length:continue
   v368=p_rva(mm,sec,vt+0x368)
   if v368 in RECEIVERS:found[vt]=(p_rva(mm,sec,vt+0x18),v368)
 return found

def diagnose(exe):
 h=digest_file(exe)
 if h!=TARGET_SHA256:raise ValueError("EXE_SHA_MISMATCH:"+h)
 with exe.open("rb") as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
  sec=pe_sections(mm)
  for label,(rva,hx) in GUARDS.items():
   if read_executable(mm,sec,rva,len(hx)//2)!=bytes.fromhex(hx):
    raise ValueError("ORIGINAL_OPCODE_MISMATCH:"+label)
  edges=[]
  for label,(site,dest) in CALLS.items():
   found=e8_target(site,read_executable(mm,sec,site,5))
   if found!=dest:raise ValueError("ORIGINAL_CALL_MISMATCH:"+label)
   edges.append(dict(name=label,site=hex(site),destination=hex(dest)))
  tables=scan_vtables(mm,sec)
  counts=collections.Counter(v18 for v18,_ in tables.values())
  if len(tables)!=38 or counts!=FAMILY:
   raise ValueError("ACTOR_TYPE_FAMILY_MISMATCH:"+str(counts))
  # +0x18 method 0x02F854AC is a jump to the common method.
  b=read_executable(mm,sec,0x02F854AC,5)
  if b[0]!=0xE9 or e8_target(0x02F854AC,b"\xe8"+b[1:])!=0x03081EB4:
   raise ValueError("COMMON_UPDATE_FORWARDER_MISMATCH")
 return dict(schema="bsc.903.member_motion_contact_boundary.v1",
  exact_exe_sha=h,
  opcode_guards=len(GUARDS),direct_edges=edges,
  constructor_member_vtables=len(tables),
  actor_update_family={hex(k):v for k,v in sorted(counts.items())},
  signed_machine_derived_points=[
   "0x03081EB4 -> 0x0308489C -> 0x030C6788 is a reachable contact-record path",
   "same +0x80 affiliations are skipped at 0x030849A4 and 0x030C67D0",
   "0x030C6788 writes contact BITSETS/counters, NOT proven steering velocity",
   "0x030E0AA8 -> 0x030D3D7C stamps prior counts and clears current contacts",
   "0x02F83F44 local progress +0xBCC is type-specific; other class uses matrix +0xBC8",
   "0x02F846D6 RCX=actor+0xC18 CHILD before 0x0315C1E4; +0xE0 is post-pose displacement rate",
   "RMB and Shift both use this actor-update family; static code does not establish actual V3 subtype"
  ],
  unresolved="producer of primary soldier desired displacement/steering and its same-unit separation policy",
  patch_authorized=False,windows_tested=False,wh3_tested=False)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--exe",type=Path,required=True)
 parser.add_argument("--out",type=Path,required=True)
 a=parser.parse_args()
 if a.exe.resolve()==a.out.resolve():parser.error("cannot overwrite EXE")
 try:
  result=diagnose(a.exe)
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 except (OSError,ValueError,struct.error) as err:
  print("STRICT_STATIC_AUDIT_BLOCKED:",err,file=sys.stderr);return 2
 print("STATIC_ONLY:",result["opcode_guards"],"guards",len(result["direct_edges"]),"calls",result["constructor_member_vtables"],"vtables; NO HOOK")
 return 0
if __name__=="__main__":sys.exit(main())
