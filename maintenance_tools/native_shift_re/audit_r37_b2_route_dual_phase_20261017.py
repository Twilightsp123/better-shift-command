#!/usr/bin/env python3
"""BSC R37: WH3 updated-EXE B2 route producer -> gated two-phase member fanout.

Read-only, exact-SHA binary evidence. Does not monitor gameplay or authorize patch.
The synthetic phase helper documents *static branch predicates only*, not actual
state evolution, scheduling guarantees, or Shift crowding causality.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from audit_r35_group_transaction_20261017 import PE, disasm, branch_dest, SHA, IMAGE_BASE, SIZED

PIN=Path(__file__).with_name('r37_b2_route_dual_phase_pins_20261017.txt')
B2_TABLE=0x03AE5800
B2_CTOR=0x03268D34
B2_UPDATE=0x03276970
B2_TICK=0x032863A0
SENDER=0x0326A994
NODE_BUILDER=0x03126A58
RECEIVER=0x03070A48

EXPECTED_SIZES={'shortTask_B2_prepare':16,'shortTask_publish_route':10,'old_root_route_release_leaf':7,'B2_base_ctor_leaf':12,'B2_record_leaf':10,'B2_dispatch':9,'B2_ctor':12,
                'B2_vmethod_08':29,'B2_vmethod_10':25,'route_node_builder':14,
                'B2_member_sender':23,'member_receiver':16}
EXPECTED_CALLS={
    0x02F545DA:NODE_BUILDER,
    0x02F545EB:0x02F3BB44,
    0x02F3BB58:0x0301E890,
    0x02F54613:0x03268DD4,
    0x02F54628:0x0327ED4C,
    0x0327ED73:0x02DC7E30,
    0x0327EDBA:0x02F3F0FC,
    0x0327EDD5:B2_CTOR,
    0x03268D40:0x030C861C,
    0x032769D5:0x030C9C38,
    0x032769F2:SENDER,
    0x03276A4D:0x030F1ADC,
    0x03276A68:NODE_BUILDER,
    0x03286427:0x030C9C38,
    0x03286445:SENDER,
    0x03126B41:0x03102B28,
    0x0326AA05:0x030D9CEC,
    0x0326AA14:0x030D6AB8,
    0x0326AAD9:0x0326F210,
    0x0326AB19:0x02F775AC,
    0x0326ABCD:0x030E56B0,
    0x03070A7B:0x02DC7E30,
    0x03070AB3:0x02F647D0,
}
EXPECTED_JUMPS={
    0x0327698F:0x03276A0C,  # initial B2+0x60 null -> generate node
    0x032769DD:0x032769FA,
    0x03276A0A:0x03276A71, # after direct packet skip fallback
    0x032863B7:0x0328645E, # +0x80 already sent -> no repeat
    0x032863C4:0x0328646B, # no deferred node -> no send
    0x032863CE:0x0328646B, # unready node -> no send
    0x03126B31:0x03126B39, # converter mode == 1
    0x03126B37:0x03126B4E, # record+0x4C !=1 bypasses immediate converter
    0x0326ABC1:0x0326AA44, # member fanout loop back-edge
}

# These are exact GNU objdump disassemblies. Avoid accepting matching field
# offsets on unrelated object types; site and function owner both required.
EXACT_ASM={
 0x02F545DA:'call   0x3126a58',
 0x02F545E2:'mov    rdx,rax',
  0x02F545E5:'mov    rcx,rdi',
  0x02F545E8:'mov    rbx,rax',
  0x02F545EB:'call   0x2f3bb44',
  0x02F3BB97:'mov    QWORD PTR [rcx+0x18],rdx',
  0x02F3BBB8:'inc    DWORD PTR [rdx+0x4]',
  0x02F3BBBF:'mov    QWORD PTR [rax+0x270],rcx',
  0x0301E890:'cmp    BYTE PTR [rcx+0x80],0x0',
  0x0301E8A2:'dec    DWORD PTR [rax+0x4]',
 0x02F545FF:'mov    rdx,QWORD PTR [rbx+0x70]',
 0x02F54613:'call   0x3268dd4',
 0x03268E20:'mov    QWORD PTR [rcx+0x28],rdx',
 0x0327EDCE:'lea    rdx,[rbx+0x8f0]',
 0x0327EDD5:'call   0x3268d34',
 0x03268D7C:'mov    rax,QWORD PTR [r11+0x28]',
  0x030C861C:'mov    r10,rcx',
  0x030C868E:'ret',
 0x03268D80:'mov    QWORD PTR [rbx+0x60],rax',
 0x03268DBF:'and    QWORD PTR [rbx+0x78],0x0',
 0x03268DC4:'mov    BYTE PTR [rbx+0x80],0x0',
 0x03276982:'mov    rax,QWORD PTR [rcx+0x60]',
 0x0327699A:'mov    QWORD PTR [rbp-0x19],rax',
 0x032769E3:'lea    r9,[rbp-0x19]',
 0x032769F2:'call   0x326a994',
 0x03276A03:'mov    BYTE PTR [rbx+0x80],0x1',
 0x03276A0C:'mov    rax,QWORD PTR [rcx+0x78]',
 0x03276A15:'dec    DWORD PTR [rax+0x4]',
 0x03276A52:'mov    rcx,QWORD PTR [rbx+0x30]',
 0x03276A61:'mov    rcx,QWORD PTR [rax+0x160]',
 0x03276A68:'call   0x3126a58',
 0x03276A6D:'mov    QWORD PTR [rbx+0x78],rax',
 0x032863AA:'cmp    BYTE PTR [rcx+0x80],0x0',
 0x032863BD:'mov    rax,QWORD PTR [rcx+0x78]',
 0x032863CA:'cmp    BYTE PTR [rax+0x8],0x0',
 0x032863D4:'mov    rax,QWORD PTR [rax+0x70]',
 0x032863E6:'mov    QWORD PTR [rsp+0x20],rax',
 0x0328643A:'mov    r8,QWORD PTR [rbx+0x18]',
 0x03286445:'call   0x326a994',
 0x03286457:'mov    BYTE PTR [rbx+0x80],dil',
 0x03126ACD:'and    WORD PTR [rbx+0x8],0x0',
 0x03126AED:'and    QWORD PTR [rbx+0x70],0x0',
 0x03126B33:'cmp    BYTE PTR [rsi+0x4c],0x1',
 0x03126B46:'mov    QWORD PTR [rbx+0x70],rax',
 0x03126B4A:'mov    BYTE PTR [rbx+0x8],0x1',
 0x0326AA44:'mov    rax,QWORD PTR [rsi+0x28]',
 0x0326AA4B:'mov    r14,QWORD PTR [rax+rcx*8]',
 0x0326ABAF:'call   QWORD PTR [rax+0x368]',
 0x03070A87:'test   BYTE PTR [rdx+0x50],0x20',
 0x03070B2F:'mov    eax,DWORD PTR [rdi+0x104]',
 0x03070B66:'call   QWORD PTR [r11+0x100]',
 0x03070B9C:'call   QWORD PTR [r11+0xe8]',
}


def read_manifest():
    groups={};active=None
    for line in PIN.read_text('utf-8').splitlines():
        match=re.match(r'^# (\w+) bounds=([0-9A-Fa-f]+):([0-9A-Fa-f]+)',line)
        if match:
            active=match.group(1)
            if active in groups:raise ValueError('DUPLICATE_GROUP')
            groups[active]=((int(match.group(2),16),int(match.group(3),16)),{})
            continue
        words=line.split('#',1)[0].split()
        if not words:continue
        if active not in groups or len(words)!=2:raise ValueError('INVALID_PIN_ROW')
        at=int(words[0],16)
        if at in groups[active][1]:raise ValueError('DUPLICATE_PIN')
        groups[active][1][at]=bytes.fromhex(words[1])
    if {k:len(v[1]) for k,v in groups.items()}!=EXPECTED_SIZES:
        raise ValueError('PIN_INVENTORY_DRIFT')
    return groups


def phase_case(initial_route, fallback_node, fallback_ready, already_sent=False):
    """Conditional static path classification, not a simulated engine Tick.

    A route being nonnull is insufficient for actual delivery: engine memory
    allocation, indirect callees, node validity, receiver conditions and
    later member Tick state must all be satisfied in gameplay.
    """
    if already_sent:
        return 'SKIP_SECOND_CALL_ALREADY_SENT'
    if initial_route:
        return 'VIRTUAL_08_DIRECT_PACKET_CANDIDATE'
    if not fallback_node:
        return 'NO_ROUTE_NODE_YET'
    if not fallback_ready:
        return 'NODE_NOT_READY'
    return 'VIRTUAL_10_DEFERRED_PACKET_CANDIDATE'


def audit(exe):
    pe=PE(exe)
    try:
        if pe.base!=IMAGE_BASE or len(pe.d)!=SIZED:
            raise ValueError('EXE_IMAGEBASE_OR_SIZE_MISMATCH')
        with open(exe,'rb') as f: actual_sha=hashlib.file_digest(f,'sha256').hexdigest()
        if actual_sha!=SHA:raise ValueError('EXE_SHA256_MISMATCH')
        groups=read_manifest(); all_pins={}; all_asm={}; owners=set(); leafs=[]
        for name,(bounds,pins) in groups.items():
            lo,hi=bounds
            if not pe.is_executable(lo):raise ValueError('NON_EXECUTABLE_PIN_OWNER:'+name)
            if name in ('B2_record_leaf','old_root_route_release_leaf','B2_base_ctor_leaf'):
                if pe.owner(lo) is not None:raise ValueError('LEAF_OWNER_DRIFT')
                leafs.append(name)
            else:
                if pe.owner(lo)!=(lo,hi):raise ValueError('UNWIND_FUNCTION_BOUNDARY_DRIFT:'+name)
                owners.add(bounds)
            decoded=disasm(pe,lo,hi)
            for at,op in pins.items():
                if at<lo or at+len(op)>hi or at not in decoded:
                    raise ValueError('NOT_TRUE_INSTRUCTION_START:'+hex(at))
                if pe.read(at,len(op))!=op:
                    raise ValueError('OPCODE_MISMATCH:'+hex(at))
                if at in all_pins:raise ValueError('DUPLICATE_CROSS_FUNCTION_SITE')
                all_pins[at]=op
                all_asm[at]=decoded[at]
        for at,target in EXPECTED_CALLS.items():
            op=all_pins.get(at)
            if not op or len(op)!=5 or op[0]!=0xe8:
                raise ValueError('NOT_PINNED_DIRECT_CALL:'+hex(at))
            dest=at+5+struct.unpack_from('<i',op,1)[0]
            if dest!=target:raise ValueError('CALL_DESTINATION_MISMATCH:'+hex(at))
        for at,target in EXPECTED_JUMPS.items():
            if branch_dest(at,all_pins[at])!=target:
                raise ValueError('JUMP_DESTINATION_MISMATCH:'+hex(at))
        for at,expected in EXACT_ASM.items():
            if all_asm.get(at)!=expected:
                raise ValueError('SEMANTIC_SITE_MISMATCH:'+hex(at))
        table8=struct.unpack('<Q',pe.read(B2_TABLE+8,8))[0]
        table10=struct.unpack('<Q',pe.read(B2_TABLE+0x10,8))[0]
        if (table8,table10)!=(IMAGE_BASE+B2_UPDATE,IMAGE_BASE+B2_TICK):
            raise ValueError('B2_TWOPHASE_VTABLE_DRIFT')
        # Verify the new B2 table is actually installed by its constructor.
        ctor=disasm(pe,*groups['B2_ctor'][0])
        if '0x3ae5800' not in ctor[0x03268D45].lower() or 'mov    QWORD PTR [rbx],rdx'!=ctor[0x03268D4C]:
            raise ValueError('B2_CONSTRUCTOR_VTABLE_IDENTITY_DRIFT')
        # R11 is volatile under Win64: do not presume preservation. This one
        # direct helper is a no-call leaf and its *entire decoded body* neither
        # reads nor writes R11; R11=R8 remains valid at the B2 constructor use.
        helper=disasm(pe,*groups['B2_base_ctor_leaf'][0])
        if any('r11' in op.lower() or op.lower().startswith('call ') for op in helper.values()):
            raise ValueError('B2_R11_VOLATILE_HELPER_DRIFT')
        # Distinguish two same sender call sites on the *same concrete B2 object*.
        if all_asm[0x032769F2]!=all_asm[0x03286445]:
            raise ValueError('B2_DISPATCHER_NOT_SHARED')
        if not (0x03276982<0x0327698F<0x032769F2<0x03276A03<0x03276A0C<0x03276A68<0x03276A6D):
            raise ValueError('B2_UPDATE_BRANCH_ORDER_DRIFT')
        if not (0x032863AA<0x032863BD<0x032863CA<0x032863D4<0x03286445<0x03286457):
            raise ValueError('B2_DEFERRED_SEND_GATE_ORDER_DRIFT')
        return {
            'schema':'bsc.n1.r37_b2_converted_route_dual_phase.v1',
            'proof':'EXACT_SHA_NEW_EXE_NATIVE_STATIC',
            'sha256':actual_sha,'file_size':len(pe.d),'imagebase':hex(pe.base),
            'full_pinned_instruction_starts':len(all_pins),
            'unwind_functions':len(owners),'no_unwind_leafs':leafs,
            'direct_e8_target_checks':len(EXPECTED_CALLS),
            'control_transfer_target_checks':len(EXPECTED_JUMPS),
            'B2_vtable_slots_checked':2,
            'B2_identity':'B2 constructor installs 0x03AE5800; virtual+0x08 0x03276970, +0x10 0x032863A0',
            'B2_initial_route':'shortTask converter 0x02F545DA node+0x70 -> 0x03268DD4 record+0x28 -> B2 ctor +0x60',
            'root_route_holds_node_ref':'0x02F3BB44 stores node at record+0x18 and increments node+0x04, publishes record in UnitRoot+0x270; prior record cleanup 0x0301E890 conditionally decrements node+0x04',
            'B2_initial_route_has_independent_ref_proven':False,
            'B2_constructor_R11_live_across_direct_helper':'0x030C861C leaf verified to preserve R11 without nested CALL; do not generalize Win64 volatile rules',
            'B2_direct_phase':'if B2+0x60 != NULL, virtual+0x08 can call 0x0326A994 and mark B2+0x80=1',
            'B2_deferred_phase':'if B2+0x60 == NULL, virtual+0x08 calls node-builder 0x03126A58 into B2+0x78; virtual+0x10 requires node+0x08 != 0 before calling 0x0326A994',
            'shared_member_sender':'both B2 phases use 0x0326A994 -> per-member virtual+0x368; member receiver may create inline task or choose member action method',
            'sequential_B2_direct_then_deferred_duplicate_on_normal_done_path':False,
            'route_node_nonnull_when_ready_guaranteed':False,
            'route_pointer_conflict_between_same_shift_members_observed':False,
            'actual_engine_tick_schedule_verified':False,
            'shift_crowding_root_cause_proven':False,
            'gameplay_patch_authorized':False,
        }
    finally:pe.close()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    if args.out and args.out.resolve()==args.exe.resolve():ap.error('REFUSE_EXE_OVERWRITE')
    result=audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n','utf-8')
    print('R37_STATIC_PASS',result['full_pinned_instruction_starts'],'pins',
          result['direct_e8_target_checks'],'E8',result['control_transfer_target_checks'],
          'branches',result['B2_vtable_slots_checked'],'vtable slots; NO PATCH')

if __name__=='__main__':main()
