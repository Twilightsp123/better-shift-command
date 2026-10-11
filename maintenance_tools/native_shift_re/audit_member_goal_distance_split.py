#!/usr/bin/env python3
"""Exact-exe-pinned native B member goal flag/distance split. Read-only.

Verifies X64 byte sites, CALL edges and the squared-distance threshold 25.0.
Static conditional native behavior is not a claim about V3 runtime or a patch.
"""
from pathlib import Path
import argparse, json, struct, sys
from audit_wh3_full_native_chain import StrictPE
GUARDS={
 'B_ctor_write_task70':(0x3263f26,'884370'),
 'B_cache_read_task70':(0x328156b,'8a4170'),
 'B_cache_stack_flag':(0x328156e,'8844242c'),
 'B_cache_pass_struct':(0x32815b5,'4c8d4c2420'),
 'fanout_read_struct_c':(0x3265c61,'418a470c'),
 'fanout_pass_flag_arg':(0x3265c65,'88442420'),
 'packet_read_stack_flag':(0x326a3ec,'0fb67c2470'),
 'packet_set_r9d_flag':(0x326a407,'448bcf'),
 'packet_write_plus38':(0x2f5f94b,'45894a38'),
 'deferred_task_packet_plus40':(0x2f5f7e7,'488d4f40'),
 'packet_copy_38_read':(0x2d99fb3,'8b4238'),
 'packet_copy_38_write':(0x2d99fb6,'894138'),
 'task_action_code_74':(0x2f7a002,'8b4174'),
 'task_special_code_67_69':(0x2f7a00b,'83f802'),
 'task_override_bit10':(0x2f7a014,'f6819000000010'),
 'actor_goal_delta_x':(0x2f7a040,'f3410f5c9188000000'),
 'actor_goal_delta_z':(0x2f7a069,'f3410f5c8990000000'),
 'squared_distance_threshold_compare':(0x2f7a07f,'0f2f0dee8c9c00'),
 'skip_near_if_not_below':(0x2f7a086,'730a'),
 'near_flag_is_one':(0x2f7a088,'837b7801'),
 'near_flag_clear':(0x2f7a08e,'44894378'),
 'choose_branch_by_deferred_flag':(0x2f7a092,'44394378'),
 'actor_virtual_580':(0x2f7a116,'ff9080050000'),
 'actor_virtual_568':(0x2f7a17d,'ff9068050000'),
 'fresh_move_to_group_rebuild':(0x3032965,'e8dab1ffff'),
 'fresh_group_native_fanout':(0x302dbdb,'e8b0780a00'),
 'native_member_receiver_v368':(0x30d550f,'ff9068030000'),
 'deferred_580_action_calls_goal_writer':(0x325ea85,'e87a33e1ff'),
 'member_motor_goal_field':(0x311963a,'0f1187e0010000'),
}
EDGES={
 0x32815c5:0x3265b24,0x3265c69:0x326a3a0,
 0x326a423:0x2f5f8dc,0x326a466:0x2f5f8dc,
 0x2f5f7ee:0x2d99f74,0x2f56479:0x2f4f514,
 0x2f4f62c:0x3279ee8,0x3279f71:0x3263ec4,
 0x3032965:0x302db44,0x302dbdb:0x30d5490,
 0x325ea85:0x3071e04,0x3119687:0x3102ca4,
}
THRESHOLD_RVA=0x3942d74

def select_actor_action(code,task_flag,dx,dz,override=False):
    """Reduced native conditional branch, not a physical motion simulator."""
    if code not in (0x67,0x68,0x69) or override:return 'v568'
    flag=0 if task_flag==1 and dx*dx+dz*dz<25.0 else task_flag
    return 'v580' if flag==0 else 'v568'

def verify_original(exe:Path):
    p=StrictPE(exe)
    try:
        for name,(site,hx) in GUARDS.items():
            if p.read(site,len(hx)//2,True).hex()!=hx:
                raise ValueError('OPCODE_GUARD_MISMATCH:'+name)
        for site,target in EDGES.items():
            data=p.read(site,5,True)
            if data[0]!=0xe8 or site+5+struct.unpack_from('<i',data,1)[0]!=target:
                raise ValueError('NATIVE_EDGE_MISMATCH:'+hex(site))
        d=struct.unpack('<f',p.read(THRESHOLD_RVA,4))[0]
        if d!=25.0:raise ValueError('DISTANCE_THRESHOLD_CHANGED')
        return {
          'sha256':p.sha,'grade':'EXACT_ORIGINAL_EXE_STATIC_ONLY',
          'instruction_guards':len(GUARDS),'verified_call_edges':len(EDGES),
          'horizontal_squared_distance_gate':d,
          'provenance':[
            'B cache subtype+0x70 -> member fanout packet arg flag',
            'packet+0x38 via copy into deferred task+0x78',
            'per-member horizontal XZ distance <5 clears task+0x78 only if ==1',
            'branch v580 vs v568 depends on special action code, flag and distance',
            '0x02F561E8 MOVE callback has conditional E8 to 0x02F4F514 -> 0x03279EE8 -> B cached subtype',
            'fresh RMB conditional issuer 0x030323C8->0x0302DB44->0x030D5490'
          ],
          'counterexample':{'near4_flag1':select_actor_action(0x68,1,4,0),
                            'far6_flag1':select_actor_action(0x68,1,6,0)},
          'v3_branch_observed':False,'safe_patch_authorized':False,
          'gameplay_causality_proven':False}
    finally:p.close()

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--exe',required=True,type=Path)
    a.add_argument('--out',required=True,type=Path)
    args=a.parse_args()
    if args.exe.resolve()==args.out.resolve():a.error('REFUSE_EXE_OVERWRITE')
    try:
        proof=verify_original(args.exe)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
        print('STATIC PASS',len(GUARDS),'byte guards',len(EDGES),'native calls; NO PATCH')
    except (OSError,ValueError,struct.error) as e:
        print('NATIVE_GOAL_SPLIT_REFUSED',e,file=sys.stderr)
        return 2
    return 0

if __name__=='__main__':sys.exit(main())
