#!/usr/bin/env python3
"""Exact WH3 9.0.3 native MOVE queue object handoff, read-only proof.

Separates native task *identity* from per-leg geometry. Does not infer user
RMB/Shift keys from a static flag, prove soldier crowding, or patch game code.
"""
import argparse,json,re,struct,shutil
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

PINS={
0x030323FC:'458af1',0x030326B4:'488d8b78020000',
0x030326BB:'418ad6',0x030326BE:'e84dddf1ff',
0x030326E4:'e8d369fdff',
0x02F50425:'84d2',0x02F50427:'7520',
0x02F50430:'c6811c2d000001',0x02F50444:'e84b9bfeff',
0x02F504C2:'41ff80082d0000',0x02F504D7:'4183b8082d000028',
0x02F39FA9:'e8625d0100',
0x030090D1:'488d1518249000',0x030090D8:'488917',
0x030090E7:'4883a7a000000000',
0x0304455F:'488b01',0x03044562:'ff5040',
0x03044596:'ff5038',0x0304459D:'ff4618',
0x030445A8:'488bd6',0x030445AB:'ff5048',
0x03039FB4:'488b91a0000000',0x03039FC0:'837a2004',
0x03039FC6:'807a2400',0x03039FCC:'4883ba5801000000',
0x03039FE5:'e8aa97d2ff',0x03039FEE:'488bc2',
0x030408AF:'e800b9fdff',0x030408CF:'c7422001000000',
0x030408EC:'0f118220010000',0x030408F8:'0f118a30010000',
0x030408FF:'0f118240010000',0x03040906:'498991a0000000',
0x008D3350:'b001c3',0x0301C1B4:'f6819a00000004'}
EDGES={
0x030326BE:0x02F50410,0x030326E4:0x030090BC,
0x02F50444:0x02F39F94,0x02F39FA9:0x02F4FD10,
0x03039FE5:0x02D63794,0x030408AF:0x0301C1B4}
SLOT_VTABLE=0x0390B4F0
SLOT_METHODS={
0x00:0x0300C660,0x08:0x03025D70,
0x38:0x008D3350,0x40:0x03039FB0,0x48:0x03040864}
LEAVES={0x008D3350,0x0301C1B4}

def checked_opcode_starts(pe):
    if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
    by_owner={};verified=[]
    for site in PINS:
        if pe.read(site,len(PINS[site])//2,True).hex()!=PINS[site]:
            raise ValueError('NATIVE_OPCODE_CHANGED:'+hex(site))
        owner=pe.function(site)
        if owner is None:
            if site not in LEAVES:
                raise ValueError('UNSUPPORTED_NO_UNWIND_SITE:'+hex(site))
            verified.append(site)
            continue
        by_owner.setdefault(owner,[]).append(site)
    for (start,end),sites in by_owner.items():
        lines=pe.disasm(start,end-start).splitlines()
        starts=set()
        for line in lines:
            m=re.match(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+',line)
            if m:starts.add(int(m.group(1),16))
        for site in sites:
            if site not in starts:raise ValueError('MIDDLE_OF_INSTRUCTION:'+hex(site))
            verified.append(site)
    return len(verified)

def audit(exe):
    pe=StrictPE(Path(exe))
    try:
        count=checked_opcode_starts(pe)
        for caller,callee in EDGES.items():
            data=pe.read(caller,5,True)
            actual=caller+5+struct.unpack_from('<i',data,1)[0]
            if data[0]!=0xe8 or actual!=callee:
                raise ValueError('E8_CALL_TARGET_CHANGED:'+hex(caller))
        for offset,target in SLOT_METHODS.items():
            ptr=struct.unpack('<Q',pe.read(SLOT_VTABLE+offset,8))[0]
            if ptr!=pe.base+target:raise ValueError('MOVE_SLOT_VTABLE_CHANGED:'+hex(offset))
        if struct.unpack('<Q',pe.read(0x03AE00E8+0x10,8))[0]==pe.base+0x03025D70:
            raise ValueError('CACHED_B_TASK_CLASS_ALIAS')
        return {
          'schema':'bsc.n1.exact_move_queue_object_handoff.v1',
          'original_exe_sha256':pe.sha,'evidence_grade':'EXACT_EXE_STATIC',
          'exact_opcode_and_instruction_guards':count,
          'direct_e8_edges':len(EDGES),
          'MOVE_slot_vtable_entries':len(SLOT_METHODS),
          'queued_MOVE_slot_vtable':hex(SLOT_VTABLE),
          'branch':'R9B->R14B->DL; DL=0 clears queue, nonzero appends',
          'queue_ring_capacity':40,
          'source_slot_getter':'0x03039FB0',
          'source_task_eligibility':{
              'task_plus_20_status':4,
              'task_plus_24_nonzero':True,
              'task_plus_158_nonnull':True,
              'group_helper_passed':True},
          'next_slot_setter':'0x03040864',
          'task_pointer_identity_preserved_when_eligible':True,
          'new_task_status':1,
          'rewritten_task_geometry_offsets':['0x120','0x130','0x140'],
          'next_slot_plus_a0_aliases_old_task':True,
          'task_plus_158_cleared_by_setter':False,
          'member_motor_goal_cleared_by_setter':False,
          'command_keys_confirmed':False,
          'user_gameplay_instance_confirmed':False,
          'physical_crowding_root_cause_proven':False,
          'native_patch_authorized':False}
    finally:pe.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.exe.resolve()==args.out.resolve():p.error('NO_EXE_OVERWRITE')
    result=audit(args.exe)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('PASS',len(PINS),'original opcodes + starts',len(EDGES),'E8 edges',
          len(SLOT_METHODS),'typed virtual methods; NO GAME PATCH')
if __name__=='__main__':main()
