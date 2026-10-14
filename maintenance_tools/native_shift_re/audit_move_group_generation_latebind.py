#!/usr/bin/env python3
"""BSC N1 exact-WH3-9.0.3 static late-bound MOVE group / pooled generation.

Proves the specific late lookup from shortTask+8 (UnitRoot) to CURRENT
root+0x32F8 and that this field can be replaced via group pool reuse.
This is a structural ordering counterexample, NOT actual Shift runtime proof.
Never patches EXE, writes to the game process, or uploads pointers.
"""
import argparse
import json
import re
import shutil
import struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
PINS={int(s,16):bytes.fromhex(b) for s,b in (line.split() for line in """
02F2C734 4053
02F2C74D 48895108
02F2C777 488d059af6b800
02F2C77E 488901
02F562DE e8fd8cffff
02F562E3 83782004
02F562F2 40387024
02F5630C 40387374
02F56358 e80bda3000
02F56365 4c899b90000000
02F5636C e86f8cffff
02F56371 f3410f104328
02F56377 f3410f104b2c
02F56389 498b4338
02F56394 498b4340
02F563F4 488b4b08
02F563F8 488d542450
02F563FD 488b89f8320000
02F56404 e8373a3200
02F56409 e9a9000000
02F564B7 4038b3a0000000
02F564C4 4038b3a1000000
02F564CB 0f85ee000000
02F5650A 488b5308
02F5650E 488bba98320000
02F56515 8b8294320000
02F5652D 493988f8320000
02F56536 e889951700
02F5655C 488bba78320000
02F5657B 493988f8320000
02F56584 e83b951700
030197B7 488b5918
030197BE 8b4114
030197C7 488b4708
030197CB 488b13
030197CE 488b8840040000
030197D5 488b8950010000
030197DC 4883c158
030197E0 e8ef2a0100
030197EE 83671400
0301B86D 488bba50010000
0301B874 488b5f58
0301B87D 488b5f60
0301B8A8 488b0b
0301B8AB 488d542420
0301B8B0 48894f58
0301B8B7 e880730a00
0301B8BC 488d4e10
0301B8C5 488d542450
0301B8CA e8659b30fe
0301B8F3 488db980320000
0301B8FD 488bcf
0301B902 e8a1deffff
0301B91F e810ffffff
0301B96D 48899ef8320000
0302C2DE 488b02
0302C2E1 488bfa
0302C2E4 488bd9
0302C2E7 33d2
0302C2EC ff5010
0302C2EF 488b03
0302C2F2 488907
0302C2F5 48893b
0302DB8E e851ddfeff
0302DBDB e8b0780a00
030C2C61 e8da000000
030C2C68 488d0d81c98400
030C2C6F 48890b
030C2C7D 488983100a0000
030C2C9B 4889ab300b0000
030C2D44 48894108
030C2D4E 48894110
030C61DE 8bda
030C61E3 e860e5ffff
030C61E8 f6c301
030C61EB 740d
030C61ED bad8d00000
030C61F5 e83a4742fd
030D54CA 41ff5248
030D54D5 488b4728
030D54D9 4c8d0476
030D54E6 4c03442440
030D54F0 488b1cf0
030D54F7 450fb74822
030D54FC e867a3e8ff
030D550F ff9068030000
03279E4A 488b4110
03279E54 488b8840040000
03279E62 e89d8fb4ff
03279E69 744f
03279EB3 e894b6e5ff
""".strip().splitlines())}
DIRECT_E8={int(s,16):int(t,16) for s,t in (line.split() for line in """
02F562DE 02F4EFE0
02F56358 03263D68
02F5636C 02F4EFE0
02F56404 03279E40
02F56536 030CFAC4
02F56584 030CFAC4
030197E0 0302C2D4
0301B8B7 030C2C3C
0301B8CA 01325434
0301B902 030197A8
0301B91F 0301B834
0302DB8E 0301B8E4
0302DBDB 030D5490
030C2C61 030C2D40
030D54FC 02F5F868
03279E62 02DC2E04
03279EB3 030D554C
030C61E3 030C4748
030C61F5 04EA934
""".strip().splitlines())}
NO_UNWIND_LEAF=(0x030C2D40,0x030C2DC6)
TYPED_METHODS={
 0x0390F5F0+0x10:0x030C61D4,   # true pooled group vtable destructor
 0x03ABBE18+0x10:0x02F561E8,  # short MOVE task native update
 0x0390B4F0+0x08:0x03025D70,  # active MOVE slot
}

def simulate_hypothetical_sequence(*,refresh_before_tick, recycle_same_address, old_tick_enabled):
    """Offline decision example, not a claim about actual scheduling.

    Epochs are synthetic tags and are NOT known fields inside WH3 structures.
    """
    initial_address=0x1000
    root={'group_address':initial_address, 'group_epoch':0}
    task={'root':root, 'source_epoch':0}
    if refresh_before_tick:
        root['group_epoch']=1
        root['group_address']=(initial_address if recycle_same_address else 0x2000)
    if not old_tick_enabled:
        return {'fanout':False,'cross_epoch':False,
                'same_address_as_creation':root['group_address']==initial_address}
    observed=root['group_epoch']
    return {'fanout':True,'cross_epoch':observed!=task['source_epoch'],
            'same_address_as_creation':root['group_address']==initial_address,
            'task_epoch':task['source_epoch'],'current_group_epoch':observed}

def instruction_starts(pe):
    if not shutil.which('objdump'):
        raise ValueError('OBJDUMP_REQUIRED')
    owners={}
    for at,pattern in PINS.items():
        if pe.read(at,len(pattern),True)!=pattern:
            raise ValueError('EXACT_OPCODE_DRIFT:'+hex(at))
        owner=pe.function(at)
        if owner is None and NO_UNWIND_LEAF[0]<=at<NO_UNWIND_LEAF[1]:
            owner=NO_UNWIND_LEAF
        if owner is None:
            raise ValueError('NO_UNWIND_OR_EXPLICIT_LEAF:'+hex(at))
        if owner not in owners:
            asm=pe.disasm(owner[0],owner[1]-owner[0]);starts=set()
            for line in asm.splitlines():
                m=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',line)
                if m: starts.add(int(m.group(1),16))
            owners[owner]=starts
        if at not in owners[owner]:
            raise ValueError('MID_INSTRUCTION:'+hex(at))
    return len(owners)

def audit(exe):
    pe=StrictPE(Path(exe))
    try:
        if pe.sha!=SHA:raise ValueError('WRONG_EXE_SHA')
        n_owners=instruction_starts(pe)
        if pe.read(0x030C2DC5,3,True)!=b'\xc3\xcc\xcc':
            raise ValueError('NO_UNWIND_GROUP_BASE_END_CHANGED')
        for at,target in DIRECT_E8.items():
            raw=pe.read(at,5,True)
            if raw[0]!=0xe8 or at+5+struct.unpack_from('<i',raw,1)[0]!=target:
                raise ValueError('DIRECT_CALL_CHANGED:'+hex(at))
        for at,target in TYPED_METHODS.items():
            if struct.unpack('<Q',pe.read(at,8))[0]!=pe.base+target:
                raise ValueError('TYPED_VTABLE_CHANGED:'+hex(at))
        if PINS[0x0301B8B0]!=bytes.fromhex('48894f58'):
            raise ValueError('POOL_POP_IDENTITY_CHANGED')
        if PINS[0x0302C2F5]!=bytes.fromhex('48893b'):
            raise ValueError('POOL_PUSH_IDENTITY_CHANGED')
        if PINS[0x0302C2E7]!=bytes.fromhex('33d2') or PINS[0x030C61E8]!=bytes.fromhex('f6c301'):
            raise ValueError('POOL_DEALLOCATE_FLAG_DRIFT')
        if PINS[0x030C61EB]!=bytes.fromhex('740d') or 0x030C61EB+2+struct.unpack('<b',PINS[0x030C61EB][1:])[0]!=0x030C61FA:
            raise ValueError('POOL_NONFREE_PATH_CHANGED')
        # The cleanup compare is a CURRENT root-group pointer comparison and
        # occurs in a later state path. It is not a verified generation guard.
        if PINS[0x02F5652D]!=bytes.fromhex('493988f8320000'):
            raise ValueError('AFTER_DISPATCH_CLEANUP_COMPARE_CHANGED')
        return {
            'schema':'bsc.n1.short_move_task_group_generation_late_binding.v1',
            'exe_sha256':pe.sha,
            'proof_grade':'EXACT_ORIGINAL_EXE_STATIC',
            'code_opcode_and_objdump_starts':len(PINS),
            'verified_function_or_leaf_bodies':n_owners,
            'direct_E8_edges':len(DIRECT_E8),
            'typed_vtable_slots':len(TYPED_METHODS),
            'group_rebuild':{
              'entry':'0x0301B8E4',
              'root_group_list':'root+0x3280',
              'recycle_old':'0x030197A8 -> 0x0302C2D4',
              'destructor_type':'vtable 0x0390F5F0 +0x10 = 0x030C61D4',
              'destructor_dealloc_flag':'0 at 0x0302C2E7, so 0x030C61EB skips heap free',
              'return_to_pool':'context+0x440+0x150+0x58',
              'reacquire_pool':'0x0301B834 reads same pool +0x58',
              'reinitialize':'0x030C2C3C installs group vtable 0x0390F5F0',
              'current_group_write':'0x0301B96D [root+0x32F8]=new group'},
            'task_callback':{
              'short_task_constructor':'0x02F2C734 stores UnitRoot at +0x08',
              'task_tick':'0x02F561E8',
              'conditional_group_read':'0x02F563F4 [shortTask+8] -> 0x02F563FD [UnitRoot+0x32F8]',
              'task_local_geometry_source':'0x02F56358 constructs descriptor from shortTask fields +0x20/+0x30',
              'group_dispatch':'0x02F56404 -> 0x03279E40',
              'task_status_gates':'shared status +0x20=4 and +0x24 != 0, shortTask+0x74 flag',
              'post_dispatch_cleanup':'separate task+0xA0/+0xA1 checks; compare root group with group lists at 0x02F5652D/0x02F5657B'},
            'live_root_group_is_read_at_task_update_not_fixed_at_creation':True,
            'group_address_may_be_reused_across_reinitialization':True,
            'pointer_equality_implies_same_generation':False,
            'group_generation_token_in_original_proven':False,
            'old_task_survives_group_rebuild_in_actual_shift_proven':False,
            'old_task_packet_dispatched_into_new_group_in_game_proven':False,
            'final_motor_crowding_causality_proven':False,
            'native_patch_authorized':False,
            'offline_counterexamples':{
              'group_pointer_reused':simulate_hypothetical_sequence(refresh_before_tick=True,recycle_same_address=True,old_tick_enabled=True),
              'different_pointer':simulate_hypothetical_sequence(refresh_before_tick=True,recycle_same_address=False,old_tick_enabled=True),
              'no_refresh':simulate_hypothetical_sequence(refresh_before_tick=False,recycle_same_address=True,old_tick_enabled=True),
              'task_retired':simulate_hypothetical_sequence(refresh_before_tick=True,recycle_same_address=True,old_tick_enabled=False)},
        }
    finally:pe.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.exe.resolve()==args.out.resolve():p.error('NEVER_OVERWRITE_EXE')
    report=audit(args.exe)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('STATIC PASS',report['code_opcode_and_objdump_starts'],'code starts,',report['direct_E8_edges'],'E8,',report['typed_vtable_slots'],'typed slots; NOT A PATCH')
if __name__=='__main__':main()
