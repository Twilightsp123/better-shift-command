#!/usr/bin/env python3
"""Exact WH3 9.0.3: type-aware native geometry-manager bridge, no game patch.

Proof: the same manager-layout (+0x160 of route-context) is consumed by
big-MOVE-task iteration and conditional group/route conversion. The big
MOVE task's *own* +0x160 is a different field on a different object.
No observed RMB/Shift instance identity or crowding causation is inferred.
"""
import argparse
import json
import re
import shutil
import struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

SHA = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
PINS = {int(site,16):bytes.fromhex(raw) for site,raw in (
    line.split() for line in r""" 030C2C56 488b5208
 030C2C5A 4883c230
 030C2C61 e8da000000
 030C2C7D 488983100a0000
 030C2D40 488b4208
 030C2D44 48894108
 030C2D48 488b4208
 030C2D4E 48894110
 02DD5B5D 488b8f40040000
 02DD5B69 4c8bc6
 02DD5B6C e82bfcffff
 02DD57BA 488bd9
 02DD57CE 488b4308
 02DD57D2 4c8b8840040000
 02DD58D7 488b8b60010000
 02DD58DE e89d353500
 03128E9C 488bd9
 03128EA8 488bbbf0010000
 03128ED0 488b7738
 03128F17 488bd7
 03128F1D e8524fffff
 0312907E 488d5720
 0312908E 488d4b18
 03129092 e8054afdff
 03129097 48894770
 0310ED41 488b8900020000
 0310ED87 488b01
 0310EDA2 4889742428
 0310EDA7 e8a4fafdff
 0310EDC4 488bd3
 0310EDCA e8c90e0100
 0310EE26 48899ff0010000
 0310EE35 48899ff8010000
 0311DE74 488bc4
 0311DEA0 488bf1
 0311DEB2 488bfa
 0311DEC0 0f84b2060000
 0311E578 488bce
 0311E580 488b9f60010000
 0311E5B3 44886f24
 0311E636 e8d1010000
 0311E63B 807f2401
 0311E63F 0f859b010000
 0311E645 488b8758010000
 0311E64C 48894320
 0311E6A4 f30f114b48
 0311E6A9 f30f11434c
 0311E6E2 f30f114b54
 0311E6E7 f30f114350
 030D55AD 488b4310
 030D55C7 488b8840040000
 030D55DD 488b8960010000
 030D55E4 4883c118
 030D55F5 e8a2840200
 030D5603 e888feffff
 030D5490 48895c2408
 030D54CA 41ff5248
 030D550F ff9068030000
 0300889E 488b4238
 030088C2 488b8040040000
 030088C9 488b8860010000
 030088D0 e8db901100
 030088D5 48894718
 031219B0 48895c2408
 03121A74 488b8840040000
 03121A7B 488b8950010000
 03121A91 488d4f18
 03121A95 488d5320
 03121A99 e8febffdff
 03121A9E 48894370
 030FDABC 0f2970a8
 030FDAC0 488bf1
 030FDEAE ffc0
 030FDEB0 8986d0010000
 030FDF1D 8b8ed0010000
 030FDF23 4c8d4c2470
 03279EB3 e894b6e5ff""".splitlines() if line.strip()
)}
# Additional adjacent instructions needed for original-algorithm generation gating.
PINS.update({
    0x0311E6EC: bytes.fromhex('4c89af58010000'),
    0x030FE08E: bytes.fromhex('83f8ff'),
    0x030FE093: bytes.fromhex('ffc0'),
    0x030FE095: bytes.fromhex('8986d0010000'),
})
LEAF_OWNER = (0x030C2D40,0x030C2DC6)
DIRECT_CALLS = {
    0x030C2C61:0x030C2D40,
    0x02DD5B6C:0x02DD579C,
    0x02DD58DE:0x03128E80,
    0x03128F1D:0x0311DE74,
    0x03129092:0x030FDA9C,
    0x0310EDA7:0x030EE850,
    0x0310EDCA:0x0311FC98,
    0x0311E636:0x0311E80C,
    0x030D55F5:0x030FDA9C,
    0x030D5603:0x030D5490,
    0x030088D0:0x031219B0,
    0x03121A99:0x030FDA9C,
}
CHECKED_VTABLE = {0x0390B4F8:0x03025D70, 0x03ABBE28:0x02F561E8}

# Identical under same UnitRoot/context lifetime, NOT a sampled pointer address.
def native_source_names(root='UnitRoot'):
    ctx=f'MEM[{root}+0x38]'
    route_ctx=f'MEM[{ctx}+0x440]'
    manager=f'MEM[{route_ctx}+0x160]'
    return {
        'group_plus_10':ctx,
        'route_context':route_ctx,
        'shared_manager':manager,
        'group_fanout_first_converter_argument':manager+'+0x18',
        'manager_tick_first_argument':manager,
        'manager_task_node_converter_first_argument':manager+'+0x18',
        'original_route_node_converter_first_argument':manager+'+0x18',
        'queued_big_task_plus_160_alias_proven':False,
    }

def owner_of(pe,at):
    return pe.function(at) or (LEAF_OWNER if LEAF_OWNER[0]<=at<LEAF_OWNER[1] else None)

def verify_exact_instructions(pe):
    if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
    grouped={}
    for at,expected in PINS.items():
        if pe.read(at,len(expected),True)!=expected:
            raise ValueError('NATIVE_OPCODE_CHANGED:'+hex(at))
        owner=owner_of(pe,at)
        if owner is None:raise ValueError('NO_UNWIND_OR_PINNED_LEAF:'+hex(at))
        if owner not in grouped:
            text=pe.disasm(owner[0],owner[1]-owner[0])
            grouped[owner]={int(m.group(1),16) for row in text.splitlines()
               if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',row))}
        if at not in grouped[owner]:raise ValueError('MID_INSTRUCTION:'+hex(at))
    return len(PINS),len(grouped)

def audit(exe):
    pe=StrictPE(Path(exe))
    try:
        if pe.sha!=SHA:raise ValueError('EXE_SHA256_MISMATCH')
        n,owners=verify_exact_instructions(pe)
        for at,dest in DIRECT_CALLS.items():
            code=pe.read(at,5,True)
            if code[0]!=0xE8 or at+5+struct.unpack_from('<i',code,1)[0]!=dest:
                raise ValueError('E8_DESTINATION_DRIFT:'+hex(at))
        for at,dest in CHECKED_VTABLE.items():
            if struct.unpack('<Q',pe.read(at,8))[0]!=pe.base+dest:
                raise ValueError('TYPED_VTABLE_DRIFT:'+hex(at))
        if pe.read(0x030C2DC5,3,True)!=b'\xc3\xcc\xcc':
            raise ValueError('PINNED_LEAF_TERMINATOR_CHANGED')
        # Explicit source field constraints by opcode. No guessed alias.
        structural={
          0x030C2D4E:'48894110', # ctor group+0x10=context
          0x02DD5B5D:'488b8f40040000', # context+0x440
          0x02DD58D7:'488b8b60010000', # routeContext+0x160 -> manager
          0x03128EA8:'488bbbf0010000', # manager+0x1f0 big-task head
          0x0312908E:'488d4b18',       # manager+0x18 converter source
          0x03129097:'48894770',       # node+0x70 result
          0x0310EE26:'48899ff0010000', # first task in manager+0x1f0
          0x0311E580:'488b9f60010000', # bigTask+0x160 (different owner!)
          0x0311E64C:'48894320',       # nextSubtask+0x20 old ref
          0x030D55AD:'488b4310',       # group+0x10 context
          0x030D55C7:'488b8840040000', # context+0x440
          0x030D55DD:'488b8960010000', # routeContext+0x160
          0x030D55E4:'4883c118',       # manager+0x18 converter source
          0x030088C9:'488b8860010000', # original route path manager source
          0x03121A91:'488d4f18',       # manager+0x18 route node converter
          0x030FDAC0:'488bf1',         # converter first arg preserved as RSI
          0x030FDEB0:'8986d0010000',   # conditional RSI+0x1d0 bookkeeping
          0x030FE095:'8986d0010000',   # second conditional bookkeeping branch
        }
        for at,code in structural.items():
            if PINS[at].hex()!=code:raise ValueError('PROVENANCE_CONTRACT_CHANGED:'+hex(at))
        return dict(
            schema='bsc.n1.shared_move_geometry_manager_three_converter_sites.v1',
            original_exe_sha256=pe.sha,proof_grade='EXACT_EXE_STATIC',
            opcode_and_instruction_starts=n,unwind_or_explicit_leaf_owners=owners,
            verified_E8_edges=len(DIRECT_CALLS),verified_typed_vtable_entries=len(CHECKED_VTABLE),
            route_source=native_source_names(),
            route_context_tick='0x02DD5B5D -> 0x02DD579C (object+0x160) -> 0x03128E80',
            queued_big_task_head='manager+0x1F0 via 0x0310EE26 and 0x03128EA8',
            queued_big_task_state1='0x03128F1D -> 0x0311DE74; conditional state1 old projection -> nextSubtask+0x48..0x54',
            manager_node_conversion='0x0312908E RCX=&manager+0x18; 0x03129092 CALL 0x030FDA9C; node+0x70=result',
            group_fanout_conversion='0x030D55DD manager=[routeContext+0x160]; 0x030D55E4 RCX=&manager+0x18; 0x030D55F5 CALL same converter',
            route_node_conversion='0x03121A91 RCX=&manager+0x18; 0x03121A99 CALL same converter',
            converter_common_subobject_offset=0x18,
            converter_conditional_counter='[converter_first_arg+0x1D0]=[manager+0x1E8] may increment on native branches, not necessarily once per call',
            same_manager_instance_in_a_particular_SHIFT_battle_confirmed=False,
            big_task_plus160_equals_manager_plus160=False,
            manager_conversion_output_equal_to_big_task_subtask_proven=False,
            state1_projection_causes_crowding_proven=False,
            native_patch_authorized=False,
        )
    finally:pe.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.exe.resolve()==a.out.resolve():p.error('NEVER_OVERWRITE_EXE')
    r=audit(a.exe)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('PASS',r['opcode_and_instruction_starts'],'original instruction starts,',r['verified_E8_edges'],'calls; NO PATCH')
