#!/usr/bin/env python3
"""Exact-original WH3 static producer/consumer proof for member motor goal.
Read only. Does NOT prove the old goal was used in a specific V3 battle.
"""
import argparse
import json
import struct
import sys
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

PINS={
    "motor_writer_skip":(0x03119556,"80b92802000001"),
    "motor_goal_store":(0x0311963A,"0f1187e0010000"),
    "motor_postwrite_aux":(0x03119687,"e81896feff"),
    "aux_flag_gate":(0x03102CAB,"f6c204"),
    "aux_list_member":(0x03102CB0,"488b8900020000"),
    "aux_unlink_call":(0x03102CBF,"e8d8e90100"),
    "aux_unlink_member_ptr":(0x031216E4,"4c898a00020000"),
    "goal_read_mode_guard":(0x03115C98,"f6818801000002"),
    "goal_read_status_guard":(0x03115CAB,"80b98f01000000"),
    "goal_read_member_x":(0x03115CB4,"f30f10b988000000"),
    "goal_read_member_target":(0x03115CBC,"4c8d89e0010000"),
    "goal_read_member_z":(0x03115CC3,"f30f10b190000000"),
    "goal_decode":(0x03115CD3,"e8fc710000"),
    "goal_heading":(0x03115CE3,"e8e877feff"),
    "goal_dot_gate":(0x03115D16,"0f2f0da36e8000"),
    "goal_decoder_route_ref":(0x0311CEDB,"488b4910"),
    "goal_decoder_xyz":(0x0311CEEF,"418b00"),
    "member_action_member_ptr":(0x032561E4,"488b4908"),
    "member_action_motor_state":(0x032561E8,"8b9110070000"),
    "member_action_goal_read":(0x03256204,"e88bfaebff"),
    "member_action_consumes_result":(0x0325620B,"0f845d010000"),
    "member_action_tick_calls_reader_wrapper":(0x0325FD87,"e8f463ffff"),
    "group_member_goal_reader":(0x02F858FD,"e892031900"),
    "B_deferred_receive":(0x0306BA5B,"e8683defff"),
    "B_deferred_return":(0x0306BA60,"e975010000"),
    "immediate_old_action_clear":(0x0306BBAE,"e85d4ed4ff"),
    "near_action_new_goal":(0x0325EA85,"e87a33e1ff"),
    "far_action_new_goal":(0x03256161,"e89ebce1ff"),
}
E8={
    0x03119687:0x03102CA4,
    0x03102CBF:0x0312169C,
    0x03115CD3:0x0311CED4,
    0x03115CE3:0x030FD4D0,
    0x03256204:0x03115C94,
    0x0325FD87:0x03256180,
    0x02F858FD:0x03115C94,
    0x0306BA5B:0x02F5F7C8,
    0x0306BBAE:0x02DB0A10,
    0x0325EA85:0x03071E04,
    0x03256161:0x03071E04,
}
def e8_target(site, data):
    if len(data)!=5 or data[0]!=0xE8:raise ValueError("NOT_E8:"+hex(site))
    return site+5+struct.unpack_from("<i",data,1)[0]

def verify(exe):
    pe=StrictPE(exe)
    try:
        for name,(site,hexbytes) in PINS.items():
            if pe.read(site,len(hexbytes)//2,True).hex()!=hexbytes:
                raise ValueError("OPCODE_CHANGED:"+name)
        for site,target in E8.items():
            if e8_target(site,pe.read(site,5,True))!=target:
                raise ValueError("DIRECT_CALL_CHANGED:"+hex(site))
        return {
            "grade":"EXACT_ORIGINAL_EXE_STATIC_ONLY",
            "sha256":pe.sha,
            "opcode_guards":len(PINS),"direct_calls":len(E8),
            "native_goal_writer":"0x0311954C -> member+0x1E0 at 0x0311963A, guarded by member+0x228",
            "typed_reader":"member action 0x0325E294 -> 0x03256180 -> 0x03115C94 -> member+0x1E0 goal and member+0x88/+0x90 current position -> directional action predicate",
            "related_group_reader":"0x02F85880 loops native member pointers and conditionally calls the same 0x03115C94",
            "negative_controls":[
                "0x03102CA4 calls 0x0312169C to unlink member+0x200/+0x208/+0x210, NOT a proven physical motor integrator",
                "0x0311EC28 reads UnitRoot+0x1E0, not this member+0x1E0"
            ],
            "missing_proof":"V3 actual B receive followed by action use of old member goal before new goal commit, and geometric incompatibility with the native turn",
            "patch_authorized":False,"game_run":False,
        }
    finally:pe.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    if a.exe.resolve()==a.out.resolve():parser.error("REFUSE_EXE_OVERWRITE")
    try:proof=verify(a.exe)
    except (ValueError,OSError,KeyError,struct.error) as ex:
        print("ORIGINAL_GOAL_AUDIT_REFUSED:",ex,file=sys.stderr);return 2
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("STATIC PASS",len(PINS),"guards",len(E8),"E8 edges. Runtime NOT observed.")
    return 0
if __name__=="__main__":sys.exit(main())
