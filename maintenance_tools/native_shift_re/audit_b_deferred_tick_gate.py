#!/usr/bin/env python3
"""BSC N1 exact-original deferred task v+0x80 gate / zero-delay audit.

READ ONLY; verifies original WH3 SHA, opcodes, native call and branch targets.
Conditional native static reachability DOES NOT prove the V3 battle path.
"""
from pathlib import Path
import argparse, json, struct, sys
from audit_wh3_full_native_chain import StrictPE

ORIGINAL_SHA="518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a"
IMAGE_BASE=0x140000000
PIN={
 0x326a402:"c644243800", 0x326a40a:"c644243000",
 0x326a445:"c644243800", 0x326a44d:"c644243001",
 0x326a423:"e8b454cfff", 0x326a466:"e87154cfff",
 0x2f5f915:"0fb6442438",0x2f5f924:"0fb64c2440",
 0x2f5f929:"80e101",0x2f5f932:"c0e104",
 0x2f5f940:"80c906",0x2f5f95e:"41884a50",
 0x2d9a01a:"2410",0x2d9a01e:"41884050",
 0x2f5f7dd:"488d0534669a00",0x2f5f7ee:"e881a7e3ff",
 0x2f5f91a:"41894a4c",0x2f5f83d:"8b8898000000",
 0x2f5f843:"034b4c",0x2f5f84a:"898fa0000000",
 0x2f6b184:"8b81a0000000",0x2f6b18a:"398298000000",
 0x2f6b190:"724e",0x2f6b1db:"e810ee0000",
 0x306ba5b:"e8683defff",0x306ba60:"e975010000",
 0x8f4dd0:"0fb68190000000",0x8f4dd7:"c0e804",
 0x8f4dda:"2401",0x8f4ddc:"c3",
 0x3082090:"f6870801000010",0x308209c:"0f85c0010000",
 0x30820a2:"f687100b000008",0x3263c0a:"0883100b0000",
 0x30820b5:"0f85a7010000",0x3082262:"8a8708010000",
 0x3082268:"a808",0x308227d:"a804",
 0x308228a:"743f",0x308228f:"743a",
 0x30822cb:"488d8f28030000",0x30822d2:"e875ecffff",
 0x30822e4:"e9c0000000",0x30822e9:"488bcf",
 0x3082343:"488d8fa8040000",0x308234d:"ff9080000000",
 0x3082356:"753e",0x3082165:"e81a34feff",
}
CALLS={
 0x326a423:0x2f5f8dc,0x326a466:0x2f5f8dc,
 0x2f5f7ee:0x2d99f74,0x306ba5b:0x2f5f7c8,
 0x30822d2:0x3080f4c,0x3082165:0x3065584,
 0x2f6b1c5:0x2f67178,0x2f6b1db:0x2f79ff0,
}
BRANCHES={
 0x306ba60:(5,0x306bbda),0x308209c:(6,0x3082262),
 0x30820b5:(6,0x3082262),0x30822e4:(5,0x30823a9),
 0x308227f:(2,0x30822e9),0x3082356:(2,0x3082396),
 0x2f6b190:(2,0x2f6b1e0),
}
def branch_dest(site,b):
    if len(b)==5 and b[0] in (0xe8,0xe9):
        return site+5+struct.unpack_from("<i",b,1)[0]
    if len(b)==2 and b[0] in (0x72,0x73,0x74,0x75):
        return site+2+struct.unpack_from("<b",b,1)[0]
    if len(b)==6 and b[:2] in (b"\x0f\x84",b"\x0f\x85"):
        return site+6+struct.unpack_from("<i",b,2)[0]
    raise ValueError("UNSUPPORTED_BRANCH")

def b_packet_initial_flag(variant):
    if variant not in ("a","b"):raise ValueError("BAD_BRANCH")
    # Both 0x0326A402 and 0x0326A445 set caller [rsp+0x38]=0.
    # CALL pushes 8-byte return address: callee [rsp+0x40]=caller [rsp+0x38].
    # 0x02F5F924 -> AND 1 -> SHL 4 -> OR 6 -> packet+0x50.
    flag=((0 & 1)<<4)|((0 if variant=="a" else 1)&1)|6
    if variant=="a":flag|=8
    return flag

def special_tick_arm(member108,phase,entered_special=True):
    if not entered_special:return "normal_actor_update"
    if member108 & 8:return "actor_virtual_498"
    if member108 & 4:
        return "old_subaction_v10" if phase in (0x10,4) else "other_state"
    return "deferred_v80_flag_QUERY_not_task_tick"

def verify(exe):
    p=StrictPE(exe)
    try:
        for site,hx in PIN.items():
            if p.read(site,len(hx)//2,True).hex()!=hx:
                raise ValueError("ORIGINAL_OPCODE_MISMATCH:"+hex(site))
        for site,fn in CALLS.items():
            if branch_dest(site,p.read(site,5,True))!=fn:
                raise ValueError("DIRECT_CALL_CHANGED:"+hex(site))
        for site,(n,fn) in BRANCHES.items():
            if branch_dest(site,p.read(site,n,True))!=fn:
                raise ValueError("CONDITIONAL_BRANCH_CHANGED:"+hex(site))
        vptr=struct.unpack("<Q",p.read(0x03905E98,8))[0]
        if vptr!=IMAGE_BASE+0x008F4DD0:raise ValueError("VTABLE_V80_CHANGED")
        assert b_packet_initial_flag("a")&0x10==0
        assert b_packet_initial_flag("b")&0x10==0
        return dict(schema="bsc.n1.b_deferred_tick_gate.v1",
          exe_sha256=p.sha,proof_level="original_EXE_STATIC_not_V3",
          opcode_guards=len(PIN),call_edges=len(CALLS),
          branch_targets=len(BRANCHES),vtable_slots=1,
          initial_packet_flag_a=hex(b_packet_initial_flag("a")),
          initial_packet_flag_b=hex(b_packet_initial_flag("b")),
          findings=[
           "deferred vtable 0x03905E18 +0x80 is 0x008F4DD0, returns task+0x90 bit4 only",
           "B packet constructor writes flag bit4=0 for both native branches; copied into task+0x90",
           "B packet+0x4C=0, task+0xA0=creation group tick; no required one-tick delay",
           "0x03081EB4 special branch old-action +0x328 tick and deferred +0x4A8 v80 QUERY are mutually exclusive",
           "0x030820A2 tests member+0xB10 bit3, NOT bit7 written by B group classifier",
          ],unknown=[
           "task bit4 may be changed by unproven later writers",
           "normal member motor update outside this special branch",
           "whether V3 used B path and retained an incompatible old motor goal",
          ],patch_authorized=False,game_verified=False)
    finally:p.close()

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--exe",required=True,type=Path)
    a.add_argument("--out",required=True,type=Path)
    z=a.parse_args()
    if z.exe.resolve()==z.out.resolve():a.error("EXE_OVERWRITE_DENIED")
    try:
        proof=verify(z.exe)
        z.out.parent.mkdir(parents=True,exist_ok=True)
        z.out.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n")
        print("PASS original static",len(PIN),"guards",len(CALLS),"calls; NO PATCH")
        return 0
    except (ValueError,OSError,struct.error) as e:
        print("STATIC_AUDIT_DENIED:",e,file=sys.stderr)
        return 2
if __name__=="__main__":sys.exit(main())
