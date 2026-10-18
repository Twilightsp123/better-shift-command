#!/usr/bin/env python3
"""BSC R41 — SHA-guarded, read-only original-WH3 typed member motion audit.

Examines the current WH3 Win64 EXE, not a live game process. The direct/indirect
call edges establish *static mechanisms*, not player Shift runtime hits or root
cause, and do not authorize any patch or injected observation.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from audit_r35_group_transaction_20261017 import PE, disasm, branch_dest, SHA, SIZED, IMAGE_BASE

HERE = Path(__file__).resolve().parent
PIN_FILE = HERE / 'r41_member_motion_integration_pins_20261018.txt'
GROUP_COUNT = 14
PIN_COUNT = 134
DIRECT_E8 = {
    0x030592F8: 0x03146FF0,
    0x030592FF: 0x0310006C,
    0x03058D5E: 0x030592BC,
    0x031000F6: 0x03146FF0,
    0x0310014C: 0x03146FF0,
    0x03100247: 0x03121F54,
    0x031471E8: 0x0316DD70,
    0x03147E4D: 0x03155DB8,
    0x03147E64: 0x03164ED0,
    0x030785B5: 0x0316460C,
    0x03048888: 0x0304C72C,
    0x03087349: 0x03059BC8,
    0x03087351: 0x0308D830,
    0x0305A06D: 0x03121F54,
}
DIRECT_BRANCH = {
    0x030592E3:0x030592FF,
    0x030592ED:0x030592F8,
    0x030592F6:0x030592FF,
    0x030592FD:0x03059304,
    0x031471B8:0x0314738F,
    0x031471C4:0x03147306,
    0x0314738A:0x031484D9,
}
MEMBER_VTABLE = {
    (0x03912950,0x18):0x03086F04,
    (0x03912950,0x20):0x030592BC,
    (0x03912950,0xF0):0x03164710,
    (0x03912950,0x100):0x030785AC,
    (0x03AD3360,0x18):0x03086224,
    (0x03AD3360,0x20):0x03058D2C,
    (0x03AD3360,0xF0):0x03164710,
}
POSITION_STORES = {
    'direct_xyz': {0x0314720B:0x88,0x03147223:0x8c,0x0314723B:0x90},
    'second_xyz': {0x03147E85:0x88,0x03147E9D:0x8c,0x03147EB5:0x90},
    'direct_motion_vector': {0x03147281:0xe0,0x03147293:0xe8},
    'second_motion_vector': {0x031483BD:0xe0,0x031483CF:0xe8},
}


def inventory(pin_file=PIN_FILE):
    data=Path(pin_file).read_text('utf-8')
    out={}
    group=None
    for line in data.splitlines():
        match=re.fullmatch(r'# (\w+) bounds=([0-9A-Fa-f]+):([0-9A-Fa-f]+) instructions=(\d+)',line)
        if match:
            name,lo,hi,n=match.groups()
            if name in out:raise ValueError('DUPLICATE_GROUP:'+name)
            out[name]={'bounds':(int(lo,16),int(hi,16)),'count':int(n),'pins':{}}
            group=name
            continue
        s=line.split('#',1)[0].split()
        if not s:continue
        if len(s)!=2 or group is None:raise ValueError('MALFORMED_PIN_ROW')
        at=int(s[0],16)
        if at in out[group]['pins']:raise ValueError('DUPLICATE_OPCODE_IN_GROUP:'+hex(at))
        out[group]['pins'][at]=bytes.fromhex(s[1])
    if len(out)!=GROUP_COUNT:raise ValueError('GROUP_COUNT_DRIFT')
    total=sum(len(g['pins']) for g in out.values())
    if total!=PIN_COUNT:raise ValueError('PIN_COUNT_DRIFT')
    if any(len(g['pins'])!=g['count'] for g in out.values()):raise ValueError('GROUP_PIN_COUNT_DRIFT')
    if len({at for g in out.values() for at in g['pins']})!=total:
        raise ValueError('DUPLICATE_OPCODE_ACROSS_GROUPS')
    return out


def is_store_to_member(op, field):
    """Check exact operand target + function-tracked RBX member identity.

    This is only valid inside common_integrator, where 0x03147019 MOV RBX,RCX.
    """
    target=f'[rbx+0x{field:x}]'
    return op.startswith(('movss  ','movsd  ','mov    ')) and target in op.split(',',1)[0]


def audit(exe):
    p=PE(exe)
    try:
        if len(p.d)!=SIZED:raise ValueError('EXE_SIZE_MISMATCH')
        if p.base!=IMAGE_BASE:raise ValueError('IMAGE_BASE_MISMATCH')
        with open(exe,'rb') as f: sha=hashlib.file_digest(f,'sha256').hexdigest()
        if sha!=SHA:raise ValueError('EXE_SHA256_MISMATCH:'+sha)
        groups=inventory();pins={};assembled={}
        for group,entry in groups.items():
            lo,hi=entry['bounds']
            if not(0<lo<hi):raise ValueError('BAD_OWNER_SPAN:'+group)
            if p.owner(lo)!=(lo,hi):raise ValueError('PE_UNWIND_DRIFT:'+group)
            if not p.is_executable(lo):raise ValueError('OWNER_NOT_EXECUTABLE:'+group)
            ops=disasm(p,lo,hi)
            assembled[group]=ops
            for at,raw in entry['pins'].items():
                if not (lo<=at<hi):raise ValueError('OUT_OF_OWNER_RANGE:'+hex(at))
                if at not in ops:raise ValueError('NOT_AN_INSTRUCTION_START:'+hex(at))
                if p.read(at,len(raw))!=raw:raise ValueError('OPCODE_DRIFT:'+hex(at))
                pins[at]=raw
        for call,destination in DIRECT_E8.items():
            raw=pins.get(call)
            if raw is None or raw[0]!=0xe8 or len(raw)!=5:
                raise ValueError('E8_NOT_PINNED:'+hex(call))
            actual=call+5+struct.unpack_from('<i',raw,1)[0]
            if actual!=destination:raise ValueError('CALL_TARGET_DRIFT:'+hex(call))
        for site,destination in DIRECT_BRANCH.items():
            if branch_dest(site,pins[site])!=destination:
                raise ValueError('BRANCH_TARGET_DRIFT:'+hex(site))
        for (table,slot),function in MEMBER_VTABLE.items():
            ptr=struct.unpack('<Q',p.read(table+slot,8))[0]
            if ptr!=IMAGE_BASE+function:raise ValueError('MEMBER_VTABLE_DRIFT:'+hex(table+slot))
        for site,target in {
            0x03052D20:0x03912950,
            0x03051F02:0x03AD3360,
        }.items():
            raw=pins[site]
            if raw[:3]!=bytes.fromhex('488d05') or len(raw)!=7:
                raise ValueError('MEMBER_CONSTRUCTOR_NOT_LEA:'+hex(site))
            if site+7+struct.unpack_from('<i',raw,3)[0]!=target:
                raise ValueError('MEMBER_CONSTRUCTOR_TABLE_DRIFT:'+hex(site))
        if pins[0x03147019]!=bytes.fromhex('488bd9'):
            raise ValueError('INTEGRATOR_OBJECT_NOT_MEMBER')
        if pins[0x030592C8]!=bytes.fromhex('488bd9'):
            raise ValueError('MEMBER_UPDATE_OBJECT_NOT_MEMBER')
        if pins[0x03058D4D]!=bytes.fromhex('488bf9'):
            raise ValueError('SPECIAL_UPDATE_OBJECT_NOT_MEMBER')
        if pins[0x03052D34]!=bytes.fromhex('488903'):
            raise ValueError('ORDINARY_MEMBER_VTABLE_WRITE_DRIFT')
        if pins[0x03051F09]!=bytes.fromhex('498907'):
            raise ValueError('SPECIAL_MEMBER_VTABLE_WRITE_DRIFT')
        for group,sites in POSITION_STORES.items():
            for site,field in sites.items():
                op=assembled['common_integrator'][site]
                if not is_store_to_member(op,field):
                    raise ValueError('INTEGRATOR_FIELD_STORE_TYPE_DRIFT:'+hex(site)+':'+op)
        # Whole executable-section E8 inventory: only three direct CALLs can
        # target this exact integrator RVA. Byte matches are also disassembled
        # at unwind-verified instruction starts, excluding embedded data bytes.
        target=0x03146FF0
        caller_candidates=[]
        for name,start,virtual,raw_size,file_off,flags in p.sections:
            if not(flags&0x20000000):continue
            chunk=p.d[file_off:file_off+raw_size]
            position=0
            while (idx:=chunk.find(b'\xe8',position))>=0:
                position=idx+1
                if idx+5>len(chunk):continue
                at=start+idx
                if at+5+struct.unpack_from('<i',chunk,idx+1)[0]==target:
                    caller_candidates.append(at)
        expected_callers={0x030592F8,0x031000F6,0x0310014C}
        if set(caller_candidates)!=expected_callers:
            raise ValueError('INTEGRATOR_DIRECT_CALLER_INVENTORY_DRIFT')
        for at in caller_candidates:
            owner=p.owner(at)
            if owner is None:raise ValueError('CALLER_WITHOUT_UNWIND_OWNER')
            if not disasm(p,*owner).get(at,'').startswith('call '):
                raise ValueError('E8_CANDIDATE_NOT_CODE_START')
        # Read-only binary value, NOT proof of a runtime constant. The divisor
        # resides in .srdata and the engine may legitimately mutate it.
        divisor_initial=struct.unpack('<I',p.read(0x03D0E294,4))[0]
        numerator_initial=struct.unpack('<f',p.read(0x03922388,4))[0]
        if divisor_initial!=100 or numerator_initial!=1000.0:
            raise ValueError('SCALING_DATA_IMAGE_DRIFT')
        # The arithmetic leading to the first XYZ stores uses this same member's
        # relative displacement. It does NOT prove who produced these deltas.
        for site,fragment in {
            0x031471F5:'addss  xmm0,DWORD PTR [rbx+0x13c]',
            0x03147213:'movss  xmm1,DWORD PTR [rbx+0x140]',
            0x0314722B:'movss  xmm0,DWORD PTR [rbx+0x144]',
            0x03147E7D:'addss  xmm0,DWORD PTR [rbx+0x88]',
            0x03147EAD:'addss  xmm0,DWORD PTR [rbx+0x90]',
        }.items():
            if fragment not in assembled['common_integrator'].get(site,''):
                raise ValueError('INTEGRATOR_DELTA_ARITHMETIC_DRIFT:'+hex(site))
        # A more meaningful provenance: the integrator itself writes accumulated
        # member movement delta (+0x13C/+0x144) before consulting bit0x02,
        # then a particular early branch resets it after position integration.
        for site,field in {0x03147199:0x13c,0x031471A1:0x144,
                           0x031472C3:0x13c,0x031472D1:0x144,
                           0x0314745D:0x140,0x03147465:0x13c,
                           0x0314746D:0x144}.items():
            op=assembled['common_integrator'].get(site,'')
            if not is_store_to_member(op,field):
                raise ValueError('INTRA_INTEGRATOR_DELTA_WRITER_DRIFT:'+hex(site))
        if not (0x03147199<0x031471B5<0x0314720B<0x031472C3):
            raise ValueError('INTEGRATOR_DELTA_TIME_ORDER_DRIFT')
        # Typed actual packet writers set bit2 while clearing bit8.
        flag_operands={
          'packet_simple_position_writer':(0x03164670,0x03164676,0x0316467F,0x03164681),
          'packet_complex_position_writer':(0x03164471,0x03164477,0x03164480,0x03164482),
        }
        for name,(load,mask,add,store) in flag_operands.items():
            if pins[mask]!=b'\x24\xf7' or pins[add]!=b'\x0c\x02':
                raise ValueError('PACKET_MEMBER_FLAG_SEMANTIC_DRIFT:'+name)
            if not('[rdi+0x108]' in assembled[name][load] or '[rdi+0x108]' in assembled[name][store]
                 or '[rsi+0x108]' in assembled[name][load] or '[rsi+0x108]' in assembled[name][store]):
                raise ValueError('PACKET_MEMBER_FLAG_TYPE_DRIFT:'+name)
        if pins[0x031471B5]!=bytes.fromhex('f6c202'):
            raise ValueError('INTEGRATOR_BIT2_GATE_CHANGED')
        if pins[0x031471C1]!=bytes.fromhex('f6c104'):
            raise ValueError('INTEGRATOR_SECONDARY_FLAG_CHANGED')
        # Sequential local proof only: the pointer/membership of the three
        # UnitRoot object-array collections has NOT been fully typed to member.
        array_method_sites=(0x0304C75D,0x0304C788,0x0304C7B3)
        if any(pins[x]!=bytes.fromhex('ff5020') for x in array_method_sites):
            raise ValueError('UNITROOT_GENERIC_VIRTUAL_DISPATCH_DRIFT')
        return {
          'schema':'bsc.n1.r41_typed_member_integrator.v1',
          'proof':'EXACT_SHA_READONLY_STATIC_NEW_EXE',
          'exe_sha256':sha,'exe_size':len(p.d),'image_base':hex(p.base),
          'verified_groups':len(groups),'verified_unwind_function_spans':len(assembled),
          'verified_instruction_starts':len(pins),'verified_e8_targets':len(DIRECT_E8),
          'verified_all_executable_section_direct_integrator_callers':len(caller_candidates),
          'verified_branch_targets':len(DIRECT_BRANCH),'verified_vtable_slots':len(MEMBER_VTABLE),
          'typed_ordinary_member_vtable':hex(0x03912950),
          'typed_special_member_vtable':hex(0x03AD3360),
          'typed_movement_entry':'ordinary member vtable+0x20=0x030592BC; derived +0x20=0x03058D2C then E8 base',
          'ordinary_member_tick_separate':'ordinary vtable+0x18=0x03086F04: direct steering 0x03059BC8',
          'motion_route_gate': 'member+0x108 bit0x10 OR (member+0xB20 nonnull AND member+0xB28==4) -> 0x0310006C; else 0x03146FF0',
          'alternate_route_integrates':'0x0310006C has E8 to 0x03146FF0 at 0x031000F6 and 0x0310014C under different guards',
          'alternate_route_world_goal':'same-member +0x1E0 -> 0x03121F54 at 0x03100247; exact temporal relation to integration varies by branch',
          'typed_integrator':'0x03146FF0; member from RCX saved in RBX at 0x03147019',
          'integrator_direct_xyz_sites':[hex(x) for x in POSITION_STORES['direct_xyz']],
          'integrator_second_xyz_sites':[hex(x) for x in POSITION_STORES['second_xyz']],
          'integrator_motion_vector_sites':[hex(x) for k in ('direct_motion_vector','second_motion_vector') for x in POSITION_STORES[k]],
          'integrator_scaling_data_initial':{'numerator_float':numerator_initial,'denominator_uint':divisor_initial,'runtime_mutability_unexcluded':True},
          'integrator_delta_fields':'member+0x13C/+0x140/+0x144 are displacement deltas, also written on different branches of the SAME typed integrator; a simple branch clears deltas after XYZ updates. Other upstream writers and Shift provenance not fully proved',
          'packet_writers_flag_link':'both typed packet position writers clear bit0x08 and set bit0x02 at member+0x108; integrator tests bit0x02',
          'member_bits_link_is_same_runtime_shift_instance_proven':False,
          'unitroot_three_virtual_20_arrays':['+0x3274/+0x3278','+0x3294/+0x3298','+0x32B4/+0x32B8'],
          'unitroot_object_array_member_types_all_verified':False,
          'unitroot_arrays_guaranteed_to_schedule_this_member_under_shift':False,
          'ordinary_shift_member_integrator_dynamic_hit_proven':False,
          'same_integrator_has_delta_writers':True,
          'individual_member_delta_producers_fully_identified':False,
          'vanilla_shift_crowding_root_cause_proven':False,
          'safe_native_patch_site_established':False,
          'gameplay_patch_authorized':False,
        }
    finally:p.close()


def main():
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument('--exe',type=Path,required=True)
    arg.add_argument('--out',type=Path)
    args=arg.parse_args()
    if args.out is not None and args.exe.resolve()==args.out.resolve():
        arg.error('EXE_OVERWRITE_FORBIDDEN')
    data=audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(f"STATIC_PASS {data['verified_instruction_starts']} opcodes "
          f"{data['verified_e8_targets']} E8 "
          f"{data['verified_branch_targets']} jumps "
          f"{data['verified_vtable_slots']} member vtable slots; NO PATCH")

if __name__=='__main__':main()
