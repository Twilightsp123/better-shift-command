#!/usr/bin/env python3
"""Exact WH3 original EXE: typed B deferred packet -> member motor path audit.

READ ONLY. The static route-to-motor path is conditional. Never claims V3 hit
or that changing any native conditional would be safe.
"""
import argparse
from collections import Counter
import hashlib
import json
import struct
import sys
from pathlib import Path

from audit_wh3_full_native_chain import StrictPE

SHA = "518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
BASE = 0x140000000
# Instruction-aligned sites and literal exact-original bytes (not generated from
# the target at verification time). Unwind ownership is checked where available.
PINS = {
 "B_packet_mode_source":(0x3265bf5,"418b9e18030000"),
 "B_packet_flag_switch":(0x3265beb,"41385f0d"),
 "B_packet_action_68":(0x3265c0a,"bb68000000"),
 "B_packet_action_67":(0x3265c16,"8d5862"),
 "B_packet_action_69":(0x3265c01,"8d5862"),
 "B_packet_action_zero":(0x3265c3a,"4533c9"),
 "B_packet_action_from_member":(0x3265c3f,"448bcb"),
 "B_packet_builder_call":(0x3265c69,"e832470000"),
 "B_packet_builder_r9_to_r14":(0x326a3be,"458bf1"),
 "B_packet_builder_action_arg":(0x326a40f,"458bc6"),
 "B_packet_store_action_34":(0x2f5f945,"45894234"),
 "B_member_deferred_creation":(0x306ba5b,"e8683defff"),
 "deferred_task_packet_copy":(0x2f5f7ee,"e881a7e3ff"),
 "packet_copy_source_34":(0x2d99fad,"8b4234"),
 "packet_copy_dest_34":(0x2d99fb0,"894134"),
 "deferred_tick_deadline_read":(0x2f6b184,"8b81a0000000"),
 "deferred_tick_deadline_cmp":(0x2f6b18a,"398298000000"),
 "deferred_tick_start":(0x2f83b78,"488bcb4883"),
 "task_action_74_read":(0x2f7a002,"8b4174"),
 "task_action_67_69_gate":(0x2f7a00b,"83f802"),
 "task_action_mode_guard":(0x2f7a014,"f6819000000010"),
 "task_action_local_gate":(0x2f7a092,"44394378"),
 "task_install_member_action_v580":(0x2f7a116,"ff9080050000"),
 "task_install_other_action_v568":(0x2f7a17d,"ff9068050000"),
 "task_marks_dispatch_done":(0x2f7a183,"c6839c00000001"),
 "member_action_reset":(0x306a9a7,"e86460d4ff"),
 "member_action_constructor_call":(0x306a9bb,"e890e91d00"),
 "member_action_vtable_rip_lea":(0x324935c,"488d15a5a46c00"),
 "member_action_vtable_install":(0x3249363,"488911"),
 "member_action_source_goal":(0x3249366,"418b01"),
 "member_subaction_gate_state":(0x325ea21,"807e6e01"),
 "member_subaction_gate_6e":(0x325ea25,"756c"),
 "member_subaction_gate_r15d":(0x325ea27,"4585ff"),
 "member_subaction_gate_6c":(0x325ea2c,"807e6c01"),
 "member_action_motor_goal_call":(0x325ea85,"e87a33e1ff"),
 "member_action_marks_issued":(0x325ea8a,"c6467d01"),
 "member_full_goal_write":(0x3071e35,"0f1183f8070000"),
 "member_goal_progress_call":(0x3071e86,"e895000000"),
 "member_motor_goal_write":(0x311963a,"0f1187e0010000"),
 "member_motor_notify":(0x3119687,"e81896feff"),
 "B_subtype_once_flag":(0x328152a,"80b98000000000"),
 "B_subtype_once_skip":(0x3281537,"0f85a1000000"),
 "B_subtype_ready_gate":(0x328154a,"80780800"),
 "B_subtype_group_fanout":(0x32815c5,"e85a45feff"),
 "B_subtype_dispatch_mark":(0x32815d7,"4088bb80000000"),
 "B_subtype_group_completion_gate":(0x32815e2,"83b89808000000"),
 "member_tick_subaction_owner":(0x30822cb,"488d8f28030000"),
 "member_tick_subaction_call":(0x30822d2,"e875ecffff"),
 "subaction_owner_flag_gate":(0x3080f52,"80b95401000001"),
 "subaction_embedded_pointer":(0x3080f5b,"488d5908"),
 "subaction_v8_initialize":(0x3080f71,"ff5008"),
 "subaction_v10_update":(0x3080f84,"ff5010"),
}
VTABLES = {
 0x03905e18+0x10:0x02f83b24,
 0x03913808+0x10:0x0325e294,
 0x03add278+0x10:0x0325d9e0,
}
DIRECT = {
 0x32815c5:0x3265b24,
 0x30822d2:0x3080f4c,
 0x3265c69:0x326a3a0,
 0x306ba5b:0x2f5f7c8,
 0x2f5f7ee:0x2d99f74,
 0x306a9bb:0x3249350,
 0x325ea85:0x3071e04,
 0x3071e86:0x3071f20,
 0x3119687:0x3102ca4,
}
def rel32(site, b):
    if len(b)!=5 or b[0]!=0xe8:raise ValueError("NOT_NATIVE_E8")
    return site+5+struct.unpack_from("<i",b,1)[0]

def member_tables(pe):
    needle=struct.pack("<Q",BASE+0x008f37b0)
    receiver_set={0x0306b9f0,0x0306b9cc,0x03117ce0}
    results=[]
    for name,start,rawsz,offset,vsz,flags in pe.sections:
        if flags & 0x20000000 or not rawsz:continue
        region=pe._mm[offset:offset+rawsz]
        pos=0
        while True:
            at=region.find(needle,pos)
            if at<0:break
            pos=at+1
            vt=start+at-0x3f8
            if vt<start or vt%8 or vt+0x5b8>start+rawsz:continue
            def ptr(slot):
                return struct.unpack("<Q",pe.read(vt+slot,8))[0]-BASE
            if ptr(0x368) in receiver_set:
                results.append({"vt":hex(vt),"receiver":hex(ptr(0x368)),
                                "v580":hex(ptr(0x580)),"v568":hex(ptr(0x568))})
    return results

def verify(exe):
    pe=StrictPE(exe)  # validates exact SHA, PE and ImageBase before reading
    try:
        for name,(site,hx) in PINS.items():
            if pe.read(site,len(hx)//2,True).hex()!=hx:
                raise ValueError("OPCODE_MISMATCH:"+name)
        for slot,impl in VTABLES.items():
            if struct.unpack("<Q",pe.read(slot,8))[0]!=BASE+impl:
                raise ValueError("VTABLE_IDENTITY_MISMATCH:"+hex(slot))
        for site,impl in DIRECT.items():
            if rel32(site,pe.read(site,5,True))!=impl:
                raise ValueError("DIRECT_CALL_MISMATCH:"+hex(site))
        family=member_tables(pe)
        if len(family)!=38 or any(x["v580"]!="0x306a990" for x in family):
            raise ValueError("MEMBER_V580_CENSUS_CHANGED")
        other=Counter(x["v568"] for x in family)
        if other!=Counter({"0x306a8fc":37,"0x311737c":1}):
            raise ValueError("MEMBER_V568_CENSUS_CHANGED:"+str(other))
        return {
          "schema":"bsc.n1.original_b_deferred_motor.v1",
          "exe_sha256":pe.sha,
          "evidence_level":"original_EXE_static_conditional_only",
          "pinned_opcode_instructions":len(PINS),
          "checked_native_vtables":len(VTABLES),
          "verified_direct_calls":len(DIRECT),
          "member_class_census":len(family),
          "member_v580_target":"0x0306A990 for 38/38 member classes",
          "member_v568_targets":dict(other),
          "typed_conditional_route":[
            "B node+0x70 via 0x03281520 / 0x03265B24 -> per-member packet+0x34",
            "after packet fanout 0x032815D7 marks B subtype dispatch, distinct from member motor goal commit; 0x032815E2 additionally tests group+0x898",
            "packet+0x34 through 0x02D99F74 to deferred task+0x74",
            "task+0x74 / mode / distance gates in 0x02F79FF0 select member virtual +0x580 versus +0x568",
            "virtual +0x580 -> 0x0306A990 -> 0x03249350 installs 0x03913808 member+0x330 action",
            "common actor tick 0x03081EB4 at 0x030822CB passes &member+0x328 to 0x03080F4C; owner-flag-gated virtual +0x10 selects 0x0325E294",
            "member action +0x10 -> 0x0325E294 conditionally calls 0x03071E04",
            "0x03071E04 -> 0x03071F20 -> 0x0311954C can commit member+0x1E0 motor target"],
          "unproven":[
            "V3 group mode and selected B cached-route task execution",
            "member actual motor goal commit time relative to next Shift leg",
            "whether altering these conditional paths safely reduces crowding"],
          "patch_authorized":False,"game_verified":False
        }
    finally:pe.close()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    if a.exe.resolve()==a.out.resolve():ap.error("NEVER_OVERWRITE_EXE")
    try:
        report=verify(a.exe)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("PASS",len(PINS),"native instructions",len(VTABLES),
              "vtables",len(DIRECT),"calls; static ONLY, no patch")
        return 0
    except (OSError,ValueError,struct.error) as err:
        print("B_DEFERRED_MOTOR_AUDIT_REFUSED:",err,file=sys.stderr)
        return 2
if __name__=="__main__":sys.exit(main())
