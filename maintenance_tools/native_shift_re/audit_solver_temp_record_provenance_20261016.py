#!/usr/bin/env python3
"""Original WH3 solver virtual callbacks consume converter scratch, NOT node input.

Exact SHA, PE RVA bytes, unwind/leaf GNU objdump starts, E8/JCC. Read only.
"""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA
MANIFEST=Path(__file__).with_name('solver_temp_record_provenance_pins_20261016.txt')
LEAVES=((0x030ECA50,0x030ECAB0),(0x030EC9EC,0x030ECA50),
        (0x0312D0D0,0x0312D11E))
E8={0x030FDCE9:0x030F5AE4,0x030FDDAC:0x03125A1C,
    0x030F5B04:0x0311D0CC,0x030F5B1E:0x0312D088,
    0x0312D0A1:0x0311D0CC,0x0312D0C6:0x0312D0D0,
    0x03125AF1:0x0310FBA0,0x03271BE9:0x030ECA50}
JCC={0x03125AFD:0x031267BF,
     0x0310FBE0:0x0310FE04,0x0310FBF2:0x0310FE04}
REQUIRED={
    0x030ECA5F:'4c8911',
    0x030FDCDB:'4c8d4560',0x030FDD78:'4c8d4560',
    0x030F5B2B:'488906',0x030F5B30:'894e08',0x030F5B36:'894e0c',
    0x03125A5C:'498bf8',0x03125B0B:'488b4f08',
    0x03125B3D:'ff5008',0x03125B67:'4c8bf8',
    0x031267F9:'41ff5018',
    0x0310FBDD:'4885c9',0x0310FBED:'ff5010'
}
def pins():
    d={}
    for line_no,line in enumerate(MANIFEST.read_text('utf8').splitlines(),1):
        p=line.split('#',1)[0].split()
        if not p:continue
        if len(p)!=2:raise ValueError('PIN_ROW_DRIFT:'+str(line_no))
        site=int(p[0],16)
        if site in d:raise ValueError('DUPLICATE_PIN:'+hex(site))
        d[site]=bytes.fromhex(p[1])
    if len(d)!=60:raise ValueError('PIN_COUNT_DRIFT')
    for site,raw in REQUIRED.items():
        if d[site]!=bytes.fromhex(raw):raise ValueError('TYPED_OPERAND_DRIFT:'+hex(site))
    return d

def solver_early_gate(route_pointer_present,virtual_plus10_true):
    """A necessary predicate, not proof of virtual result1 path reachability."""
    return bool(route_pointer_present and virtual_plus10_true)

def packed_two_dwords(low,high):
    return {'low':low&0xffffffff,'high':high&0xffffffff,
            'runtime_object_pointer_proven':False}

def audit(exe):
    pe=OriginalEXE(exe)
    try:
        if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
        cache={}
        for addr,expected in pins().items():
            if pe.section(addr)!='.00cfg' or pe.read(addr,len(expected))!=expected:
                raise ValueError('OPCODE_DRIFT:'+hex(addr))
            owner=pe.owner(addr)
            span=owner[:2] if owner else next((x for x in LEAVES if x[0]<=addr<x[1]),None)
            if span is None:raise ValueError('UNWIND_OR_LEAF_OWNER_DRIFT:'+hex(addr))
            if span not in cache:cache[span]=pe.starts_in(*span)
            if addr not in cache[span]:raise ValueError('MID_INSTRUCTION:'+hex(addr))
        for site,target in E8.items():
            b=pe.read(site,5)
            if b[0]!=0xe8 or site+5+struct.unpack_from('<i',b,1)[0]!=target:
                raise ValueError('E8_DRIFT:'+hex(site))
        for site,target in JCC.items():
            b=pe.read(site,6)
            if b[:1]!=b'\x0f' or not 0x80<=b[1]<=0x8f or \
                site+6+struct.unpack_from('<i',b,2)[0]!=target:
                raise ValueError('JCC_DRIFT:'+hex(site))
        return {
          'schema':'bsc.n1.solver_temp_record_provenance.v1',
          'original_exe_sha256':pe.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
          'opcode_decoded_sites':60,'e8_targets':8,'jcc_targets':3,
          'fallback_input_record_plus00':'NULL from 0x030ECA50',
          'actual_solver_R8':'&converter local work record [RBP+0x60], built by 0x030F5AE4',
          'work_plus00':'0x0312D088 return object pointer',
          'work_plus08_0c':'two separate 32-bit copies of transformed point data',
          'special_branch_gate':'0x0310FBA0 must return 1, requiring nonnull work+0 and later virtual+0x10 success',
          'work_plus08_as_pointer':'0x03125B0B reads QWORD [work+8] before virtual+0x08',
          'return1_virtual_plus18':'0x031267F9 invokes +0x18 of object returned by previous virtual+0x08',
          'return1_reachable_for_this_work_record_proven':False,
          'return1_vtable_target_typed_proven':False,
          'return1_modifies_shared_candidate_count_proven':False,
          'gameplay_shift_crowding_cause_proven':False,
          'native_patch_authorized':False,
        }
    finally:pe.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--out',type=Path)
    args=p.parse_args()
    if args.out and args.out.resolve()==args.exe.resolve():p.error('EXE_OVERWRITE_FORBIDDEN')
    result=audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n','utf8')
    print('STATIC_PASS',result['opcode_decoded_sites'],'opcode',result['e8_targets'],'E8',result['jcc_targets'],'JCC; NO PATCH')
if __name__=='__main__':main()
