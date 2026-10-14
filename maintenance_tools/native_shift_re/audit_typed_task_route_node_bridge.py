#!/usr/bin/env python3
"""WH3 exact 9.0.3 typed B-family auxiliary task -> route node lineage.

Read-only machine-code evidence only. The auxiliary +0x20 can carry a native
big-task pointer, and its associated route-node constructor consumes task
fields including +0x158. This is NOT proof that a Shift-instance took this
branch or that the original geometry is wrong. No EXE writes, no hooks.
"""
import argparse
import json
import re
import shutil
import struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

SHA = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'

# All pins are frozen from verified instruction *starts* on the exact original.
PINS = {int(a,16):bytes.fromhex(h) for a,h in (line.split() for line in r'''
02F562FC 498bce
02F5630C 40387374
02F56310 0f84f8000000
02F5632B f30f104378
02F5633A 4533c9
02F5634A 4c89442428
02F5634F 4c8b4308
02F56353 4889742420
02F56358 e80bda3000
02F56365 4c899b90000000
02F56381 4889442450
02F563EB 4c895c2458
02F563F4 488b4b08
02F563F8 488d542450
02F563FD 488b89f8320000
02F56404 e8373a3200
02F5640E e8ed2f58fd
02F5641E e8bd8bffff
02F56423 4c8b4308
02F56427 488d5320
02F5642B 4c8bc8
02F5642E 498bca
02F56431 e846da3000
030EC9EC 488b02
030EC9EF 488901
030EC9F2 488b4208
030ECA24 0fb74238
030ECA38 8b4244
030ECA44 0fb6424c
030ECA4E c3
030ECB10 4053
030ECB1B 488b542470
030ECB23 4c894918
030ECB2E 66c741080100
030ECB34 4c894110
030ECB38 4883c120
030ECB3C e8abfeffff
030ECB41 488b4c2478
030ECB4B 4c894b70
030ECB4F f30f1081800000
030ECB66 488b9158010000
030ECB98 e847160100
030ECBA2 48894370
030ECBB8 e8b31b0200
030FE1E4 48895c2408
030FE1F3 488bf9
030FE20E 488b4f50
030FE24A 488b9040040000
030FE251 488d4748
030FE255 4889442428
030FE272 e8653dfcff
030FE280 488d5318
030FE28C 488b5b08
030FE290 4885db
030FE293 75eb
0311E580 488b9f60010000
0311E63B 807f2401
0311E645 488b8758010000
0311E64C 48894320
0311E6EC 4c89af58010000
031219B0 48895c2408
03121A0B 488b03
03121A25 6683630800
03121A33 488d4b20
03121A39 c7430401000000
03121A40 e8a7affcff
03121A45 4883637000
03121A4D e81ecdfeff
03121A58 4883bfd0020000
03121A62 48899fd0020000
03121A69 488b4708
03121A91 488d4f18
03121A95 488d5320
03121A99 e8febffdff
03121A9E 48894370
03121AA2 c6430801
03121ABC 48895c2408
03121AD6 488b89e0020000
03121B29 4c8b87d8020000
03121B30 8b974c0b0000
03121B36 4889742428
03121B3B 48896c2420
03121B40 e8cbaffcff
03121B4B 4883bfd0020000
03121B55 488987d0020000
03121B6B 488987d8020000
03128E80 48895c2408
03128EA8 488bbbf0010000
03129031 488bbbd0020000
03129059 44396704
03129078 44386708
0312907C 7524
0312907E 488d5720
03129085 e88e2dffff
0312908C 7414
0312908E 488d4b18
03129092 e8054afdff
03129097 48894770
0312909E 44886f08
03263AB0 48895c2410
03263AC5 e8d6fae5ff
03263ACA 4883674000
03263ACF 488d0552c68700
03263AD6 488907
03263AEB 498b03
03263AEE 48894750
03263AF2 498b4308
03263AF6 48894758
03263B95 4883a790000000
03263B9D 4883a798000000
03263C2C 488b4750
03263C35 ff4018
03263D68 488b4208
03263D6C 4c8b542428
03263D71 f30f10442448
03263D77 488901
03263D83 48894108
03263D87 4c895120
03263D8B 4c894110
03263DD9 4d85d2
03263DDE 41ff4218
03263DE5 c3
03263E5D 4c894c2428
03263E6B 4533c0
03263E7C 4883ec58
03263EAC 4c894c2420
03263EB4 e8affeffff
03263ED5 488d150cc28700
03263EDC 488913
03263FE4 488d151dc18700
03263FEE 488913
0326775C 4883ec48
03267795 4d8902
032677C7 41834a48ff
032677E7 488b5010
0326780F e89c52e8ff
03279E62 e89d8fb4ff
03279E67 84c0
03279E69 744f
03279EBA 498db9f0080000
03279EC1 488bcf
03279ED2 4c8bc3
03279ED5 488bd7
03279ED8 e8d39bfeff
03281408 4053
03281411 488b4958
0328141A 488b8b98000000
03281426 e819000000
03281444 4053
0328144A 4883792000
03281454 488b4958
03281480 4883635800
03281485 488b4320
03281497 48837b5800
0328149E 488b4320
032814A7 4883b858010000
032814AF 7466
032814B1 488d542420
032814DB 488b4308
032814E4 4c8b4320
032814EF 488b8860010000
032814F6 4d85c0
032814F9 740f
032814FB e8bc05eaff
03281500 48894358
0328150A e8a104eaff
0328150F 48894358
03281513 c6436001
'''.strip().splitlines())}
PINS[0x032814A7]=bytes.fromhex('4883b85801000000')  # objdump wraps final immediate byte

# No-PE-unwind leaves must have manually bounded end including `ret`, never
# inferred from the next nearby RVA alone.
LEAF_SPANS = {
    0x03263D68:(0x03263D68,0x03263DE6),
    0x030EC9EC:(0x030EC9EC,0x030ECA4F),
}

# The three adjacent tables are distinct installed vtables; the address
# 0x03AE0138 is NOT +0x50 on the first 0x03AE00E8 object.
INSTALLED_TABLES = {
    0x03263ED5:0x03AE00E8,
    0x03263FE4:0x03AE0108,
    0x03263ACF:0x03AE0128,
}
TYPED_METHODS = {
    0x03AE00E8+0x10:0x03281520,
    0x03AE0108+0x10:0x03281600,
    0x03AE0128+0x10:0x03281408,
}
E8 = {
    0x02F56358:0x03263D68,
    0x02F56431:0x03263E7C,
    0x02F56404:0x03279E40,
    0x02F5641E:0x02F4EFE0,
    0x03263AC5:0x030C35A0,
    0x03263EB4:0x03263D68,
    0x03279ED8:0x03263AB0,
    0x03281426:0x03281444,
    0x032814C6:0x0326775C,
    0x032814FB:0x03121ABC,
    0x0328150A:0x031219B0,
    0x03121B40:0x030ECB10,
    0x03121A40:0x030EC9EC,
    0x030ECB3C:0x030EC9EC,
    0x030ECB98:0x030FE1E4,
    0x030ECBB8:0x0310E770,
    0x030FE272:0x030C1FDC,
    0x030FE287:0x030C7858,
    0x03121A99:0x030FDA9C,
    0x03129092:0x030FDA9C,
    0x03129085:0x0311BE18,
    0x03279E62:0x02DC2E04,
}
# Gate endpoints are real x64 conditional branch targets, not guessed labels.
JCC = {
    0x02F56310:(b'\x0f\x84',0x02F5640E),
    0x03279E69:(b'\x74',0x03279EBA),
    0x032814AF:(b'\x74',0x03281517),
    0x032814F9:(b'\x74',0x0328150A),
    0x0312907C:(b'\x75',0x031290A2),
}


def checked_branch(pe,at,prefix,target):
    n=6 if len(prefix)==2 else 2
    code=pe.read(at,n,True)
    if not code.startswith(prefix):raise ValueError('JCC_OPCODE_CHANGED:'+hex(at))
    disp=struct.unpack_from('<i' if n==6 else '<b',code,2 if n==6 else 1)[0]
    if at+n+disp!=target:raise ValueError('JCC_TARGET_CHANGED:'+hex(at))


def verify_instruction_starts(pe):
    if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
    cache={}
    for at,raw in PINS.items():
        if pe.read(at,len(raw),True)!=raw:raise ValueError('OPCODE_DRIFT:'+hex(at))
        owner=pe.function(at)
        if owner is None:
            owner=next((v for v in LEAF_SPANS.values() if v[0]<=at<v[1]),None)
        if owner is None:raise ValueError('UNVERIFIED_INSTRUCTION_OWNER:'+hex(at))
        if owner not in cache:
            asm=pe.disasm(owner[0],owner[1]-owner[0])
            cache[owner]={int(m.group(1),16) for line in asm.splitlines()
               if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',line))}
        if at not in cache[owner]:raise ValueError('MID_INSTRUCTION:'+hex(at))
    for start,stop,expected in (
        (0x03263D68,0x03263DE6,b'\xc3'),
        (0x030EC9EC,0x030ECA4F,b'\xc3'),
    ):
        if pe.read(stop-1,1,True)!=expected:
            raise ValueError('LEAF_BOUNDARY_RET_CHANGED:'+hex(start))
    return len(PINS),len(cache)


def symbolic_routes(*,short_task_flag74:int, big_task_available:bool,
                    aux_route_exists:bool, old_subtask_exists:bool,
                    B_mode_allowed:bool=True):
    """Minimal *synthetic* branch fixture, not a simulation of game motion.

    Assumes other native predicates are satisfied. Used to prevent a mistaken
    unconditional claim about carrying old-task geometry. The real runtime
    has more guards, callbacks and dynamic object types.
    """
    if short_task_flag74 not in (0,1):raise ValueError('SYNTHETIC_FLAG_NOT_BOOLEAN')
    aux_big_task=bool(short_task_flag74==0 and big_task_available)
    if not B_mode_allowed:return 'NO_B_TASK_CONSTRUCTION'
    if aux_route_exists:return 'PRESERVE_EXISTING_ROUTE_NODE'
    if aux_big_task and not old_subtask_exists:return 'SKIP_NODE_WHILE_OLD_SUBTASK_NULL'
    if aux_big_task and old_subtask_exists:return 'CREATE_BIG_TASK_ANCHORED_NODE'
    return 'CREATE_GENERIC_NODE'


def audit(exe):
    pe=StrictPE(Path(exe))
    try:
        if pe.sha!=SHA:raise ValueError('EXE_SHA_MISMATCH')
        pins,owners=verify_instruction_starts(pe)
        for at,dest in E8.items():
            b=pe.read(at,5,True)
            if b[0]!=0xE8 or at+5+struct.unpack_from('<i',b,1)[0]!=dest:
                raise ValueError('E8_CHANGED:'+hex(at))
        for at,(prefix,target) in JCC.items():checked_branch(pe,at,prefix,target)
        for at,dest in INSTALLED_TABLES.items():
            ins=pe.read(at,7,True)
            if ins[:3] not in (b'\x48\x8d\x05',b'\x48\x8d\x15') or \
               at+7+struct.unpack_from('<i',ins,3)[0]!=dest:
                raise ValueError('TABLE_INSTALL_CHANGED:'+hex(at))
        for at,dest in TYPED_METHODS.items():
            if struct.unpack('<Q',pe.read(at,8))[0]!=pe.base+dest:
                raise ValueError('VTABLE_SUBCLASS_CHANGED:'+hex(at))
        if len(set(INSTALLED_TABLES.values()))!=3:
            raise ValueError('ADJACENT_TABLES_COLLAPSED')
        if 0x03AE0128+0x10 != 0x03AE00E8+0x50:
            raise ValueError('ADDRESS_ARITHMETIC_CHANGED')
        return {
            'schema':'bsc.n1.typed_big_task_to_B_route_node_static.v1',
            'sha256':pe.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
            'opcode_instruction_starts':pins,'unwind_or_pinned_leaf_owners':owners,
            'direct_E8':len(E8),'branch_targets':len(JCC),
            'vtable_RIP_installs':len(INSTALLED_TABLES),
            'typed_vtable_slots':len(TYPED_METHODS),
            'native_B_task_factory':'0x03279E40 mode-zero branch -> 0x03263AB0 installs 0x03AE0128',
            'distinct_adjacent_vtables':[hex(v) for v in INSTALLED_TABLES.values()],
            'B_vtable_plus_10':'0x03281408; NOT 0x03AE00E8+0x50',
            'short_task_flag_74_nonzero_aux':'0x02F56358 direct aux; stack arg5 zero -> aux+0x20=NULL',
            'short_task_flag_74_zero_aux':'0x02F56431 -> 0x03263E7C -> 0x03263D68; arg5 from big task getter -> aux+0x20',
            'B_task_primary_aux':'0x03263AB0 descriptor+0x08 -> B task+0x58',
            'node_creation_gate':'0x03281444: existing aux+0x58 node wins; task+0x20 nonnull with task+0x158 NULL skips; else use task-aware or generic constructor',
            'task_aware_node':'0x03121ABC -> 0x030ECB10; node+0x20 descriptor COPY, big task is separate 6th ABI argument',
            'task_aware_geometry':'0x030ECB10: task+0x80/+0x84/+0x88/+0x90/+0x98 and task+0x158 -> 0x030FE1E4 -> node+0x70',
            'task_aware_old_subtask_chain':'0x030FE1E4 enumerates oldSubtask starting at task+0x158, follows next pointer +0x08 and attaches each route+0x18 payload',
            'task_aware_route_initial_valid_flag':'0x030ECB2E writes node+0x08=1; 0x03129078/7C skips converter update on this initial valid state',
            'generic_route_initial_valid_flag':'0x03121A25 clears node+0x08; optional first converter successful path sets it at 0x03121AA2',
            'generic_node':'0x031219B0 -> 0x030EC9EC (descriptor copy); optional converter 0x030FDA9C -> node+0x70',
            'manager_route_node_list':'manager+0x2D0/+0x2D8 with node+0x18/+0x10 linkage',
            'manager_route_node_update':'0x03128E80 may call 0x030FDA9C and replace node+0x70 on independently gated branch',
            'task_aware_node_selected_for_real_player_SHIFT':False,
            'state1_old_projection_identified_as_crowding_cause':False,
            'record_i_to_motor_goal_runtime_identity_proven':False,
            'native_patch_authorized':False,
        }
    finally:pe.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.exe.resolve()==args.out.resolve():p.error('NEVER_OVERWRITE_EXE')
    r=audit(args.exe)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('PASS',r['opcode_instruction_starts'],'native instruction starts,',r['direct_E8'],'direct edges; NO PATCH')
