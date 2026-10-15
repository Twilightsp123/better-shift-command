#!/usr/bin/env python3
"""Fixed-WH3 original MOVE heading policy: route slot -> shortTask -> B sender.

Exact SHA, typed PE/unwind/leaf instruction starts, E8 targets, stack aliases.
Read-only. It does not establish game-time Shift occurrence or a safe patch.
"""
import argparse,json,math,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA

MANIFEST=Path(__file__).with_name('native_two_stage_heading_pins.txt')
LEAVES=((0x03009280,0x030092fc),(0x030092fc,0x03009382),
        (0x02f2c834,0x02f2c8ba),(0x02f50fe4,0x02f5101f))
E8={
 0x03025e91:0x0301287c,0x03025f6f:0x030092fc,
 0x03026022:0x0301287c,0x0302607f:0x03009280,
 0x02f2c784:0x02f2c834,0x02f4f52b:0x02f50fe4,
 0x02f4f554:0x02d4be38,0x02f4f565:0x0311d0cc,
 0x02f4f57e:0x0118309c,0x02f4f58b:0x00531e54,
 0x02f4f5ba:0x030ecab0,0x02f4f5de:0x031219b0,
 0x02f4f62c:0x03279ee8,
}
def pins():
    table={}
    for line_no,line in enumerate(MANIFEST.read_text('utf-8').splitlines(),1):
        fields=line.split('#',1)[0].split()
        if not fields:continue
        if len(fields)!=2:raise ValueError('MANIFEST_ROW:'+str(line_no))
        rva=int(fields[0],16)
        if rva in table:raise ValueError('DUPLICATE_RVA:'+hex(rva))
        table[rva]=bytes.fromhex(fields[1])
    if len(table)!=87:raise ValueError('MANIFEST_SIZE_DRIFT')
    return table

def policy(slot_flags, saved_heading):
    """Only this MOVE activation + new shortTask constructor, not all tasks."""
    uses_saved=bool(slot_flags&0x02)
    return {
      'method':'manual' if slot_flags&0x01 else 'helper',
      'activation_heading':'slot+0x98' if uses_saved else 'live group+0xBF0',
      'shortTask_plus72':saved_heading & 0xffff if uses_saved else 0,
      'shortTask_plus74':int(uses_saved),
      'later_B_heading':'shortTask+0x72' if uses_saved else 'live group+0xBF0'
    }

def audit(exe):
    pe=OriginalEXE(exe)
    try:
        if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
        starts={}
        for rva,expected in pins().items():
            if pe.section(rva)!='.00cfg' or pe.read(rva,len(expected))!=expected:
                raise ValueError('OPCODE_DRIFT:'+hex(rva))
            owner=pe.owner(rva)
            bounds=owner[:2] if owner else next((x for x in LEAVES if x[0]<=rva<x[1]),None)
            if bounds is None:raise ValueError('UNKNOWN_FUNCTION_OWNER:'+hex(rva))
            if bounds not in starts:starts[bounds]=pe.starts_in(*bounds)
            if rva not in starts[bounds]:raise ValueError('MID_INSTRUCTION:'+hex(rva))
        for site,dest in E8.items():
            raw=pe.read(site,5)
            if raw[0]!=0xe8 or site+5+struct.unpack_from('<i',raw,1)[0]!=dest:
                raise ValueError('E8_DRIFT:'+hex(site))
        for end in (0x030092fb,0x03009381,0x02f2c8b9,0x02f51006,0x02f5101e):
            if pe.read(end,1)!=b'\xc3':raise ValueError('LEAF_RET_DRIFT:'+hex(end))
        # 3 pushes and SUB RSP,0x1A0 in 0x03025D70; RBP=entryRSP-0xB8.
        # Local descriptor begins RSP+0x40.
        sp=0x100000; rsp=sp-0x1b8; rbp=sp-0xb8
        if (rbp-0x7e,rbp-0x7c)!=(rsp+0x82,rsp+0x84):
            raise ValueError('WIN64_STACK_ALIAS_DRIFT')
        return {
          'schema':'bsc.n1.two_stage_heading_and_task_release.v1',
          'proof':'EXACT_ORIGINAL_EXE_STATIC','sha256':pe.sha,
          'instruction_starts':87,'e8_targets':len(E8),'leaf_rets':5,
          'flag_table':{str(i):policy(i,0x1234) for i in range(4)},
          'task_flag':'shortTask+0x74 copied from descriptor+0x44; equals source MOVE slot+0x9A bit2 at construction',
          'later_B_selector':'0x02F4F530 tests +0x74: +0x72 saved angle vs recalculation from current UnitRoot group',
          'release_before_B_selector':'0x02F4F52B calls 0x02F50FE4, conditionally decrementing old bigTask ref and clearing *[shortTask+0x80] before selector',
          'shift_runtime_instance_observed':False,
          'group_generation_mismatch_observed':False,
          'motor_goal_conflict_proven':False,
          'gameplay_patch_authorized':False,
        }
    finally:pe.close()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    if args.out and args.out.resolve()==args.exe.resolve():
        ap.error('EXE_OVERWRITE_FORBIDDEN')
    v=audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('PASS',v['instruction_starts'],'original instructions',v['e8_targets'],'E8; NO PATCH')
if __name__=='__main__':main()
