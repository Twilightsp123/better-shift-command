#!/usr/bin/env python3
"""Exact-WH3 read-only audit: B route node ownership, tick, invalidation, A/B shared builder.

No instruction here proves B's route cache is directly sampled by the main soldier
motor; that is an unresolved indirect consumer. Version limited to the supplied
original EXE SHA, and this tool never writes executable memory or its input.
"""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
import struct
import sys

EXPECTED_SHA = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
IMAGE_BASE = 0x140000000

# All original opcode hex values are fixed explicitly; none are harvested from the
# binary under examination at runtime.
PIN = {
    'B_state_install': (0x03279ED8, 'e8d39bfeff'),
    'B_member_location_state': (0x03263BFB, 'e83850e0ff'),
    'B_member_bit7_clear': (0x03263C00, '80a3100b00007f'),
    'B_member_bit7_result': (0x03263C0A, '0883100b0000'),
    'B_task_existing_node': (0x03281454, '488b4958'),
    'B_task_existing_ready': (0x0328145D, '80790800'),
    'B_task_existing_geom': (0x03281469, '488b4970'),
    'B_task_geom_invalid': (0x0328146D, 'e8aed5e5ff'),
    'B_task_drop_node_ref': (0x0328147D, '014804'),
    'B_task_drop_node_ptr': (0x03281480, '4883635800'),
    'B_task_drop_prior_ref': (0x03281489, '014818'),
    'B_task_drop_prior_ptr': (0x0328148C, '4883632000'),
    'B_task_pending_no_node': (0x03281497, '48837b5800'),
    'B_task_group_owner': (0x032814E8, '488b8040040000'),
    'B_task_group_route_context': (0x032814EF, '488b8860010000'),
    'B_task_prior_route_build': (0x032814FB, 'e8bc05eaff'),
    'B_task_prior_ref': (0x03281500, '48894358'),
    'B_task_fresh_route_build': (0x0328150A, 'e8a104eaff'),
    'B_task_fresh_ref': (0x0328150F, '48894358'),
    'B_node_alloc_refcount_1': (0x030ECB27, 'c7410401000000'),
    'B_node_fresh_cache_ready': (0x030ECB2E, '66c741080100'),
    'B_node_copy_route_description': (0x030ECB3C, 'e8abfeffff'),
    'B_node_build_route_geometry': (0x030ECB98, 'e847160100'),
    'B_node_geom_store': (0x030ECBA2, '48894370'),
    'B_node_connect_prev_next': (0x030ECBB8, 'e8b31b0200'),
    'B_node_group_head_store': (0x03121B55, '488987d0020000'),
    'B_node_group_tail_store': (0x03121B6B, '488987d8020000'),
    'B_node_no_prior_pending': (0x03121A25, '6683630800'),
    'B_node_no_prior_no_geometry': (0x03121A45, '4883637000'),
    'B_node_no_prior_optional_geometry': (0x03121A99, 'e8febffdff'),
    'group_regular_member_task_update': (0x02DD58AE, 'e8edfa1a00'),
    'group_route_context_load': (0x02DD58D7, '488b8b60010000'),
    'group_route_tick': (0x02DD58DE, 'e89d353500'),
    'route_manager_active_head': (0x03129031, '488bbbd0020000'),
    'route_manager_budget_zero': (0x03129038, '418bec'),
    'route_manager_current_node_live': (0x03129059, '44396704'),
    'route_manager_remove_dead': (0x03129065, 'e80e0dfeff'),
    'route_manager_budget_one_gate': (0x03129073, '413bed'),
    'route_manager_node_pending': (0x03129078, '44386708'),
    'route_manager_pending_allowed': (0x03129085, 'e88e2dffff'),
    'route_manager_shared_route': (0x03129092, 'e8054afdff'),
    'route_manager_node_geom': (0x03129097, '48894770'),
    'route_manager_budget_increment': (0x0312909B, '4103ed'),
    'route_manager_node_ready': (0x0312909E, '44886f08'),
    'route_manager_active_count': (0x0312906C, '4401ab500b0000'),
    'route_unlink_head_cmp': (0x03109D88, '483991d0020000'),
    'route_unlink_head_update': (0x03109D95, '488981d0020000'),
    'route_unlink_tail_cmp': (0x03109D9C, '483999d8020000'),
    'route_unlink_tail_update': (0x03109DA9, '488981d8020000'),
    'route_unlink_geometry_cleanup': (0x03109DB3, 'e8f4c7feff'),
    'route_unlink_recycle_node': (0x03109DC2, '48899fe0020000'),
    'route_cleanup_geometry_read': (0x030F65D2, '488b4970'),
    'route_cleanup_geometry_release': (0x030F65DB, 'e8e04bd2ff'),
    'B_route_constructor_geometry': (0x030FE272, 'e8653dfcff'),
    'B_route_constructor_merge': (0x030FE287, 'e8cc95fcff'),
    'A_shared_route_geometry': (0x030D55F5, 'e8a2840200'),
    'A_direct_actor_targets': (0x030D5603, 'e888feffff'),
    'A_release_temporary_geometry': (0x030D5610, 'e8ab5bd4ff'),
}
# All are instructions with E8 + signed32 displacement.
CALLS = {
    'B_group_action_ctor': (0x03279ED8, 0x03263AB0),
    'B_actor_spatial_marker': (0x03263BFB, 0x03068C38),
    'B_task_route_reference_test': (0x0328146D, 0x030DEA20),
    'B_task_subroute_old_context': (0x032814FB, 0x03121ABC),
    'B_task_subroute_new_context': (0x0328150A, 0x031219B0),
    'B_route_node_constructor': (0x03121B40, 0x030ECB10),
    'B_route_node_build_geometry': (0x030ECB98, 0x030FE1E4),
    'B_geometry_first_segment': (0x030FE272, 0x030C1FDC),
    'B_geometry_merge_segments': (0x030FE287, 0x030C7858),
    'B_node_link_prev_next': (0x030ECBB8, 0x0310E770),
    'B_route_tick_from_group_update': (0x02DD58DE, 0x03128E80),
    'B_manager_remove_dead_node': (0x03129065, 0x03109D78),
    'B_manager_pending_geom_check': (0x03129085, 0x0311BE18),
    'B_manager_refresh': (0x03129092, 0x030FDA9C),
    'B_unlink_finalizer': (0x03109DB3, 0x030F65AC),
    'B_geometry_release': (0x030F65DB, 0x02E1B1C0),
    'A_generate_member_route': (0x030D55F5, 0x030FDA9C),
    'A_distribute_members': (0x030D5603, 0x030D5490),
    'A_release_temporary_route': (0x030D5610, 0x02E1B1C0),
    'B_fresh_node_optional_geometry': (0x03121A99, 0x030FDA9C),
}

def pe_sections(m):
    if m[:2] != b'MZ': raise ValueError('not MZ')
    nt=struct.unpack_from('<I',m,0x3C)[0]
    if m[nt:nt+4] != b'PE\0\0': raise ValueError('not PE')
    machine,count=struct.unpack_from('<HH',m,nt+4)
    if machine!=0x8664:raise ValueError('not x64 PE')
    opt=nt+24
    sz=struct.unpack_from('<H',m,nt+20)[0]
    image=struct.unpack_from('<Q',m,opt+24)[0]
    if image!=IMAGE_BASE:raise ValueError('wrong imagebase')
    results=[]
    for i in range(count):
        o=opt+sz+i*40
        name=m[o:o+8].split(b'\0',1)[0].decode('ascii')
        virtual,addr,length,offset=struct.unpack_from('<IIII',m,o+8)
        flags=struct.unpack_from('<I',m,o+36)[0]
        results.append((name,addr,length,offset,flags))
    return results

def read_rva(m,sections,rva,n,executable=False):
    for name,start,sz,offset,flags in sections:
        if start<=rva and rva+n<=start+sz:
            if executable and not flags & 0x20000000:
                raise ValueError('not executable '+name+' '+hex(rva))
            return bytes(m[offset+rva-start:offset+rva-start+n])
    raise ValueError('not file backed '+hex(rva))

def call_target(site,b):
    if len(b)!=5 or b[0]!=0xE8:raise ValueError('not E8 '+hex(site))
    return (site+5+struct.unpack_from('<i',b,1)[0]) & 0xFFFFFFFF

def original_verify(path):
    path=Path(path)
    with path.open('rb') as f:
        sha=hashlib.file_digest(f,'sha256').hexdigest()
    if sha!=EXPECTED_SHA:raise ValueError('original-exe sha mismatch '+sha)
    with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        sections=pe_sections(mm)
        for key,(addr,hx) in PIN.items():
            got=read_rva(mm,sections,addr,len(hx)//2,True).hex()
            if got!=hx:raise ValueError('opcode mismatch '+key+' got '+got+' expected '+hx)
        for key,(site,dest) in CALLS.items():
            got=call_target(site,read_rva(mm,sections,site,5,True))
            if got!=dest:raise ValueError('call mismatch '+key+' got '+hex(got))
    return dict(
        schema='bsc.903.b_fallback_route_node_lifecycle.v1',
        original_exe_sha256=sha,
        machine_guards=len(PIN),direct_e8_edges=len(CALLS),
        observations={
            'native_b_branch':'0x03279E40 creates 0x03AE0128 group action; constructor 0x03263AB0 writes member bit7 by spatial predicate before any child route',
            'B_prior_node':'0x03281444 retains B action+0x58 route node while compatible; failed 0x030DEA20 decrements node+4 and clears B task ref, then may allocate another route node',
            'B_route_store':'0x03121ABC -> 0x030ECB10 creates node (refcount+4=1, ready+8=1) and route geometry at node+0x70 via 0x030FE1E4, links active group route-manager list +0x2d0/+0x2d8',
            'B_no_prior':'0x031219B0 creates node ready=0/cache=null, with conditional immediate route build 0x030FDA9C and ready=1',
            'B_tick':'0x02DD579C updates subgroup +0x160 with 0x03128E80; this tick removes node iff refcount+4=0 and may fill at most one pending node geometry cache (per-invocation ebp<1 gate)',
            'B_route_reclaim':'0x03109D78 unlinks node from active ctx list, calls 0x030F65AC to unlink neighboring pointers and release node+0x70 geometry, recycles node to ctx+0x2e0',
            'A_shared_geometry':'0x030D554C calls 0x030FDA9C then directly 0x030D5490 to distribute per-member targets; it releases its temporary geometry afterward. B may store results of the same generator in a persistent group node',
            'cross_owner':'B task at 0x03281444 loads owner via task+0x8->+0x440->+0x160, the same subgroup+0x160 ticked by 0x02DD579C',
            'phase_not_proven':'Route-node retention or asynchronous cache fill does not prove any actor is still traveling an old waypoint. B route-to-main actor motor edge not established.',
        },
        static_only=True,patch_authorized=False,V3_B_branch_observed=False
    )

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    if a.exe.resolve()==a.out.resolve():p.error('cannot overwrite EXE')
    try:
        result=original_verify(a.exe)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    except (ValueError,OSError,struct.error) as ex:
        print('FAIL_CLOSED:',ex,file=sys.stderr)
        return 2
    print('PASS original SHA',len(PIN),'machine guards',len(CALLS),'call edges; STATIC ONLY NO PATCH')
    return 0

if __name__=='__main__':raise SystemExit(main())