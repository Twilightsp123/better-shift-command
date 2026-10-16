#!/usr/bin/env python3
"""Read-only exact original EXE: per-member route installation and goal commit."""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA
PINS=Path(__file__).with_name('member_goal_commit_pins_20261016.txt')
E8={0x03071e86:0x03071f20,0x030720e3:0x0311954c,
    0x030723d9:0x0311954c,0x0325ea85:0x03071e04,
    0x0311957d:0x03126f64}
JCC={0x03119563:0x0311968c,0x031195d6:0x0311961e,
     0x031195f9:0x0311961e,0x0311961c:0x0311962a,
     0x0325e9e2:0x0325eb6d,0x0325e9ec:0x0325eb6d,
     0x0325ea0a:0x0325eb6d,0x0325ea25:0x0325ea93}
EPSILON=struct.unpack('<f',bytes.fromhex('0ad7233c'))[0]
def pins():
    d={}
    for line in PINS.read_text('utf8').splitlines():
        fields=line.split('#',1)[0].split()
        if not fields:continue
        if len(fields)!=2:raise ValueError('BAD_PIN')
        at=int(fields[0],16)
        if at in d:raise ValueError('DUPLICATE_PIN')
        d[at]=bytes.fromhex(fields[1])
    if len(d)!=60:raise ValueError('PIN_COUNT_DRIFT')
    return d

def goal_dedup(old,new,same_token,same_heading,flags):
    """Only the bounded coordinate/identity branch, not all native gates."""
    return not (flags & 0x200) and same_token and same_heading and \
        len(old)==len(new)==3 and all(abs(a-b)<=EPSILON for a,b in zip(old,new))

def direct_calls(exe,target):
    sect=next((s for s in exe.sections if s[0]=='.00cfg'),None)
    if sect is None:raise ValueError('TEXT_SECTION_MISSING')
    name,va,span,rp,rawsize=sect
    blob=exe.mm[rp:rp+rawsize];offset=0;hits=[];starts={}
    while True:
        i=blob.find(b'\xe8',offset)
        if i<0 or i+5>len(blob):break
        offset=i+1
        at=va+i
        if at+5+struct.unpack_from('<i',blob,i+1)[0]!=target:continue
        owner=exe.owner(at)
        if owner is None:continue
        bounds=owner[:2]
        if bounds not in starts:starts[bounds]=exe.starts_in(*bounds)
        if at in starts[bounds]:hits.append(at)
    return sorted(set(hits))

def audit(path):
    exe=OriginalEXE(path)
    try:
        if exe.sha!=SHA:raise ValueError('SHA_MISMATCH')
        starts={}
        for at,b in pins().items():
            if exe.section(at)!='.00cfg' or exe.read(at,len(b))!=b:
                raise ValueError('OPCODE_DRIFT:'+hex(at))
            owner=exe.owner(at)
            if owner is None:raise ValueError('NO_UNWIND_OWNER:'+hex(at))
            bounds=owner[:2]
            if bounds not in starts:starts[bounds]=exe.starts_in(*bounds)
            if at not in starts[bounds]:raise ValueError('MID_INSTRUCTION:'+hex(at))
        for at,target in E8.items():
            b=exe.read(at,5)
            if b[0]!=0xe8 or at+5+struct.unpack_from('<i',b,1)[0]!=target:
                raise ValueError('E8_DRIFT:'+hex(at))
        for at,target in JCC.items():
            b=exe.read(at,6)
            if b[0]==0x0f and 0x80<=b[1]<=0x8f:
                got=at+6+struct.unpack_from('<i',b,2)[0]
            elif 0x70<=b[0]<=0x7f:
                got=at+2+struct.unpack_from('<b',b,1)[0]
            else:raise ValueError('JCC_OPCODE_DRIFT')
            if got!=target:raise ValueError('JCC_DRIFT:'+hex(at))
        if exe.read(0x0391ccfc,4)!=bytes.fromhex('0ad7233c'):
            raise ValueError('GOAL_EPSILON_DRIFT')
        goals=direct_calls(exe,0x0311954c)
        routes=direct_calls(exe,0x03071e04)
        if len(goals)!=8 or len(routes)!=25:raise ValueError('DIRECT_CALL_INVENTORY_DRIFT')
        return {'schema':'bsc.n1.member_goal_commit_gates.v1',
          'sha256':exe.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
          'guarded_instructions':60,'guarded_e8':len(E8),'guarded_jcc':len(JCC),
          'target_epsilon':EPSILON,
          'motor_goal_direct_call_sites':[hex(i) for i in goals],
          'route_installer_direct_call_sites':[hex(i) for i in routes],
          'motor_goal_setter':'0x0311954C',
          'goal_commit':'member+0x1e0 16 bytes, +0x1f0 token, +0x180 scalar, +0x188 flags',
          'goal_skip':'member+0x228==1; token+heading+three-axis epsilon; r9 bit9 bypass',
          'route_installer':'0x03071E04 writes member+0x7f8/+0x818 and resets +0x710',
          'per_member_action':'0x0325EA85 gated call; action+0x7d latched at 0x0325EA8A',
          'runtime_Shift_causal_gate_found':False,
          'gameplay_patch_authorized':False}
    finally:exe.close()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    if args.out and args.out.resolve()==args.exe.resolve():
        ap.error('EXE_OVERWRITE_FORBIDDEN')
    data=audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('PASS',data['guarded_instructions'],'original opcodes',
          data['guarded_e8'],'E8',data['guarded_jcc'],'JCC',
          len(data['motor_goal_direct_call_sites']),'goal sites; NO PATCH')
if __name__=='__main__':main()
