#!/usr/bin/env python3
"""Exact WH3 native stage-1 MOVE projection from inherited subtask geometry.

This shows how the queued MOVE successor can retain/use the prior subtask
motion direction to seed a new geometry segment. It does NOT show that this
causes the known Shift crowding, and is not a patch.
"""
import argparse,json,re,struct,shutil
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

PINS={
 0x030EE88D:'44894120', # task+0x20 state init zero
 0x030EE908:'4d898258010000', # task+0x158 initialized NULL
 0x0312058B:'49898558010000', # action producer writes +0x158
 0x0311DF17:'48898f58010000', # progress later writes +0x158
 0x0311E4D1:'48898f58010000', # progress also writes +0x158
 0x0310EE12:'4883bb5801000000', # creation / ready loop waits +0x158
 0x03128F94:'4c39a758010000', # group task pump checks +0x158
 0x0311DEAA:'4533ed', # R13 register holds zero for later field clear
 0x0311DEBD:'83e901',
 0x0311DEC0:'0f84b2060000', # state 1 -> 0x311e578
 0x0311E578:'488bce',
 0x0311E580:'488b9f60010000', # linked new subtask from +0x160
 0x0311E5C2:'0f108720010000', # queued new 16 bytes +0x120
 0x0311E5D3:'0f108f30010000', # queued new 16 bytes +0x130
 0x0311E5FA:'8b8740010000', # queued new geometry +0x140
 0x0311E63B:'807f2401', # readiness flag gates projection
 0x0311E645:'488b8758010000', # fetch prior subtask pointer
 0x0311E64C:'48894320', # retain prior subtask at new subtask+0x20
 0x0311E65E:'f20f104020', # prior subtask X
 0x0311E66F:'f30f1090b8000000', # prior subtask extent
 0x0311E687:'f30f5990ac000000', # prior direction Z
 0x0311E68F:'f30f5980a8000000', # prior direction X
 0x0311E6A4:'f30f114b48', # projection - component
 0x0311E6A9:'f30f11434c',
 0x0311E6E2:'f30f114b54', # projection + component
 0x0311E6E7:'f30f114350',
 0x0311E6EC:'4c89af58010000', # clear MAIN pointer, subtask+0x20 stays
}
CONSTANT=0x0391CBC8
STAGE1=0x0311E578

def projected_endpoints(old_x,old_z,dir_x,dir_z,extent):
    """Literal symmetric coordinates from 0x311E65E..0x311E6E7."""
    scale=0.5*extent
    return ((old_x-scale*dir_x,old_z-scale*dir_z),
            (old_x+scale*dir_x,old_z+scale*dir_z))

def audit(exe):
    pe=StrictPE(Path(exe))
    try:
        for site,raw in PINS.items():
            if pe.read(site,len(raw)//2,True).hex()!=raw:
                raise ValueError('STAGE1_OPCODE_DRIFT:'+hex(site))
        if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
        groups={};boundary_count=0
        for site in PINS:
            fn=pe.function(site)
            if not fn:raise ValueError('STAGE1_UNWIND_MISSING:'+hex(site))
            groups.setdefault(fn,[]).append(site)
        for (start,end),sites in groups.items():
            asm=pe.disasm(start,end-start)
            lines=set()
            for line in asm.splitlines():
                m=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',line)
                if m:lines.add(int(m.group(1),16))
            for site in sites:
                if site not in lines:
                    raise ValueError('STAGE1_MID_OPCODE:'+hex(site))
                boundary_count+=1
        # This conditional JZ proves state==1 enters stage1 rather than
        # treating 0x03040864's status assignment as a passive metadata write.
        branch=pe.read(0x0311DEC0,6,True)
        if 0x0311DEC0+6+struct.unpack_from('<i',branch,2)[0]!=STAGE1:
            raise ValueError('STAGE1_DISPATCH_DEST_CHANGED')
        scalar=struct.unpack('<f',pe.read(CONSTANT,4))[0]
        if scalar!=0.5:raise ValueError('STAGE1_PROJECTION_CONST_CHANGED')
        return {
          'schema':'bsc.n1.original_inherited_move_projection.v1',
          'exe_sha256':pe.sha,
          'static_guard_count':boundary_count,'constant_scale':scalar,
          'state_one_branch':'0x0311DEBD -> 0x0311E578',
          'task_new_route_geometry':'0x120..0x14F copied to active task geometry',
          'prior_subtask_source':'[task+0x158]',
          'prior_subtask_ownership_transfer':'[task+0x160]+0x20 stores prior subtask pointer',
          'new_local_projection_offsets':['subtask+0x48','+0x4C','+0x50','+0x54'],
          'projection_formula':'(oldPos.XZ ± 0.5 * oldExtent * oldDirectionXZ)',
          'main_task_158_cleared_after_projection':True,
          'old_subtask_reference_still_reachable_via_successor':True,
          'native_queue_handoff_same_instance_confirmed':False,
          'queued_shift_crowding_causality_proven':False,
          'patch_authorized':False
        }
    finally:pe.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.exe.resolve()==a.out.resolve():p.error('NO_EXE_OVERWRITE')
    proof=audit(a.exe)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('PASS',proof['static_guard_count'],'original state-1 native opcode boundaries; patch NOT authorized')
if __name__=='__main__':main()
