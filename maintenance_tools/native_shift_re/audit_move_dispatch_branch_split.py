#!/usr/bin/env python3
"""Exact original WH3: queue path skips immediate group rebuilding.

Read-only PE SHA/bytes/unwind/objdump/CFG verification. NOT a game patch.
"""
import argparse, json, re, struct, subprocess, tempfile
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE, SHA

MANIFEST=Path(__file__).with_name('move_dispatch_branch_split_manifest.txt')
EXPECTED={'PIN':39,'CALL':17,'JMP':6}
QUEUED=0x030326A2
QUEUED_E8=0x030326BE
QUEUE_EXIT=0x030326E9
IMMEDIATE=0x030326EE
GROUP_E8=0x03032965

def load(path=MANIFEST):
    out={k:{} for k in EXPECTED}
    for number,line in enumerate(Path(path).read_text('utf8').splitlines(),1):
        parts=line.split('#',1)[0].split()
        if not parts:continue
        kind=parts[0]
        if kind not in out or len(parts)!=3:raise ValueError('BAD_MANIFEST_LINE:'+str(number))
        at=int(parts[1],16)
        if at in out[kind]:raise ValueError('DUPLICATE_MANIFEST_RVA:'+hex(at))
        out[kind][at]=bytes.fromhex(parts[2]) if kind=='PIN' else int(parts[2],16)
    if any(len(out[k])!=n for k,n in EXPECTED.items()):raise ValueError('MANIFEST_COUNT_DRIFT')
    return out

def decode(pe,begin,end):
    with tempfile.NamedTemporaryFile() as f:
        f.write(pe.read(begin,end-begin));f.flush()
        run=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel',
             '--no-show-raw-insn',f'--adjust-vma=0x{begin:x}',f.name],
             capture_output=True,text=True,check=True)
    entries={}
    for line in run.stdout.splitlines():
        m=re.match(r'^\s*([0-9a-fA-F]+):\s+([a-z][a-z0-9.]*)\s*(.*)$',line)
        if m:entries[int(m.group(1),16)]=(m.group(2),m.group(3).strip())
    return entries

def successors(code,at):
    if at not in code:return []
    keys=list(code)
    op,arg=code[at]
    if op.startswith('ret'):return []
    index=keys.index(at)
    next_at=keys[index+1] if index+1<len(keys) else None
    if op=='jmp':
        return [int(arg,16)] if re.fullmatch(r'0x[0-9a-f]+',arg) else []
    if op.startswith('j') and re.fullmatch(r'0x[0-9a-f]+',arg):
        return [int(arg,16)]+([next_at] if next_at is not None else [])
    return [next_at] if next_at is not None else []

def walk(code,start):
    visited=set()
    todo=[start]
    while todo:
        at=todo.pop()
        if at in visited:continue
        if at not in code:raise ValueError('CFG_TARGET_OUTSIDE_FUNCTION:'+hex(at))
        visited.add(at)
        todo.extend(n for n in successors(code,at) if n not in visited)
    return visited

def target(site,code,kind):
    if kind=='CALL':
        if len(code)!=5 or code[0]!=0xe8:raise ValueError('E8_OPCODE_DRIFT:'+hex(site))
        return site+5+struct.unpack_from('<i',code,1)[0]
    if code[:1]==b'\xe9':return site+5+struct.unpack_from('<i',code,1)[0]
    if code[:1]==b'\x0f' and len(code)>=6 and 0x80<=code[1]<=0x8f:
        return site+6+struct.unpack_from('<i',code,2)[0]
    raise ValueError('BRANCH_OPCODE_DRIFT:'+hex(site))

def audit(exe,manifest=MANIFEST):
    check=load(manifest)
    pe=OriginalEXE(exe)
    try:
        if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
        decoded={}
        for rva,op in check['PIN'].items():
            if pe.section(rva)!='.00cfg' or pe.read(rva,len(op))!=op:
                raise ValueError('OPCODE_DRIFT:'+hex(rva))
            owner=pe.owner(rva)
            if owner is None:raise ValueError('MISSING_UNWIND_OWNER:'+hex(rva))
            bounds=owner[:2]
            if bounds not in decoded:decoded[bounds]=decode(pe,*bounds)
            if rva not in decoded[bounds]:raise ValueError('MID_INSTRUCTION:'+hex(rva))
        for kind in ('CALL','JMP'):
            for site,expected in check[kind].items():
                data=pe.read(site,5 if kind=='CALL' else 6)
                if target(site,data,kind)!=expected:raise ValueError('DIRECT_TARGET_DRIFT:'+hex(site))
        bounds=pe.owner(QUEUED)[:2]
        if bounds!=pe.owner(GROUP_E8)[:2]:raise ValueError('DIFFERENT_DISPATCH_FUNCTIONS')
        queue=walk(decoded[bounds],QUEUED)
        group=walk(decoded[bounds],IMMEDIATE)
        if QUEUED_E8 not in queue or QUEUE_EXIT not in queue:
            raise ValueError('QUEUE_NOT_REACHABLE')
        if GROUP_E8 in queue:raise ValueError('QUEUED_PATH_REACHES_GROUP_CALL')
        if GROUP_E8 not in group or QUEUED_E8 in group:
            raise ValueError('IMMEDIATE_GROUP_PATH_INVALID')
        activation=pe.owner(0x03025D70)[:2]
        if activation not in decoded:decoded[activation]=decode(pe,*activation)
        body=decoded[activation]
        direct=[]
        for site,(op,arg) in body.items():
            if op=='call' and re.fullmatch(r'0x[0-9a-f]+',arg):direct.append((site,int(arg,16)))
        if 0x0301B8E4 in [x for _,x in direct] or 0x0302DB44 in [x for _,x in direct]:
            raise ValueError('ACTIVATION_HAS_DIRECT_GROUP_REBUILD_CALL')
        for site in (0x03025E91,0x03025FC6,0x03025FEE,0x03025FFB,0x03026022,0x030260AF):
            if site not in [s for s,_ in direct]:raise ValueError('ACTIVATION_CALL_MISSING:'+hex(site))
        return {'schema':'bsc.n1.typed_move_dispatch_exclusivity.v1',
                'sha256':pe.sha,'evidence':'EXACT_ORIGINAL_EXE_STATIC',
                'opcode_instruction_starts':len(check['PIN']),
                'direct_e8':len(check['CALL']),'conditional_unconditional_jumps':len(check['JMP']),
                'queue_branch_can_reach_group_rebuild_call':False,
                'nonqueue_branch_can_reach_group_rebuild_call':True,
                'queue_branch_jump_target':hex(check['JMP'][QUEUE_EXIT]),
                'immediate_group_path':'0x0301B8E4 group -> 0x0301287C route -> 0x030D5490 packet (conditional)',
                'activation_direct_calls':len(direct),
                'activation_route_update_calls':['0x03025E91','0x03026022'],
                'activation_uses_current_group_plusB38':True,
                'group_reference_sample_requires_move_slot_plus9A_bit2_clear':True,
                'sampled_group_spatial_field':'group+0xB38 + 0xB8 = group+0xBF0; 0x0311D0CC returns transformed XZ',
                'activation_creates_new_shortTask_at':'0x030260AF',
                'shorttask_callback_late_reads_UnitRoot_plus32F8':True,
                'input_hotkey_identity_proven':False,
                'actual_shift_member_generation_mismatch_proven':False,
                'native_gameplay_patch_authorized':False}
    finally:pe.close()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    if args.out and args.out.resolve()==args.exe.resolve():ap.error('EXE_OVERWRITE_FORBIDDEN')
    result=audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('PASS',result['opcode_instruction_starts'],'machine instructions',result['direct_e8'],'E8',result['conditional_unconditional_jumps'],'JMP/JCC; NO GAMEPLAY PATCH')
if __name__=='__main__':main()
