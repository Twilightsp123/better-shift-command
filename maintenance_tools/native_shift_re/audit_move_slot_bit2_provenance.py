#!/usr/bin/env python3
"""Original WH3 command descriptor bit2 -> MOVE slot+0x9A -> heading branch.

Read-only exact EXE SHA and machine-code evidence. Not a runtime/gameplay fix.
"""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA

PIN={
 0x030323FF:'498bf8',
 0x0303249E:'0f85fe010000',
 0x03032577:'0f8525010000',
 0x03032679:'804f5a06',
 0x030326DB:'4c8bcf',
 0x030326E4:'e8d369fdff',
 0x030090C6:'498bd9',
 0x030090DB:'488d4f40',
 0x030090DF:'488bd3',
 0x030090E2:'e819000000',
 0x03009168:'0fb6415a',
 0x03009186:'0fb6c1',
 0x03009189:'32425a',
 0x0300918C:'2404',
 0x0300918E:'32c1',
 0x03009190:'4188405a',
 0x030091D1:'c3',
 0x03025E5B:'f6839a00000002',
 0x03025E69:'0f840a010000',
}
E8={0x030326E4:0x030090BC,0x030090E2:0x03009100}
JCC={0x0303249E:0x030326A2,0x03032577:0x030326A2,0x03025E69:0x03025F79}
LEAF=(0x03009100,0x030091D2)

def copy_low_seven(dst,src):
    for k in range(7):
        mask=1<<k
        dst=((dst^src)&mask)^dst
    return dst

def samples_group_when_activated(normalized,original_flags):
    at_enqueue=(original_flags|0x06) if normalized else original_flags
    stored=copy_low_seven(0,at_enqueue)
    return (stored&0x02)==0

def audit(exe):
    pe=OriginalEXE(exe)
    try:
        if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
        start_cache={}
        for rva,hexx in PIN.items():
            b=bytes.fromhex(hexx)
            if pe.section(rva)!='.00cfg' or pe.read(rva,len(b))!=b:
                raise ValueError('OPCODE_DRIFT:'+hex(rva))
            owner=pe.owner(rva)
            if owner is None and LEAF[0]<=rva<LEAF[1]:bounds=LEAF
            elif owner is not None:bounds=owner[:2]
            else:raise ValueError('UNWIND_OWNER_MISSING:'+hex(rva))
            if bounds not in start_cache:start_cache[bounds]=pe.starts_in(*bounds)
            if rva not in start_cache[bounds]:raise ValueError('MID_INSTRUCTION:'+hex(rva))
        for site,target in E8.items():
            raw=pe.read(site,5)
            if raw[0]!=0xe8 or site+5+struct.unpack_from('<i',raw,1)[0]!=target:
                raise ValueError('E8_TARGET_DRIFT:'+hex(site))
        for site,target in JCC.items():
            raw=pe.read(site,6)
            if raw[:1]!=b'\x0f' or not (0x80<=raw[1]<=0x8f) or site+6+struct.unpack_from('<i',raw,2)[0]!=target:
                raise ValueError('JCC_TARGET_DRIFT:'+hex(site))
        if pe.owner(LEAF[0]) is not None or pe.read(0x030091D1,2)!=b'\xc3\xcc':
            raise ValueError('NO_UNWIND_LEAF_BOUNDARY_DRIFT')
        for src in range(128):
            for dst in range(128):
                if (copy_low_seven(dst,src)&0x7f)!=src:raise ValueError('BIT_COPY_MODEL_DRIFT')
        return {'schema':'bsc.n1.move_slot_flag2_provenance.v1',
           'sha256':pe.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
           'original_instruction_starts':len(PIN),'E8_targets':len(E8),'JCC_targets':len(JCC),
           'descriptor_source':'current command descriptor +0x5A at slot constructor',
           'slot_destination':'MOVE slot+0x9A',
           'copy_leaf':'0x03009100..0x030091D1',
           'pre_enqueue_mutation_site':'0x03032679 OR [descriptor+0x5A],0x06',
           'bypass_branches':['0x0303249E','0x03032577'],
           'slot_bit2_zero_routes_to_group_sample':True,
           'normalization_that_ors_0x06_excludes_group_sample':True,
           'physical_shift_key_identity_verified':False,
           'actual_member_goal_mismatch_observed':False,
           'native_gameplay_patch_authorized':False}
    finally:pe.close()

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--exe',type=Path,required=True);a.add_argument('--out',type=Path)
    v=a.parse_args()
    if v.out and v.out.resolve()==v.exe.resolve():a.error('EXE_OVERWRITE_FORBIDDEN')
    data=audit(v.exe)
    if v.out:
        v.out.parent.mkdir(parents=True,exist_ok=True)
        v.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('PASS',data['original_instruction_starts'],'opcodes',data['E8_targets'],'E8',data['JCC_targets'],'JCC; NO PATCH')
if __name__=='__main__':main()
