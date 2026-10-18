#!/usr/bin/env python3
"""R43 read-only, SHA-locked WH3 native member pending-input / delta handoff audit.

No game-process instrumentation or patch. Reported paths are conditional and NOT
proven to be caused by a player's Shift MOVE.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from audit_r35_group_transaction_20261017 import PE, disasm, branch_dest

HERE=Path(__file__).resolve().parent
MANIFEST=HERE/'r43_member_pending_goal_delta_pins_20261018.txt'
SHA='9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496'
SIZE=232531920
BASE=0x140000000
MEMBER_VTABLE=0x03912950
VTABLE_SLOTS={0x18:0x03086F04, 0x20:0x030592BC,0x128:0x03084B5C}
FUNCTION_GROUPS=9
PIN_COUNT=101
CALLS={
  0x03053128:0x03051D98,
  0x03087013:0x03065DB8,
  0x03065EB2:0x03154974,
  0x0315498F:0x03169594,
  0x03071CC9:0x0315FB24,
  0x0315FB3C:0x03169594,
}
JUMPS={
  0x03086FD9:0x0308706F,
  0x031471B8:0x0314738F,
  0x031471C4:0x03147306,
  0x03154A70:0x03154A7E,
  0x0315FB44:0x0315FB5B,
  0x0314738A:0x031484D9,
}
# Limit all full-section direct E8 caller inventories to exact original EXE
# and verify actual instruction starts, not arbitrary embedded E8 bytes.
DIRECT_CALLER_EXPECTED={
  0x03154974:(0x03065EB2,),
  0x0315FB24:(0x03071CC9,),
  0x03146FF0:(0x030592F8,0x031000F6,0x0310014C),
}


def inventory(path=MANIFEST):
    out={}; name=None
    for line in Path(path).read_text('utf-8').splitlines():
        m=re.fullmatch(r'# (\w+) bounds=([0-9A-Fa-f]+):([0-9A-Fa-f]+) count=(\d+)',line)
        if m:
            name,lo,hi,count=m.groups()
            if name in out:raise ValueError('DUPLICATE_GROUP')
            out[name]={'span':(int(lo,16),int(hi,16)),'count':int(count),'pins':{}}
            continue
        row=line.split('#',1)[0].split()
        if not row:continue
        if name is None or len(row)!=2:raise ValueError('BAD_PIN_ROW')
        at=int(row[0],16)
        if at in out[name]['pins']:raise ValueError('DUPLICATE_INSTRUCTION')
        out[name]['pins'][at]=bytes.fromhex(row[1])
    pins=[at for g in out.values() for at in g['pins']]
    if len(out)!=FUNCTION_GROUPS or len(pins)!=PIN_COUNT or len(pins)!=len(set(pins)):
        raise ValueError('PIN_OR_GROUP_COUNT_DRIFT')
    if any(len(g['pins'])!=g['count'] for g in out.values()):raise ValueError('GROUP_PIN_COUNT_DRIFT')
    return out


def direct_callers(p,targets):
    """Executable code-section scan; require objdump call instruction boundaries."""
    targets=set(targets)
    possible={t:[] for t in targets}
    for _,va,virtual,raw,rp,flags in p.sections:
        if not (flags & 0x20000000):continue
        data=p.d[rp:rp+raw]
        pos=0
        while True:
            i=data.find(b'\xe8',pos)
            if i<0:break
            pos=i+1
            if i+5>len(data):continue
            t=va+i+5+struct.unpack_from('<i',data,i+1)[0]
            if t not in targets:continue
            at=va+i
            owner=p.owner(at)
            if owner:possible[t].append((at,owner))
    verified={t:[] for t in targets}; cache={}
    for t,items in possible.items():
        for at,owner in items:
            if owner not in cache:cache[owner]=disasm(p,*owner)
            if cache[owner].get(at,'').startswith('call'):
                verified[t].append(at)
    return {t:tuple(sorted(set(x))) for t,x in verified.items()}


def _text(decoded,group,at):return decoded[group].get(at,'')

def audit(exe):
    exe=Path(exe)
    if not exe.is_file():raise ValueError('EXE_NOT_FOUND')
    with exe.open('rb') as f:actual_sha=hashlib.file_digest(f,'sha256').hexdigest()
    if actual_sha!=SHA:raise ValueError('EXE_SHA256_MISMATCH:'+actual_sha)
    p=PE(exe)
    try:
        if p.base!=BASE or len(p.d)!=SIZE:raise ValueError('PE_IDENTITY_CHANGED')
        groups=inventory(); decoded={}; opcodes={}
        for name,g in groups.items():
            lo,hi=g['span']
            if not p.is_executable(lo):raise ValueError('NON_EXECUTABLE_FUNCTION:'+name)
            if name=='unlink_leaf':
                if p.owner(lo) is not None:raise ValueError('LEAF_UNWIND_CHANGED')
            elif p.owner(lo)!=(lo,hi):
                raise ValueError('UNWIND_FUNCTION_DRIFT:'+name)
            ins=disasm(p,lo,hi)
            decoded[name]=ins
            for at,raw in g['pins'].items():
                if not (lo<=at<hi) or at not in ins:raise ValueError('INVALID_DECODE_START:'+hex(at))
                if p.read(at,len(raw))!=raw:raise ValueError('OPCODE_DRIFT:'+hex(at))
                opcodes[at]=raw
        for at,target in CALLS.items():
            raw=opcodes[at]
            if len(raw)!=5 or raw[0]!=0xe8 or at+5+struct.unpack_from('<i',raw,1)[0]!=target:
                raise ValueError('E8_TARGET_DRIFT:'+hex(at))
        for at,target in JUMPS.items():
            if branch_dest(at,opcodes[at])!=target:
                raise ValueError('BRANCH_TARGET_DRIFT:'+hex(at))
        for slot,target in VTABLE_SLOTS.items():
            if struct.unpack('<Q',p.read(MEMBER_VTABLE+slot,8))[0]!=BASE+target:
                raise ValueError('TYPED_VTABLE_DRIFT:'+hex(slot))
        # Constructor is the same typed object as the Tick; the deferred
        # subrecord constructor is passed a pointer INTO the member object.
        member=decoded['member_ctor'];tick=decoded['member_tick']
        ctor_lea=opcodes[0x03052D20]
        if ctor_lea[:3]!=bytes.fromhex('488d05') or \
           0x03052D20+7+struct.unpack_from('<i',ctor_lea,3)[0]!=MEMBER_VTABLE or \
           member.get(0x03052D34)!='mov    QWORD PTR [rbx],rax':
            raise ValueError('MEMBER_CONSTRUCTOR_VTABLE_IDENTITY_DRIFT')
        if _text(decoded,'member_ctor',0x0305306F)!='lea    rcx,[rbx+0x8d8]' or \
           _text(decoded,'member_tick',0x03086F2C)!='mov    rdi,rcx':
            raise ValueError('MEMBER_AND_EMBEDDED_RECORD_IDENTITY_DRIFT')
        if _text(decoded,'member_tick',0x03086F48)!='xor    r14d,r14d' or \
           _text(decoded,'member_tick',0x03086FD2)!='cmp    BYTE PTR [rdi+0x8d8],r14b':
            raise ValueError('PENDING_GATE_DRIFT')
        if _text(decoded,'member_tick',0x03086FE5)!='lea    r8,[rdi+0x8dc]' or \
           _text(decoded,'member_tick',0x03086FF1)!='lea    rdx,[rdi+0x8e8]' or \
           _text(decoded,'member_tick',0x03087005)!='mov    rcx,rdi':
            raise ValueError('MEMBER_TICK_PENDING_ARGUMENT_ALIAS_DRIFT')
        if _text(decoded,'member_tick',0x0308700C)!='mov    BYTE PTR [rdi+0x8d8],r14b' or \
           not(0x03086FD2<0x0308700C<0x03087013<0x03087018<0x03087034<0x0308705B):
            raise ValueError('PENDING_CONSUME_PHASE_DRIFT')
        apply=decoded['pending_apply']
        required={
          0x03065DD6:'mov    rbp,r8',0x03065DD9:'mov    rdi,rdx',
          0x03065DDC:'mov    rbx,rcx',
          0x03065E8A:'movups xmm0,XMMWORD PTR [rdi]',
          0x03065E9B:'mov    rcx,rbx',
          0x03065E9E:'movups XMMWORD PTR [rbx+0x1e0],xmm0',
          0x03065EA5:'movsd  xmm1,QWORD PTR [rdi+0x10]',
          0x03065EAA:'movsd  QWORD PTR [rbx+0x1f0],xmm1',
          0x03065E98:'mov    rdx,rbp',
        }
        for at,expected in required.items():
            if apply.get(at)!=expected:raise ValueError('PENDING_SOURCE_TO_GOAL_OR_VECTOR_DRIFT:'+hex(at))
        # Callee 0x03169594 is a verified no-unwind leaf function that
        # uses RCX but DOES NOT clobber it or make a nested call.
        unlink=decoded['unlink_leaf']
        if any(re.match(r'^(?:mov|lea|add|sub|xor|and|or|pop|xchg|shl|shr|sar)\s+(?:rcx|ecx|cx|cl|r10|r10d|r10b|r11|r11d|r11b)\b',ins)
               for ins in unlink.values()) or any('call' in ins for ins in unlink.values()) or \
           unlink[0x03169628]!='ret':
            raise ValueError('LEAF_HELPER_CLOBBERS_MEMBER_RCX')
        stage=decoded['delta_install']
        for at,expected in {
          0x03154983:'mov    bl,r9b',0x03154986:'mov    r11b,r8b',
          0x03154989:'mov    r10,rdx',0x0315498C:'mov    rdi,rcx',
          0x0315499C:'mov    dl,BYTE PTR [rcx+0x108]',
          0x031549AC:'or     dl,0x2',
          0x031549DC:'mulss  xmm3,DWORD PTR [r10]',
          0x031549E1:'mulss  xmm1,DWORD PTR [r10+0x4]',
          0x031549E7:'mulss  xmm2,DWORD PTR [r10+0x8]',
          0x03154A10:'movsd  QWORD PTR [rcx+0x13c],xmm0',
          0x03154A18:'mov    DWORD PTR [rcx+0x144],eax',
          0x03154A4C:'mov    BYTE PTR [rcx+0x108],dl',
        }.items():
            if stage.get(at)!=expected:raise ValueError('VECTORS_TO_TYPED_DELTA_DRIFT:'+hex(at))
        # A verified alternate same-field-layout routine clears the delta,
        # but this is NOT a proof the player Shift branch takes that route.
        alt=decoded['target_alt'];reset=decoded['delta_alt']
        if alt[0x03071CB5]!='movups XMMWORD PTR [rbp+0x1e0],xmm0' or \
           alt[0x03071CC1]!='movsd  QWORD PTR [rbp+0x1f0],xmm1' or \
           reset[0x0315FB68]!='movsd  QWORD PTR [rcx+0x13c],xmm0' or \
           reset[0x0315FB76]!='mov    DWORD PTR [rcx+0x144],eax':
            raise ValueError('ALTERNATE_GOAL_DELTA_PATH_DRIFT')
        for at in (0x03154A1E,0x03154A2E,0x0315FBB2,0x0315FBC2):
            # Each instruction loads from zero-initialized PE data.
            if '[rip+' not in decoded['delta_install' if at<0x0315FB24 else 'delta_alt'][at]:
                raise ValueError('FLOAT_REFERENCE_DRIFT')
        if struct.unpack('<f',p.read(0x04073278,4))[0]!=0.0 or \
           struct.unpack('<f',p.read(0x0407327C,4))[0]!=0.0:
            raise ValueError('RESET_CONSTANTS_NONZERO')
        # Exact direct stores of +0x14c/+0x150 by these scoped, typed
        # handlers use the same zero-valued image data constants.
        for name,expected in {
          'delta_install':(0x03154A26,0x03154A44),
          'delta_alt':(0x0315FBBA,0x0315FBCA),
          'integrator':(0x031472E7,0x031472FE,0x03148442,0x03148452),
        }.items():
            for site in expected:
                if f'+0x{(0x14c if site in (0x03154A26,0x0315FBBA,0x031472E7,0x03148442) else 0x150):x}]' not in decoded[name][site]:
                    raise ValueError('SCOPED_RESET_FIELD_DRIFT:'+hex(site))
        if not (0x03147199<0x031471B8<0x031471C4<0x0314720B<0x031472C3<0x031472E7):
            raise ValueError('INTEGRATOR_DELTA_CONSUMPTION_ORDER_DRIFT')
        callers=direct_callers(p,DIRECT_CALLER_EXPECTED.keys())
        if any(callers[t]!=calls for t,calls in DIRECT_CALLER_EXPECTED.items()):
            raise ValueError('GLOBAL_E8_CALLER_INVENTORY_DRIFT')
        return dict(schema='bsc.n1.r43_pending_member_goal_delta_handoff.v1',
            proof='READ_ONLY_NEW_EXE_SHA_LOCKED_NATIVE_STATIC',
            exe_sha256=actual_sha, executable_size=SIZE, imagebase=hex(BASE),
            pinned_opcode_starts=PIN_COUNT, function_groups=FUNCTION_GROUPS,
            validated_direct_e8=len(CALLS), validated_jumps=len(JUMPS),
            validated_vtable_slots=len(VTABLE_SLOTS),
            validated_direct_callers={hex(t):[hex(x) for x in callers[t]] for t in DIRECT_CALLER_EXPECTED},
            initial_constructor_pending_record='member+0x8d8 -> 0x03051D98 initializes embedded record',
            pending_member_tick='if member+0x8d8 nonzero: pending goal member+0x8e8 and vector member+0x8dc; clear gate then call 0x03065DB8',
            direct_goal_vector_handoff='0x03065DB8 copies member+0x8e8 into member+0x1e0; passes member+0x8dc to 0x03154974',
            direct_delta_install='0x03154974 scales provided vector into member+0x13c/+0x140/+0x144, sets bit2 and zeroes +0x14c/+0x150',
            alternate_path='0x03071C84->0x0315FB24 replaces goal then clears delta; live Shift caller identity not proven',
            typed_reset_14c150='scoped verified writers set +0x14c/+0x150 to image-initialized 0.0',
            all_possible_member_delta_writers_exhaustively_identified=False,
            new_shift_move_reaches_pending_path_proven=False,
            stale_goal_after_shift_turn_observed=False,
            runtime_unit_member_phase_order_proven=False,
            root_cause_proven=False,gameplay_patch_authorized=False)
    finally:p.close()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',required=True,type=Path)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    if args.out is not None and args.out.resolve()==args.exe.resolve():
        ap.error('CANNOT_OVERWRITE_GAME_EXE')
    r=audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
    print('R43_STATIC_PASS',r['pinned_opcode_starts'],'pins',r['validated_direct_e8'],'calls',
          r['validated_jumps'],'jumps',r['validated_vtable_slots'],'vtable; NO PATCH')

if __name__=='__main__':main()
