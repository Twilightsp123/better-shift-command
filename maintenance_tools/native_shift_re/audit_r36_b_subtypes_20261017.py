#!/usr/bin/env python3
"""SHA-scoped, non-injecting WH3 Native Group B-subtype / lifecycle audit.

This explicitly distinguishes route-update B1, member-fanout B2 and separate
packet-setup B3. Static xrefs and opcodes do not prove a player Shift event.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from audit_r35_group_transaction_20261017 import PE, disasm, branch_dest, SHA, IMAGE_BASE, SIZED

HERE = Path(__file__).resolve().parent
PINS_FILE = HERE / 'r36_b_subtypes_pins_20261017.txt'
VTABLES = {
    'B1_route_progress': (0x03AE5820, 0x03286288, 0x03268920, 0x0327ED3C),
    'B2_direct_member': (0x03AE5800, 0x032863A0, 0x03268D34, 0x0327EDD5),
    'B3_other_packet': (0x03AE57E0, 0x03286480, 0x03268E3C, 0x0327EE65),
}
CALLS = {
 0x02F5B400:0x0327ECA4,
 0x02F5B475:0x02F54510,
 0x02F54527:0x02F55FE0,
 0x02F545DA:0x03126A58,
 0x02F54628:0x0327ED4C,
 0x0327ED28:0x02F3F0FC,
 0x0327ED3C:0x03268920,
 0x0327EDBA:0x02F3F0FC,
 0x0327EDD5:0x03268D34,
 0x0327EE51:0x02F3F0FC,
 0x0327EE65:0x03268E3C,
 0x032862A6:0x032862C4,
 0x03286346:0x0326C5CC,
 0x0328637B:0x03126B64,
 0x0328638A:0x03126A58,
 0x03286445:0x0326A994,
 0x03286572:0x0326B0C8,
}
JUMPS = {
 0x02F5B2F2:0x02F5B463,
 0x02F5B405:0x02F5B4B3,
 0x02F5B473:0x02F5B47C,
 0x0327ECCD:0x0327ED1E,
 0x0327ED7A:0x0327EDB3,
 0x0327EE15:0x0327EE47,
 0x032863B7:0x0328645E,
}
# Ensure two member update methods are not conflated with one another.
EXCLUSIVE_FANOUT = {
 'method_B1': 0x03286288,
 'route_update_B1': 0x032862C4,
 'method_B2': 0x032863A0,
 'method_B3': 0x03286480,
}


def read_pins():
    groups={};current=None
    for line in PINS_FILE.read_text('utf-8').splitlines():
        m=re.match(r'^# (\w+) bounds=([0-9a-fA-F]+):([0-9a-fA-F]+)$', line)
        if m:
            current=m[1]
            if current in groups:raise ValueError('DUP_GROUP')
            groups[current]=((int(m[2],16),int(m[3],16)),{})
            continue
        words=line.split('#',1)[0].split()
        if not words:continue
        if current is None or len(words)!=2:raise ValueError('MALFORMED_ROW')
        addr=int(words[0],16)
        if addr in groups[current][1]:raise ValueError('DUP_PIN')
        groups[current][1][addr]=bytes.fromhex(words[1])
    if len(groups)!=15 or sum(len(x[1]) for x in groups.values())!=128:
        raise ValueError('INVENTORY_DRIFT')
    return groups


def direct_call_candidates(pe, target_set):
    """Conservative E8 byte candidates; accept only confirmed disassembly starts."""
    target_set=set(target_set); matches={k:[] for k in target_set}
    for name,va,virtual,rs,rp,flags in pe.sections:
        if not flags&0x20000000:continue
        raw=pe.d[rp:rp+rs]; cursor=0
        while True:
            idx=raw.find(b'\xE8',cursor)
            if idx<0:break
            cursor=idx+1
            if idx+5>len(raw):continue
            site=va+idx
            dst=site+5+struct.unpack_from('<i',raw,idx+1)[0]
            if dst in matches:matches[dst].append(site)
    return matches


def audit(exe):
    pe=PE(exe)
    try:
        if pe.base!=IMAGE_BASE or len(pe.d)!=SIZED:
            raise ValueError('WRONG_PE_VERSION_OR_SIZE')
        with open(exe,'rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
        if sha!=SHA:raise ValueError('EXE_SHA256_MISMATCH')
        groups=read_pins(); observed={}; code={}; owners={}
        for name,(span,pins) in groups.items():
            lo,hi=span
            if pe.owner(lo)!=span or not pe.is_executable(lo):
                raise ValueError('FUNCTION_UNWIND_DRIFT:'+name)
            decoded=disasm(pe,lo,hi)
            code[name]=decoded
            owners[name]=[hex(lo),hex(hi)]
            for at,b in pins.items():
                if at not in decoded or at<lo or at+len(b)>hi:
                    raise ValueError('MID_INSTRUCTION:'+hex(at))
                if pe.read(at,len(b))!=b:
                    raise ValueError('BYTE_DRIFT:'+hex(at))
                if at in observed:raise ValueError('DUPLICATE_CROSS_FUNCTION')
                observed[at]=b
        for site,target in CALLS.items():
            b=observed.get(site)
            if b is None or len(b)!=5 or b[0]!=0xE8:
                raise ValueError('UNPINNED_CALL:'+hex(site))
            if site+5+struct.unpack_from('<i',b,1)[0]!=target:
                raise ValueError('CALL_TARGET_DRIFT:'+hex(site))
        for site,target in JUMPS.items():
            if branch_dest(site,observed[site])!=target:
                raise ValueError('JUMP_TARGET_DRIFT:'+hex(site))
        for label,(table,method,ctor,site) in VTABLES.items():
            if struct.unpack('<Q',pe.read(table+0x10,8))[0]!=IMAGE_BASE+method:
                raise ValueError('B_VTABLE_DRIFT:'+label)
        # Check expected current-Group embedded B object placement (parent +0x8F0,
        # task at +0x18 -> Group+0x908) from concrete three dispatcher bodies.
        group_bases={
         'dispatch_B1': {'0x8f0','0x18'},
         'dispatch_B2': {'0x8f0','0x908'},
         'dispatch_B3': {'0x8f0','0x18'},
        }
        for name,terms in group_bases.items():
            asm='\n'.join(code[name].values()).lower()
            if not all(t in asm for t in terms):
                raise ValueError('GROUP_EMBEDDED_SLOT_DRIFT:'+name)
        # Validate that each constructor explicitly installs its subtype.
        exact={
         0x0326893F:'lea    rax,[rip+',
         0x03268946:'mov    QWORD PTR [rdi],rax',
         0x03268D45:'lea    rdx,[rip+',
         0x03268D4C:'mov    QWORD PTR [rbx],rdx',
         0x03268E54:'lea    rdx,[rip+',
         0x03268E5E:'mov    QWORD PTR [rbx],rdx',
        }
        all_dis={addr:opcode for ops in code.values() for addr,opcode in ops.items()}
        for at,part in exact.items():
            if part not in all_dis.get(at,''):
                raise ValueError('CTOR_VTABLE_WRITE_DRIFT:'+hex(at))
        # Same shortTask callback *branch* can dispatch B1 vs B2, but distinct
        # bigTask state gates mean it does not do both on one CFG path.
        state_markers={
         0x02F5B2DF:'[rax+0x20]', # bigTask state ==4
         0x02F5B2EE:'[rax+0x24]', # nonzero -> B1 candidate
         0x02F5B468:'[rax+0x28]', # zero, phase3 -> B2 candidate
         0x02F5B3F9:'[rcx+0x32f8]',
         0x02F54621:'[rcx+0x32f8]',
        }
        for at,frag in state_markers.items():
            if frag not in all_dis.get(at,'').lower():
                raise ValueError('SHORTTASK_BRANCH_SEMANTIC_DRIFT:'+hex(at))
        # B1 +0x10 is a route maintenance method; B2 +0x10 can directly
        # construct+fanout; B3 +0x10 only has direct helper packet setup.
        for name,method in EXCLUSIVE_FANOUT.items():
            instructions=code[name]
            calls={at:at+5+struct.unpack_from('<i',pe.read(at,5),1)[0]
                   for at,asm in instructions.items() if asm.lstrip().startswith('call')
                   and pe.read(at,1)==b'\xe8'}
            if name in ('method_B1','route_update_B1') and (0x0326A994 in calls.values() or 0x0326B0C8 in calls.values()):
                raise ValueError('B1_FANOUT_UNEXPECTED')
            if name=='method_B2' and (0x03286445,0x0326A994) not in calls.items():
                raise ValueError('B2_MEMBER_FANOUT_MISSING')
            if name=='method_B3' and (0x03286572,0x0326B0C8) not in calls.items():
                raise ValueError('B3_SETUP_PATH_MISSING')
        # Cleanup is conditional, not an unconditional token barrier.
        if '[rcx+0x118]' not in all_dis[0x02F3F10A].lower() or not all_dis[0x02F3F11B].startswith('call   QWORD PTR [rax]'):
            raise ValueError('RESET_ACTIVE_FLAG_GUARD_DRIFT')
        if '[rbx+0x118]' not in all_dis[0x02F3F11D].lower():
            raise ValueError('RESET_FLAG_WRITE_DRIFT')
        # Only one *raw* E8 caller of each constructor in executable section;
        # then independently confirm it is exactly a known decoded call.
        only={v[2]:v[3] for v in VTABLES.values()}
        candidates=direct_call_candidates(pe,only)
        for dst,site in only.items():
            if candidates[dst]!=[site] or site not in all_dis:
                raise ValueError('EXTRA_B_CONSTRUCTOR_CALL:'+hex(dst))
        return {
            'schema':'bsc.n1.R36_B_subtypes_and_task_phase.v1',
            'proof':'FIXED_NEW_EXE_READ_ONLY_STATIC',
            'sha256':sha,'file_size':len(pe.d),'imagebase':hex(pe.base),
            'verified_opcode_starts':len(observed),
            'verified_unwind_functions':len(groups),
            'verified_E8':len(CALLS),'verified_jumps':len(JUMPS),
            'verified_B_vtable_method_slots':len(VTABLES),
            'B_constructors':{label:{'ctor':hex(ctor),'table':hex(table),'virtual_10':hex(method),'single_direct_ctor_caller':hex(site)}
                for label,(table,method,ctor,site) in VTABLES.items()},
            'same_group_storage':'3 distinct B task subtypes can be installed into a given Group+0x908 through distinct senders',
            'B1_route_mode':'03286288 -> 032862C4; conditional +0x58 route regeneration/cleanup, no direct member fanout in these 2 functions',
            'B2_fanout_mode':'032863A0 -> 03286445 E8 0326A994 -> member virtual+0x368 (condition gated)',
            'B3_packet_mode':'03286480 -> 03286572 E8 0326B0C8 -> indirect preparer; not proven direct member virtual+0x368 in this call',
            'callback_branch':'bigTask+0x20 state4 with +0x24 nonzero can reach 0327ECA4 (B1 if mode=false); +0x24 zero and bigTask+0x28==3 can reach 02F54510 -> 0327ED4C (B2 if mode=false)',
            'caller_dispatch_mutually_exclusive_per_callback_invocation':True,
            'group_slot_cleanup':'02F3F0FC conditionally invokes existing embedded object destructor only if parent+0x118 == 1, then clears status flags',
            'route_and_group_current_read':'B1 path 02F5B3F9; B2 path 02F54621; both read present UnitRoot+0x32F8 for these calls, but independently gated',
            'two_B_modes_on_same_player_shift_record_observed':False,
            'group_generation_mismatch_proven':False,
            'member_world_goal_error_proven':False,
            'gameplay_patch_authorized':False,
        }
    finally:pe.close()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',required=True,type=Path)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    if args.out and args.exe.resolve()==args.out.resolve():ap.error('CANNOT_OVERWRITE_ORIGINAL_EXE')
    output=audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('R36_STATIC_PASS',output['verified_opcode_starts'],'instructions',output['verified_E8'],'E8',
          output['verified_jumps'],'branches',output['verified_B_vtable_method_slots'],'vtable slots; NO PATCH')

if __name__=='__main__':main()
