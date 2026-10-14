#!/usr/bin/env python3
"""WH3 exact 9.0.3: per-member MOVE packet heading/position transformation.

Read-only SHA guarded native proof. No runtime pointers, hooks or gameplay patch.
Never equate record+0x22 with the final actor-facing command. The original
member receiver has additional per-member route/geometry processing.
"""
import argparse, json, re, shutil, struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

SHA = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
PINS = {int(address,16):raw for address,raw in (line.split() for line in """
02F5F86E 418b00
02F5F88C 498b4018
02F5F894 33c9
02F5F89A 8a4351
02F5F89D 24fd
02F5F8AD 6644894b40
02F5F8BD c6435026
02F5F8C1 884351
02F5F8C4 384c2450
02F5F8CD e84e2c0100
02F72526 80495102
02F7252D f6415002
02F72533 488d5940
02F72542 e831cf1000
02F72547 0fb708
02F7254A 66890b
0304DC84 488903
0304DDE6 4c89b3e8020000
0304E1A8 f30f10800c0900
0304E1B2 698190000000fd
0304E1C1 898190000000
0304E1D1 f30f590577488f
0304E1D9 f30f5805a7f38c
0304E20E f30f1183840900
0306BA2F f6425020
0306BA33 7530
0306BA65 f6425102
0306BA69 7415
0306BA75 e84e3b0100
0307F482 488b81e8020000
0307F48F 4885c0
0307F492 743a
0307F494 f30f1089840900
0307F49C 8b80cc360000
0307F4A2 f30f5c0d1ed789
0307F4AA f7d8
0307F4AC 1bc9
0307F4AE f7d1
0307F4B0 81e100400000
0307F4BD f30f59c1
0307F4C1 e88e294bfd
0307F4C6 660307
0307F4C9 668903
0307F4CE 410fb700
0307F4D2 668902
0307F4FF 488b89e8020000
0307F555 4839b5e0020000
0307F563 f30f10b5840900
0307F56B e83c24fcff
0307F570 f30f59f0
0307F574 4839b5e0020000
0307F57D 66039d80090000
0307F594 f30f5904c1
0307F599 f30f5974c104
0307F59F f30f1107
0307F5A3 f30f117704
0307F5E8 e8a3000000
0307F5ED 488b4350
0307F5F8 4c8b8840040000
0307F5FF 498bb160010000
0307F606 e865230700
0307F614 ff92c0000000
0307F61A f30f104538
0307F673 e860890800
0307F6A8 e81fda0900
0307F6C4 ff90c8000000
0307F6D6 e809feffff
0307F6EA f30f5807
0307F6EE f30f584f04
0307F6F8 f30f1107
0307F6FC f30f114f04
030C2FB4 c6412001
030C2FB8 6644894922
030C3030 c6432000
030D54B7 488d542430
030D54CA 41ff5248
030D54D9 4c8d0476
030D54E6 4c03442440
030D54EB c644242001
030D54F0 488b1cf0
030D54F7 450fb74822
030D54FC e867a3e8ff
030D550F ff9068030000
0304DC70 488d0581f88b00

""".strip().splitlines())}
E8 = {
 0x030D54FC:0x02F5F868, 0x02F5F8CD:0x02F72520,
 0x02F72542:0x0307F478, 0x0307F4C1:0x00531E54,
 0x0306BA75:0x0307F5C8, 0x0307F5E8:0x0307F690,
 0x0307F606:0x030F1970, 0x0307F673:0x03107FD8,
 0x0307F6A8:0x0311D0CC, 0x0307F6D6:0x0307F4E4,
 0x0307F56B:0x030419AC
}
MEMBER_VTABLE=0x0390D4F8
RECEIVER=0x0306B9F0
CTOR_RIP_LEA=0x0304DC70
RESULT_SCHEMA='bsc.n1.typed_move_member_packet_retarget.v1'

def symbolically_angle_offset(scalar, root_status):
    """Exact signed pre-round float expression, NOT simulation of CA movement.

    The original native leaf 0x00531E54 converts this scaled float to an int.
    No conclusion that a queued Shift actually selects this branch.
    """
    return 16384.0*(float(scalar)-0.5) if root_status == 0 else 0.0

def audit(exe):
    pe=StrictPE(Path(exe))
    try:
        if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
        if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
        owner_cache={}
        for address,expected in PINS.items():
            raw=bytes.fromhex(expected)
            if pe.read(address,len(raw),True)!=raw:
                raise ValueError('OPCODE_DRIFT:'+hex(address))
            owner=pe.function(address)
            if owner is None:raise ValueError('UNWIND_OWNER_MISSING:'+hex(address))
            if owner not in owner_cache:
                dis=pe.disasm(owner[0],owner[1]-owner[0])
                starts={int(m.group(1),16) for ln in dis.splitlines() if
                  (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',ln))}
                owner_cache[owner]=(starts,dis)
            if address not in owner_cache[owner][0]:
                raise ValueError('MID_INSTRUCTION:'+hex(address))
        for site,target in E8.items():
            code=pe.read(site,5,True)
            if code[0]!=0xe8 or site+5+struct.unpack_from('<i',code,1)[0]!=target:
                raise ValueError('E8_DRIFT:'+hex(site))
        for off,target in ((0x368,RECEIVER),(0x580,0x0306A990),(0x5B8,0x0306A8C0)):
            if struct.unpack('<Q',pe.read(MEMBER_VTABLE+off,8))[0]!=pe.base+target:
                raise ValueError('TYPED_MEMBER_VTABLE_DRIFT:'+hex(off))
        lea=pe.read(CTOR_RIP_LEA,7,True)
        if lea[:3]!=b'\x48\x8d\x05' or CTOR_RIP_LEA+7+struct.unpack_from('<i',lea,3)[0]!=MEMBER_VTABLE:
            raise ValueError('MEMBER_CONSTRUCTOR_LEA_DRIFT')
        const={
            'midpoint':(0x0391CBC8,0.5),
            'rng_scale':(0x03942A50,1.2970169336767867e-05),
            'rng_base':(0x0391D588,0.15000000596046448),
        }
        for label,(rva,expected) in const.items():
            val=struct.unpack('<f',pe.read(rva,4))[0]
            if val != expected:raise ValueError('SCALAR_CONSTANT_DRIFT:'+label)
        # Actor constructor and receiver are concrete members of the same table.
        # The payload constructor source r8 is a 0x30 record. Neither its +0x20
        # nor +0x2C flag is copied to the emitted 0x26 payload in THIS routine.
        fn=pe.function(0x02F5F868)
        asm=pe.disasm(fn[0],fn[1]-fn[0])
        reads=[ln for ln in asm.splitlines() if re.search(r'\[(?:r8)(?:\+0x[0-9a-f]+)?\]',ln)]
        if len(reads)!=5 or any('+0x20]' in ln or '+0x2c]' in ln for ln in reads):
            raise ValueError('RECORD_COPY_SOURCE_OFFSETS_CHANGED')
        if pe.read(0x00531E54,4,True)!=bytes.fromhex('0f2f0565'):
            raise ValueError('ROUNDING_LEAF_CHANGED')
        return {
            'schema':RESULT_SCHEMA,'original_exe_sha256':pe.sha,'proof':'EXACT_EXE_STATIC',
            'verified_instruction_starts':len(PINS),'verified_direct_E8':len(E8),
            'verified_typed_member_vtable_slots':3,'verified_member_vtable_LEA':1,
            'verified_float32_constants':len(const),
            'group_record_binding':'member[i] receives record[i] with stride 0x30',
            'record_heading_seed':'record+0x22 -> payload+0x40',
            'packet_ctor_fifth_bool_for_this_caller':1,
            'packet_tag_value':0x26,'packet_has_bit_0x20':True,
            'packet_postprocessor_sets_plus51_bit_2':True,
            'packet_heading_overwritten_after_formation_strategy':True,
            'heading_rule_if_member_plus2e8_nonnull_and_owner_plus36cc_zero':
              'new_heading_u16 = seed + native_round((member+0x984 - 0.5) * 0x4000)',
            'ctor_initializes_member_plus2e8_from_source':True,
            'ctor_member_plus984_source':'cached context +0x90C or LCG-derived float approximately 0.15..1.0',
            'common_receiver_uses_direct_branch_for_tag_0x26':True,
            'common_receiver_calls_0x0307F5C8_for_bit_2':True,
            'typed_member_position_adjuster':'0x0307F5C8 -> 0x0307F690 -> 0x0307F4E4 then 0x03107FD8',
            'additional_position_processing':'0x03107FD8 uses native route/space context; do not bypass',
            'record_plus20_plus2c_flags_directly_copied_to_packet':False,
            'RMB_vs_SHIFT_same_record_instance_observed':False,
            'same_unit_180_crowding_cause_proven':False,
            'native_patch_authorized':False}
    finally:
        pe.close()

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--exe',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    x=a.parse_args()
    if x.exe.resolve()==x.out.resolve():a.error('NEVER_OVERWRITE_EXE')
    result=audit(x.exe);x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('PASS',result['verified_instruction_starts'],'opcodes',result['verified_direct_E8'],'calls; NO PATCH')
if __name__=='__main__':main()
