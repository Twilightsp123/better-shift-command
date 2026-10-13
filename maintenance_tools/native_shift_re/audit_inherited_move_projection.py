#!/usr/bin/env python3
"""Exact WH3 native stage-1 MOVE projection from inherited subtask geometry.

This shows the *conditional* state-1 route: a fresh native builder
recomputes task+0x24 and only if it equals 1 does the successor inherit
prior subtask direction. It must never be modeled as unconditional reuse. It does NOT show that this
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
 0x0311E5B3:'44886f24', # state1 projection recomputed-gate control
 0x0311E61E:'e85d05ffff', # state1 projection recomputed-gate control
 0x0311E636:'e8d1010000', # state1 projection recomputed-gate control
 0x0311E63F:'0f859b010000', # state1 projection recomputed-gate control
 0x0311E6F8:'488bce', # state1 projection recomputed-gate control
 0x0311E772:'e895000000', # state1 projection recomputed-gate control
 0x0311E829:'4c8baa60010000', # state1 projection recomputed-gate control
 0x0311E891:'33ff', # state1 projection recomputed-gate control
 0x0311EAC7:'e8940affff', # state1 projection recomputed-gate control
 0x0311EACC:'448ac0', # state1 projection recomputed-gate control
 0x0311EAD4:'84c0', # state1 projection recomputed-gate control
 0x0311EB04:'4584c0', # state1 projection recomputed-gate control
 0x0311EB09:'84d2', # state1 projection recomputed-gate control
 0x0311EB0D:'418af9', # state1 projection recomputed-gate control
 0x0311EB10:'40887e24', # state1 projection recomputed-gate control
 0x0311EB14:'413af9', # state1 projection recomputed-gate control
 0x0311EB17:'0f85bb000000', # state1 projection recomputed-gate control
 0x0311EB1D:'f3410f104608', # state1 projection recomputed-gate control
 0x0311EBC2:'894e20', # state1 projection recomputed-gate control
 0x0311EC07:'c7462801000000', # state1 projection recomputed-gate control
 0x0311EC0E:'c7462004000000', # state1 projection recomputed-gate control
 0x0311EAD6:'7411', # exact native helper/threshold projection gate
 0x0311EAD8:'398be4040000', # exact native helper/threshold projection gate
 0x0311EADE:'7309', # exact native helper/threshold projection gate
 0x0311EAE0:'448d49ff', # exact native helper/threshold projection gate
 0x0311EAE4:'418ad1', # exact native helper/threshold projection gate
 0x0311EAE9:'408ad7', # exact native helper/threshold projection gate
 0x0311EAEC:'41b901000000', # exact native helper/threshold projection gate
 0x0311EB07:'7407', # exact native helper/threshold projection gate
 0x0311EB0B:'7503', # exact native helper/threshold projection gate 0x0311EBC8:'e87f6ffeff', # typed count +0x4E4 and pointer array +0x4E8
 0x03105B68:'8b81e4040000', # typed count +0x4E4 and pointer array +0x4E8
 0x03105B86:'85c0', # typed count +0x4E4 and pointer array +0x4E8
 0x03105B88:'0f84c0010000', # typed count +0x4E4 and pointer array +0x4E8
 0x03105B8E:'488b87e8040000', # typed count +0x4E4 and pointer array +0x4E8
 0x03105B9C:'4e8b34f8', # typed count +0x4E4 and pointer array +0x4E8
 0x03105D3C:'8b87e4040000', # typed count +0x4E4 and pointer array +0x4E8
 0x03105D42:'41ffc7', # typed count +0x4E4 and pointer array +0x4E8
 0x03105D45:'443bf8', # typed count +0x4E4 and pointer array +0x4E8
 0x03105D48:'0f8240feffff', # typed count +0x4E4 and pointer array +0x4E8
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
        # Critical negative-control: the state-1 transition DOES NOT always
        # transfer the previous subtask. +0x24 is reset, recomputed by the
        # same native helper used by fresh state-0, then branch-gates projection.
        direct_calls={
          0x0311E636:0x0311E80C,
          0x0311E772:0x0311E80C,
          0x0311EAC7:0x0310F560,
          0x0311EBC8:0x03105B4C,
        }
        jcc_edges={
          0x0311DEC0:0x0311E578,
          0x0311E63F:0x0311E7E0,
          0x0311EB17:0x0311EBD8,
        }
        for site,dest in direct_calls.items():
            raw=pe.read(site,5,True)
            if raw[0]!=0xe8 or site+5+struct.unpack_from('<i',raw,1)[0]!=dest:
                raise ValueError('STAGE1_NATIVE_CALL_DRIFT:'+hex(site))
        for site,dest in jcc_edges.items():
            raw=pe.read(site,6,True)
            if raw[0]!=0x0f or site+6+struct.unpack_from('<i',raw,2)[0]!=dest:
                raise ValueError('STAGE1_GATE_BRANCH_DRIFT:'+hex(site))
        scalar=struct.unpack('<f',pe.read(CONSTANT,4))[0]
        if scalar!=0.5:raise ValueError('STAGE1_PROJECTION_CONST_CHANGED')
        return {
          'schema':'bsc.n1.original_inherited_move_projection.v1',
          'exe_sha256':pe.sha,
          'static_guard_count':boundary_count,'constant_scale':scalar,
          'stage1_native_call_edges_checked':len(direct_calls),
          'stage1_conditional_branch_edges_checked':len(jcc_edges),
          'stage1_task_plus24_cleared_before_recompute':'0x0311E5B3',
          'task_plus24_recomputed_by_common_builder':'0x0311E636 -> 0x0311E80C',
          'common_builder_called_from_fresh_state0':'0x0311E772 -> 0x0311E80C',
          'builder_helper_AL_gate':'0x0311EAC7 -> 0x0310F560',
          'helper_AL_false_skips_positive_gate_at':'0x0311EAD6 / 0x0311EB07',
          'controller_field_4e4_threshold':'0x0311EAD8 compares [RBX+0x4E4] to ECX=2',
          'same_context_count_and_pointer_array':'0x03105B68 reads +0x4E4 as count; 0x03105B8E reads +0x4E8 pointer array',
          'indexed_array_entry_proven_at':'0x03105B9C loads [array+R15*8]',
          'array_loop_proven_at':'0x03105D3C..0x03105D48 re-reads count and loops index',
          'array_element_semantic_type':'UNKNOWN (not proven to be soldier count or route waypoint count)',
          'field_below_two_yields_DL_one':'0x0311EAE0 / 0x0311EAE4',
          'field_ge_two_yields_DL_zero':'0x0311EADE / 0x0311EAE9',
          'positive_gate_formula_only_on_reached_builder_path':(
             '0x0310F560 returns AL != 0 AND controller+0x4E4 >= 2; '
             'other early exit paths may skip this gate entirely'),
          'builder_task_plus24_store':'0x0311EB10',
          'state1_post_builder_projection_gate':'0x0311E63B / 0x0311E63F',
          'state1_old_projection_only_if_recomputed_flag_is_one':True,
          'state1_flag_not_one_skips_old_subtask_transfer_and_main_pointer_clear':True,
          'new_geometry_copy_occurs_before_projection_gate':True,
          'every_queued_move_inherits_prior_direction':False,
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
