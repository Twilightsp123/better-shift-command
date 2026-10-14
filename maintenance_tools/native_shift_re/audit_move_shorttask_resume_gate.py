#!/usr/bin/env python3
"""Exact 9.0.3 WH3 original EXE: queued MOVE short-task scheduler and reactivation.

Read-only, no native patch. Proves the typed manager pointer origin, top-only
short-task update, alternative descriptor branches, and possible re-arming.
Not proof that an actual player Shift instance revived a stale task.
"""
import argparse
import json
import re
import shutil
import struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

SHA = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
PINS={int(a,16):bytes.fromhex(b) for a,b in (line.split() for line in """
03007AD1 498d87a02f0000
03007B5B 4d89bf78020000
03007B62 49898780020000
02F5044C 4c8d4310
02F50460 488b4308
02F50464 4889442430
02F5048E 488b442430
02F50493 48894110
030326B4 488d8b78020000
030326BE e84dddf1ff
030326CE 488d4b18
030326E4 e8d369fdff
03008814 4c8bd9
0300884D 488b4210
03008851 48894118
03008892 c3
030090CC e843f7ffff
03026084 488b5318
03026088 b9a8000000
03026091 e81a9ff0ff
030260AF e88066f0ff
02F2FFB0 4883ec18
02F2FFCC 448b8240020000
02F2FFDF 898240020000
02F2FFEB f30f7f84c2000200
02F2FFF4 018a44020000
02F3000E 8b8240020000
02F30019 488b84c2000200
02F2C777 488d059af6b800
02F2C77E 488901
02F2C79A 6644899ba0000000
03043520 48895c2408
03043550 80bb5002000001
0304356C 488b34c3
03043579 3bf8
0304357B 7521
0304357D ff5210
03043583 807e1801
0304358E e8c9c7f0ff
0304359E ff5218
0304372F 39b384010000
03043769 488d8b78020000
03043770 e8c70b0000
03043775 488d8ba02f0000
0304377C e89ffdffff
02F56223 40387025
02F56227 0f8493000000
02F5622D 4088b1a0000000
02F56277 488b4b08
02F5627B 488b89f8320000
02F56282 e83d981700
02F562C0 4038b3a0000000
02F562C7 0f85f7010000
02F562E3 83782004
02F562F2 40387024
02F562FF c683a000000001
02F5630C 40387374
02F56310 0f84f8000000
02F56358 e80bda3000
02F563F4 488b4b08
02F563FD 488b89f8320000
02F56404 e8373a3200
02F56431 e846da3000
02F56460 e8e7d73000
02F56465 eb8d
02F564C4 4038b3a1000000
02F4FD9C 488b4cfd00
02F4FDAE ff10
02F4FDC4 ff8b40020000
""".strip().splitlines())}

LEAF_BOUNDS={0x03008814:(0x03008814,0x03008893)}
DIRECT_CALLS={
 0x030326BE:0x02F50410,0x030326E4:0x030090BC,
 0x030090CC:0x03008814,0x03026091:0x02F2FFB0,
 0x030260AF:0x02F2C734,0x0304358E:0x02F4FD5C,
 0x03043770:0x0304433C,0x0304377C:0x03043520,
 0x02F56282:0x030CFAC4,0x02F56358:0x03263D68,
 0x02F56404:0x03279E40,0x02F56431:0x03263E7C,
 0x02F56460:0x03263C4C,
}
# branch types and exact targets confirmed from original signed immediates
BRANCHES={
 0x0304357B:(0x75,0x0304359E),
 0x02F56227:(0x0f84,0x02F562C0),
 0x02F562C7:(0x0f85,0x02F564C4),
 0x02F56310:(0x0f84,0x02F5640E),
 0x02F56465:(0xeb,0x02F563F4),
}
VTABLES={
 0x03ABBE18+0x8:0x008D3280,
 0x03ABBE18+0x10:0x02F561E8,
 0x03ABBE18+0x18:0x008D3280,
 0x0390B4F0+0x8:0x03025D70,
}

def checked_starts(pe):
    if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
    by_owner={}
    for site, raw in PINS.items():
        if pe.read(site,len(raw),True)!=raw:raise ValueError('OPCODE_DRIFT:'+hex(site))
        owner=pe.function(site) or next((value for value in LEAF_BOUNDS.values()
                                        if value[0]<=site<value[1]),None)
        if owner is None:raise ValueError('NO_TYPED_OWNER:'+hex(site))
        if owner not in by_owner:
            dis=pe.disasm(owner[0],owner[1]-owner[0])
            by_owner[owner]={int(match.group(1),16):line.strip()
              for line in dis.splitlines()
              if (match:=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',line))}
        if site not in by_owner[owner]:raise ValueError('MID_INSTRUCTION:'+hex(site))
    # Root constructor RAX stays the address of root+0x2FA0 up to store.
    root_owner=pe.function(0x03007AD1)
    lines=by_owner[root_owner]
    for site,line in lines.items():
        if 0x03007AD1<site<0x03007B62:
            text=line.split('\t')[-1].lower()
            if re.search(r'\bcall\b',text) or re.search(r'\b(?:mov|lea|xor|add|sub|pop|and|or|shl|shr)\s+(?:r|e)ax\s*,',text):
                raise ValueError('ROOT_MANAGER_RAX_CLOBBERED:'+hex(site))
    return len(by_owner)

def branch_target(site,data,opcode):
    if opcode in (0x75,0xeb):
        if len(data)!=2 or data[0]!=opcode:raise ValueError('SHORT_BRANCH_DRIFT')
        return site+2+struct.unpack_from('<b',data,1)[0]
    if len(data)!=6 or data[:2]!=struct.pack('>H',opcode):raise ValueError('NEAR_BRANCH_DRIFT')
    return site+6+struct.unpack_from('<i',data,2)[0]

def simulate_manager(*, old_ready, old_already_dispatched, new_done, shared_change_rearms):
    """Synthetic *possibility* test, no claim of actual game's scheduler timings.

    A new shortTask is above the old one. The older vtable+0x18 is a no-op.
    Completion of the new top can expose old task on a subsequent tick.
    The original top callback still applies its own native state predicates.
    """
    before=dict(top='new',old_virtual='+0x18 no-op',old_dispatched=False)
    if not new_done:
        return dict(before=before,after=dict(top='new',old_dispatched=False),
                    stale_packet_possible_under_given_assumptions=False)
    a0=bool(old_already_dispatched)
    if shared_change_rearms:a0=False
    could_send=bool(old_ready and not a0)
    return dict(before=before,after=dict(top='old',old_dispatched=could_send,
                                        shared_state_eligibility_assumed=bool(old_ready)),
                stale_packet_possible_under_given_assumptions=could_send)

def audit(exe):
    pe=StrictPE(Path(exe))
    try:
        if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
        owners=checked_starts(pe)
        if pe.read(0x008D3280,3,True)!=bytes.fromhex('c20000'):
            raise ValueError('SHORT_TASK_NONLAST_CALLBACK_NOT_EMPTY')
        for site,target in DIRECT_CALLS.items():
            data=pe.read(site,5,True)
            if data[0]!=0xe8 or site+5+struct.unpack_from('<i',data,1)[0]!=target:
                raise ValueError('DIRECT_CALL_DRIFT:'+hex(site))
        for site,(opcode,target) in BRANCHES.items():
            n=2 if opcode in (0x75,0xeb) else 6
            if branch_target(site,pe.read(site,n,True),opcode)!=target:
                raise ValueError('BRANCH_TARGET_DRIFT:'+hex(site))
        for site,target in VTABLES.items():
            value=struct.unpack('<Q',pe.read(site,8))[0]
            if value!=pe.base+target:raise ValueError('TYPED_VTABLE_DRIFT:'+hex(site))
        # The short task can reset +0xA0 when the associated shared state +0x25 is set.
        # Its +0x74 selects one of two descriptor constructors, BOTH then reach
        # shortTask+8 -> CURRENT UnitRoot+0x32F8 -> group dispatcher.
        return dict(schema='bsc.n1.short_task_scheduler_resume.v1',
          sha256=pe.sha,proof_level='EXACT_ORIGINAL_EXE_STATIC',
          opcode_and_disassembly_starts=len(PINS),function_or_explicit_leaf_owners=owners,
          direct_E8_edges=len(DIRECT_CALLS),verified_branches=len(BRANCHES),
          typed_vtable_slots=len(VTABLES),
          manager_type_proven=True,
          manager_alias=('root ctor [root+0x280] = &root+0x2FA0; queue+8 '\
            '-> wrapper+0x10 -> MOVE slot+0x18 -> shortTask allocator manager'),
          manager_array_stride_bytes=16,
          manager_count_offset=0x240,
          manager_task_record_offset=0x200,
          previous_task_dispatch='vtable+0x18 = 0x008D3280 (ret 0 for shortTask)',
          latest_task_dispatch='vtable+0x10 = 0x02F561E8 for shortTask',
          manager_pop_after_last_done=True,
          tick_order='0x03043648: queue 0x0304433C before manager 0x03043520',
          shortTask_A0_guard_can_be_rearmed_on_associated_plus25=True,
          shared_state_20_24_gate_for_main_fanout=True,
          shortTask_plus74_is_descriptor_selector_not_required_fanout_gate=True,
          current_group_read_when_dispatch='[shortTask+8] -> [UnitRoot+0x32F8]',
          old_task_immediate_update_when_nonlast=False,
          old_task_can_regain_top_after_new_task_removed=True,
          no_gameplay_proof_of_old_short_task_reactivation=True,
          no_gameplay_proof_of_cross_generation_send=True,
          native_patch_authorized=False,
          offline_counterexamples={
            'new_on_top':simulate_manager(old_ready=True,old_already_dispatched=False,
                                          new_done=False,shared_change_rearms=False),
            'new_removed_old_unprocessed':simulate_manager(old_ready=True,old_already_dispatched=False,
                                          new_done=True,shared_change_rearms=False),
            'new_removed_old_was_dispatched':simulate_manager(old_ready=True,old_already_dispatched=True,
                                          new_done=True,shared_change_rearms=False),
            'explicit_rearm':simulate_manager(old_ready=True,old_already_dispatched=True,
                                          new_done=True,shared_change_rearms=True),
            'old_shared_not_ready':simulate_manager(old_ready=False,old_already_dispatched=False,
                                          new_done=True,shared_change_rearms=False),
          })
    finally:pe.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.exe.resolve()==a.out.resolve():p.error('DO_NOT_OVERWRITE_EXE')
    report=audit(a.exe)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('PASS',report['opcode_and_disassembly_starts'],'instruction guards,',report['direct_E8_edges'],'E8; no Native patch')
if __name__=='__main__':main()
