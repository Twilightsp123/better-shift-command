#!/usr/bin/env python3
"""Original WH3 native generic packet constructor -> post-constructor rewrite.

A *compatible* source for the logged 0x02/+0x44==0 payload was missed in
previous N1 notes. This is pinned static native behavior, NOT proof that
the historical battle took this branch or that Shift caused crowding.
The original EXE and user pointer logs must remain private.
"""
import argparse
from collections import Counter
import json
import struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

PINS={
 'ctor_or_06':(0x02F5F940,'80c906'),
 'ctor_plus38':(0x02F5F94B,'45894a38'),
 'ctor_plus3c':(0x02F5F92C,'f3410f11423c'),
 'ctor_qword44_three':(0x02F5F956,'49c7424403000000'),
 'ctor_flag50_store':(0x02F5F95E,'41884a50'),
 'group_task_native_vtable':(0x032659AD,'488d05547c8700'),
 'group_task_vtable_install':(0x032659B4,'488901'),
 'group_task_member_mode_copy':(0x032659CF,'418b4118'),
 'sender_ctor_call_in_new_task':(0x03265B0A,'e8f5e70100'),
 'sender_tick_period_gate':(0x03282F00,'0f2fc8'),
 'sender_tick_repeat_call':(0x03282F0F,'e8f0130000'),
 'sender_mode_in_task':(0x03284324,'8b5148'),
 'sender_member_array_pointer':(0x032844ED,'488b1cd1'),
 'sender_actor_predicate':(0x03284521,'e87ae0feff'),
 'packet_local':(0x03284B31,'488d4de0'),
 'packet_extra_arg_a':(0x03284B35,'4488442438'),
 'packet_extra_arg_b':(0x03284B3D,'44884c2430'),
 'packet_mode_to_plus38':(0x03284B45,'448b4f48'),
 'packet_heading_arg':(0x03284B49,'6689442428'),
 'packet_float_arg':(0x03284B4E,'f3440f114c2420'),
 'packet_ctor_call':(0x03284B55,'e882adcdff'),
 'packet_old_flags':(0x03284B5A,'8a4530'),
 'packet_pointer':(0x03284B5D,'488d55e0'),
 'packet_plus51_clear_bit0':(0x03284B61,'806531fe'),
 'packet_plus50_clear_bit2':(0x03284B65,'24fb'),
 'packet_plus50_merge_r14b':(0x03284B67,'410ac6'),
 'packet_ecx_zero':(0x03284B6A,'33c9'),
 'packet_plus50_write':(0x03284B6C,'884530'),
 'packet_r8_zero':(0x03284B6F,'4533c0'),
 'member_vtbl_load':(0x03284B72,'488b03'),
 'packet_plus44_zero_low32':(0x03284B75,'894d24'),
 'member_rcx':(0x03284B78,'488bcb'),
 'member_packet_v368':(0x03284B7B,'ff9068030000'),
}
CALLS={
 0x03284B55:0x02F5F8DC,
 0x03284521:0x032725A0,
 0x03265B0A:0x03284304,
 0x03282F0F:0x03284304,
 0x03279E14:0x03265964,
 0x0327D50A:0x03265964,
 0x0327D818:0x03265964,
 0x03281C9D:0x03265964,
}
VTABLES={0x03ADD618:0x03282E48}

def rewritten_flag(initial,actor_predicate):
    if not (0<=initial<=255 and 0<=actor_predicate<=255):
        raise ValueError('NOT_BYTE')
    if initial&0x06!=0x06:raise ValueError('NOT_KNOWN_CONSTRUCTOR_FLAGS')
    return ((initial & ~0x04)|actor_predicate)&0xff

def inspect_trace(log):
    flags=Counter()
    count=Counter()
    members=Counter()
    high_bytes=set()
    for line in Path(log).read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():continue
        item=json.loads(line)
        if item.get('ev')!='B_DEFERRED_RECEIVE':continue
        blob=bytes.fromhex(item['packet58'])
        if len(blob)!=0x58:raise ValueError('INVALID_PACKET_LENGTH')
        members[item['member']]+=1
        flags[blob[0x50]]+=1
        count['plus38_1']+=int(struct.unpack_from('<I',blob,0x38)[0]==1)
        count['plus3c_3f']+=int(struct.unpack_from('<f',blob,0x3c)[0]==3.0)
        count['plus44_qword_0']+=int(struct.unpack_from('<Q',blob,0x44)[0]==0)
        count['plus50_byte_02']+=int(blob[0x50]==0x02)
        count['plus51_bit0_cleared']+=int((blob[0x51]&1)==0)
        high_bytes.add(blob[0x51:0x54])
    return {'recorded_deferred_receives':sum(members.values()),
            'distinct_members':len(members),
            'field_matches':dict(count),
            'plus50_histogram':{hex(k):v for k,v in sorted(flags.items())},
            'plus50_trailing_3bytes_distinct':len(high_bytes),
            'original_sender_return_address_recorded':False}

def audit(exe,log=None):
    pe=StrictPE(exe)
    try:
        for desc,(site,expected) in PINS.items():
            if pe.read(site,len(expected)//2,True).hex()!=expected:
                raise ValueError('NATIVE_BYTE_MISMATCH:'+desc)
        for site,dest in CALLS.items():
            insn=pe.read(site,5,True)
            if insn[0]!=0xe8 or site+5+struct.unpack_from('<i',insn,1)[0]!=dest:
                raise ValueError('NATIVE_E8_MISMATCH:'+hex(site))
        for slot,dest in VTABLES.items():
            got=struct.unpack('<Q',pe.read(slot,8))[0]
            if got!=pe.base+dest:raise ValueError('GROUP_TASK_VTABLE_MISMATCH')
        # B cached-route task vtable 0x03AE00E8 is a *different class*.
        cached=struct.unpack('<Q',pe.read(0x03AE00F8,8))[0]
        if cached==pe.base+0x03282E48:
            raise ValueError('WRONG_GROUP_TASK_TYPE_ALIAS')
        lea=pe.read(0x032659AD,7,True)
        task_vtable=0x032659AD+7+struct.unpack_from('<i',lea,3)[0]
        if task_vtable!=0x03ADD608:raise ValueError('VTABLE_LEA_CHANGED')
        result={
          'schema':'bsc.n1.original_member_packet_post_ctor_rewrite.v1',
          'exe_sha256':pe.sha,'source_grade':'EXACT_ORIGINAL_EXE_STATIC',
          'opcode_guards':len(PINS),'e8_edges':len(CALLS),'vtable_types':2,
          'producer_function':'0x03284304',
          'producer_task_vtable':'0x03ADD608',
          'producer_task_tick':'0x03282E48',
          'generic_constructor':'0x02F5F8DC',
          'constructor_then_rewrite_sites':['0x03284B55','0x03284B61',
              '0x03284B65','0x03284B67','0x03284B75','0x03284B7B'],
          'packet_flag_06_rewritten_with_r14b_0':hex(rewritten_flag(6,0)),
          'packet44_qword_after_rewrite':0,
          'member_send_not_generic_untyped_offset':True,
          'old_claim_that_flag02_proves_no_02F5F8DC_source_is_invalid':True,
          'historical_sender_identity':None,
          'historical_shift_instance_execution':None,
          'safe_native_patch_authorized':False,
        }
        if log:result['private_trace_comparison']=inspect_trace(log)
        return result
    finally:pe.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--log',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.resolve()==args.exe.resolve():parser.error('NEVER_OVERWRITE_EXE')
    result=audit(args.exe,args.log)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('PASS original native:',len(PINS),'opcodes',len(CALLS),'calls; NO GAME PATCH')
if __name__=='__main__':main()
