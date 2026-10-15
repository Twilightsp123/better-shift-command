#!/usr/bin/env python3
"""Exact binary proof: newly-activated MOVE slot+0xA0 and shortTask+0x80 alias.

This is a memory-address field alias verified by Win64 stack-frame arithmetic,
not a runtime identification of a player's RMB/Shift or a physics bug root cause.
"""
import argparse, json, struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE, SHA

PINS={
 0x03025D7F:'55',0x03025D80:'4156',0x03025D82:'4157',
 0x03025D84:'488da848ffffff',0x03025D8B:'4881eca0010000',
 0x03025DD7:'4c8db3a0000000',0x03025DE1:'4d8b1e',
 0x03025E35:'41ff4b18',0x03025E39:'49893e',
 0x0302608D:'4c897590',0x0302609F:'4c8d4c2440',
 0x030260AF:'e88066f0ff',
 0x02F2C758:'4c8d4130',0x02F2C770:'498bd1',
 0x02F2C781:'498bc8',0x02F2C784:'e8ab000000',
 0x02F2C789:'4c899b90000000',0x02F2C793:'4c899b98000000',
 0x02F2C7BF:'e81c280200',0x02F2C7C7:'755e',0x02F2C81B:'e8244e0100',
 0x02F2C8A7:'488b4250',0x02F2C8AB:'48894150',0x02F2C8B9:'c3',
 0x02F4EFE0:'488b8180000000',0x02F4EFEC:'488b00',0x02F4EFEF:'c3',
 0x02F4EFF0:'488b8198000000',0x02F4EFF7:'c3',
 0x02F41651:'4883b98000000000',0x02F41669:'e8bed61c00',
 0x02F4166E:'488b8b80000000',0x02F41675:'488901',
 0x02F4167A:'e8add61c00',0x02F4167F:'48898398000000',
 0x03040906:'498991a0000000',
}
E8={0x030260AF:0x02F2C734,0x02F2C784:0x02F2C834,
    0x02F2C7BF:0x02F4EFE0,0x02F2C81B:0x02F41644,
    0x02F41669:0x0310ED2C,0x02F4167A:0x0310ED2C}
LEAF=((0x02F2C834,0x02F2C8BA),(0x02F4EFE0,0x02F4EFF8))

def stack_alias_matches(entry_sp=0):
    # 0x03025D7F..0x03025D82: three pushes. RBP=entrySP-0xB8.
    # RSP=entrySP-3*8-0x1A0. Descriptor=&[rsp+0x40].
    # offset +0x50 is [rsp+0x90] = [rbp-0x70].
    return (entry_sp-0xb8-0x70)==(entry_sp-3*8-0x1a0+0x40+0x50)

def decoded_pins_are_exact(exe):
    pe=OriginalEXE(exe)
    try:
        if pe.sha!=SHA:raise ValueError('EXE_SHA_MISMATCH')
        cache={}
        for rva,op in PINS.items():
            raw=bytes.fromhex(op)
            if pe.section(rva)!='.00cfg' or pe.read(rva,len(raw))!=raw:
                raise ValueError('INSTRUCTION_DRIFT:'+hex(rva))
            owner=pe.owner(rva)
            if owner:
                b=owner[:2]
            else:
                b=next(((lo,hi) for lo,hi in LEAF if lo<=rva<hi),None)
                if not b:raise ValueError('UNWINDLESS_OWNER_UNKNOWN:'+hex(rva))
            if b not in cache:cache[b]=pe.starts_in(*b)
            if rva not in cache[b]:raise ValueError('MID_INSTRUCTION:'+hex(rva))
        for rva,target in E8.items():
            b=pe.read(rva,5)
            if b[0]!=0xe8 or rva+5+struct.unpack_from('<i',b,1)[0]!=target:
                raise ValueError('E8_DRIFT:'+hex(rva))
        if not stack_alias_matches():raise ValueError('STACK_ALIAS_DRIFT')
        if pe.owner(0x02F2C834) or pe.owner(0x02F4EFE0):
            raise ValueError('LEAF_OWNER_CHANGED')
        # The queued task setter stores bigTask into the same slot field.
        return {
            'schema':'bsc.n1.wh3_original_move_slot_to_shorttask_big_task_alias.v1',
            'sha256':pe.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
            'verified_instruction_starts':len(PINS),'verified_e8':len(E8),
            'win64_stack_alias':True,
            'shorttask_plus80_is_address_of_move_slot_plusA0':True,
            'shorttask_getter_derefs_move_slot_plusA0':True,
            'fresh_task_creator_writes_new_bigTask_to_move_slot_plusA0_if_null':True,
            'old_bigTask_may_be_cleared_in_activation_compatibility_gate':True,
            'different_shortTask_can_observe_same_bigTask_after_successful_handoff':True,
            'player_shift_instance_bound':False,
            'member_goal_generation_conflict_proven':False,
            'native_patch_authorized':False}
    finally:pe.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--out',type=Path)
    args=p.parse_args()
    if args.out and args.out.resolve()==args.exe.resolve():p.error('EXE_OVERWRITE_FORBIDDEN')
    result=decoded_pins_are_exact(args.exe)
    if args.out:
        args.out.parent.mkdir(exist_ok=True,parents=True)
        args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('EXACT_STATIC_PASS',result['verified_instruction_starts'],'pins',result['verified_e8'],'E8; NO GAMEPLAY PATCH')
if __name__=='__main__':main()
