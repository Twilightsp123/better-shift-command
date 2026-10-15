#!/usr/bin/env python3
"""SHA-locked original WH3: MOVE shortTask -> ordinary B -> member motor target.

Independent type-safe static proof for the disclosed manifest; not a game patch.
Requires GNU objdump and original private EXE; public CI runs only synthetic tests.
"""
import argparse, json, struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE, IMAGEBASE
MANIFEST=Path(__file__).with_name('move_to_motor_goal_manifest.txt')
SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
LEAF_BOUNDS=((0x02F5F8DC,0x02F5F963),(0x02D99F74,0x02D9A06C))
EXPECTED=(218,28,10)

def load_manifest(path=MANIFEST):
    d={'PIN':{},'E8':{},'VT':{}}
    for no,line in enumerate(Path(path).read_text(encoding='utf8').splitlines(),1):
        line=line.split('#',1)[0].strip()
        if not line:continue
        parts=line.split()
        if not parts or parts[0] not in d:raise ValueError(f'MANIFEST_TYPE:{no}')
        kind=parts[0]
        if kind=='PIN' and len(parts)==3:
            k=int(parts[1],16);v=bytes.fromhex(parts[2]);
        elif kind=='E8' and len(parts)==3:
            k=int(parts[1],16);v=int(parts[2],16)
        elif kind=='VT' and len(parts)==4:
            k=(int(parts[1],16),int(parts[2],16));v=int(parts[3],16)
        else:raise ValueError(f'MANIFEST_FORMAT:{no}')
        if k in d[kind] and d[kind][k]!=v:raise ValueError(f'MANIFEST_CONFLICT:{no}')
        d[kind][k]=v
    if tuple(len(d[k]) for k in ('PIN','E8','VT'))!=EXPECTED:
        raise ValueError('MANIFEST_INVENTORY_DRIFT')
    return d

def shorttask_update_enters_b(big_task_state,old_reference_flag,big_task_stage):
    """One genuine 0x02F561E8 branch, not the only way into ordinary B."""
    return big_task_state==4 and old_reference_flag==0 and big_task_stage==3

def receiver_creates_inline_task(mode_helper_result,flags):
    return mode_helper_result==0 and flags&0x20==0

def record_kind(flag,member_state,allow_mapping=True,suppress_high=False):
    if not allow_mapping:return 0
    k={5:0x67,6:0x68,7:0x69,8:5,9:6}.get(flag,member_state)
    return 0 if suppress_high and 0x67<=k<=0x69 else k

def audit(exe,manifest=MANIFEST):
    ins=load_manifest(manifest)
    original=OriginalEXE(exe)  # full SHA/PE/section/image base checks
    try:
        if original.sha!=SHA:raise ValueError('SHA_MISMATCH')
        starts={}
        for rva,expected in ins['PIN'].items():
            if original.section(rva)!='.00cfg' or original.read(rva,len(expected))!=expected:
                raise ValueError('INSTRUCTION_DRIFT:'+hex(rva))
            owner=original.owner(rva)
            if owner:
                bounds=owner[:2]
            else:
                bounds=next((lo,hi) for lo,hi in LEAF_BOUNDS if lo<=rva<hi) if any(lo<=rva<hi for lo,hi in LEAF_BOUNDS) else None
            if not bounds:raise ValueError('UNWIND_OWNER_MISSING:'+hex(rva))
            if bounds not in starts:starts[bounds]=original.starts_in(*bounds)
            if rva not in starts[bounds]:raise ValueError('MID_INSTRUCTION:'+hex(rva))
        for site,target in ins['E8'].items():
            b=original.read(site,5)
            if b[0]!=0xE8 or site+5+struct.unpack_from('<i',b,1)[0]!=target:
                raise ValueError('E8_DRIFT:'+hex(site))
        for (table,slot),target in ins['VT'].items():
            actual=struct.unpack('<Q',original.read(table+slot,8))[0]
            if actual!=IMAGEBASE+target:raise ValueError('VTABLE_DRIFT:'+hex(table)+':'+hex(slot))
        for site,target in ((0x02F2C777,0x03ABBE18),
                             (0x03263ED5,0x03AE00E8),
                             (0x0324935C,0x03913808)):
            b=original.read(site,7)
            if b[:3] not in (b'\x48\x8d\x05',b'\x48\x8d\x15') or \
               site+7+struct.unpack_from('<i',b,3)[0]!=target:
                raise ValueError('CTOR_VTABLE_INSTALL_DRIFT:'+hex(site))
        b=original.read(0x0306BA60,5)
        if b[0]!=0xE9 or 0x0306BA65+struct.unpack_from('<i',b,1)[0]!=0x0306BBDA:
            raise ValueError('EARLY_RETURN_DRIFT')
        for leaf,r in ((0x02F5F962,bytes.fromhex('c3cc')),(0x02D9A06B,b'\xc3')):
            if original.read(leaf,len(r))!=r:raise ValueError('LEAF_BOUNDARY_DRIFT')
        return {
            'schema':'bsc.n1.wh3_903_typed_move_to_member_goal.v1',
            'original_exe_sha256':original.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
            'unique_instruction_guards':len(ins['PIN']),
            'direct_e8_guards':len(ins['E8']),'typed_vtable_guards':len(ins['VT']),
            'facts':[
                '0x02F561E8 guarded MOVE shortTask callback -> 0x02F4F514; constructor 0x02F2C734 also conditionally calls 0x02F4F514',
                '0x02F4F514 reads UnitRoot+0x32F8 current group and calls 0x03279EE8',
                '0x03279EE8 mode helper=0 -> 0x03263EC4 builds ordinary-B vtable 0x03AE00E8, not inherited-bigTask type 0x03AE0128',
                '0x03AE00E8+0x08 -> 0x03271B0C builds ordinary route conditionally at aux+0x78',
                '0x03AE00E8+0x10 -> 0x03281520 -> 0x03265B24 member[i]/record[i] 0x30 stride',
                'record+0x2c maps 5/6/7 to 0x67/0x68/0x69 under original flags; packet+0x34 copied into inline task+0x74',
                'member receiver mode=0 and flag missing 0x20 -> task member+0x4a8 and exits before direct pose path',
                'inline task conditionally installs member+0x328 action vtable 0x03913808',
                'member action virtual+0x10 can call 0x03071E04 -> 0x03071F20 -> conditional 0x0311954C writes member+0x1e0'],
            'limits':{'player_Shift_mode_directly_observed':False,
                      'inherited_move_state1_at_ordinary_b_branch_observed':False,
                      'same_unit_two_member_goal_generation_mismatch_proven':False,
                      'causal_crowding_root_cause_found':False,
                      'gameplay_patch_authorized':False}}
    finally:original.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--out',type=Path)
    x=p.parse_args()
    if x.out and x.exe.resolve()==x.out.resolve():p.error('CANNOT_OVERWRITE_EXE')
    result=audit(x.exe)
    if x.out:
        x.out.parent.mkdir(parents=True,exist_ok=True)
        x.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('STATIC PASS',result['unique_instruction_guards'],'opcode/starts',
          result['direct_e8_guards'],'E8',result['typed_vtable_guards'],'typed vtables; NO PATCH')
if __name__=='__main__':main()
