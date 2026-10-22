#!/usr/bin/env python3
"""BSC R61: cross-check the actual new-EXE native delayed/immediate packet cleanup boundaries.

This is a strict SHA-pinned *static* audit and symbolic-branch matrix, NOT an
instrumentation agent and NOT a gameplay patch. It does not read game processes.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct
from pathlib import Path
from r61_pe_readonly import PE

HERE=Path(__file__).resolve().parent
SHA256='9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496'
IMAGEBASE=0x140000000
PINS=HERE/'r61_invariant_pins.txt'
# These are externally recovered function boundaries, NOT imputed from offset equality.
LEAF_SPANS=[(0x02DC7E30,0x02DC7E48),(0x02F648E4,0x02F6496B)]
E8={
  0x03070A7B:0x02DC7E30,0x0327ECC6:0x02DC7E30,
  0x03070A94:0x02DB5AC4,0x03070AB3:0x02F647D0,
  0x030782B0:0x0307AE84,0x03078985:0x0307AE84,
  0x0307AE9B:0x02DB5AC4,0x0307AEA7:0x02DB5A20,0x0307AED1:0x0324D994,
  0x030782CF:0x03163DC4,0x030785B5:0x0316460C,
  0x0307860D:0x03078944,0x03077F26:0x03078268,
  0x0327ED17:0x030DA5D8,0x0327ED3C:0x03268920,
  0x0326AAD9:0x0326F210,0x0326F2D6:0x02F648E4,
}
JUMPS={
 0x03070A85:0x03070ABD,0x03070A8B:0x03070ABD,
 0x03070AB8:0x03070C32,0x03070B52:0x03070B6F,
 0x0307828E:0x030782B5,0x030782AE:0x030782B5,
 0x03078983:0x0307898A,0x0327ECCD:0x0327ED1E,
}
MEMBER_TABLES={
 'regular':(0x03912950,{0xe8:0x03078268,0x100:0x030785AC,0x478:0x03078944}),
 'special':(0x03AD3360,{0xe8:0x03077EE4,0x100:0x030785AC,0x478:0x030785E0}),
}

def h(x):return '0x'+format(x,'08X')

def read_pins():
    pins={}
    for line in PINS.read_text().splitlines():
        w=line.split('#',1)[0].split()
        if not w:continue
        if len(w)!=2:raise ValueError('INVALID_PIN_ROW')
        at=int(w[0],16)
        if at in pins:raise ValueError('DUPLICATE_PIN')
        pins[at]=bytes.fromhex(w[1])
    if len(pins)!=71:raise ValueError(f'PIN_COUNT_DRIFT_{len(pins)}')
    return pins

def branch_target(at,b):
    if len(b)==2 and 0x70<=b[0]<=0x7f:return at+2+struct.unpack_from('<b',b,1)[0]
    if len(b)==5 and b[0]==0xe9:return at+5+struct.unpack_from('<i',b,1)[0]
    if len(b)==6 and b[:1]==b'\x0f' and 0x80<=b[1]<=0x8f:return at+6+struct.unpack_from('<i',b,2)[0]
    raise ValueError(f'UNKNOWN_JUMP_{at:x}')

def helper(mode):
    if not isinstance(mode,int) or mode<0 or mode>0xffffffff:raise ValueError('BAD_MODE')
    return int(mode<=5 and bool((0x29>>mode)&1))

def packet_bit20_from_b2(input_a,input_b,optional_bit8=False):
    # B2 constructor: 0x06 | (argA&1) | ((argB&1)<<4); only extra local bit 0x08.
    return 0x06|(input_a&1)|((input_b&1)<<4)|(0x08 if optional_bit8 else 0)

def receiver_packet_path(mode,packet_flags,member104=3,member_kind='regular'):
    """A local native-branch abstraction, NOT a demonstration of one live Shift instance.

    Output `transitively_cleans_delayed` describes ONLY the verified +0xE8
    branch, in the known member type, under the receiver's sixth-argument=1.
    """
    if member_kind not in ('regular','special'):raise ValueError('INVALID_MEMBER_KIND')
    is_immediate=bool(helper(mode) or packet_flags&0x20)
    if not is_immediate:
        return dict(path='deferred',member_method=None,transitively_cleans_delayed=False,
                    note='DEFERRED_REPLACES_PRIOR_DEFERRED_VIA_RECEIVER')
    method='+0x100' if member104 in (1,2) else '+0xE8'
    # special +0xE8 forwards the sixth parameter to the shared regular method.
    direct_cleanup=method=='+0xE8' and 6<=mode<=9
    return dict(path='immediate',member_method=method,
                transitively_cleans_delayed=direct_cleanup,
                note=('TYPED_TRANSITIVE_CLEANUP' if direct_cleanup else
                      'CLEANUP_NOT_PROVEN_BY_THIS_DIRECT_CHAIN'))

def direct_e8_inventory(p:PE,target:int):
    sec=next(x for x in p.sections if x[0]=='.udata')
    _,va,vs,rs,ro=sec
    raw=p.mm;at=ro;possible=[]
    while True:
        idx=raw.find(b'\xe8',at,ro+rs-5)
        if idx<0:break
        at=idx+1
        site=va+idx-ro
        if site+5+struct.unpack_from('<i',raw,idx+1)[0]==target:possible.append(site)
    starts={};verified=[]
    for site in possible:
        owner=p.owner(site)
        if owner is None:continue
        key=owner[:2]
        if key not in starts:starts[key]={a for a,b,ins in p.asm(site) if b[:1]==b'\xe8' and ins.startswith('call')}
        if site in starts[key]:verified.append(site)
    return sorted(verified)

def static_audit(exe):
    exe=Path(exe)
    with exe.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=SHA256:raise ValueError('EXE_SHA_MISMATCH')
    p=PE(exe)
    try:
        if p.imagebase!=IMAGEBASE:raise ValueError('PE_IMAGEBASE_DRIFT')
        pins=read_pins();owners={}
        for at,b in pins.items():
            if p.read(at,len(b))!=b:raise ValueError('BYTES_CHANGED_'+h(at))
            own=p.owner(at)
            if own:span=own[:2]
            else:
                spans=[x for x in LEAF_SPANS if x[0]<=at<x[1]]
                if len(spans)!=1:raise ValueError('UNTYPED_FUNCTION_'+h(at))
                span=spans[0]
            if span not in owners:
                owners[span]={a:(bb,ins) for a,bb,ins in p.asm(at,span=span)}
            if at not in owners[span] or owners[span][at][0]!=b:
                raise ValueError('MID_INSTRUCTION_'+h(at))
        for at,target in E8.items():
            if at not in pins:raise ValueError('E8_NOT_PINNED_'+h(at))
            b=pins[at]
            if len(b)!=5 or b[0]!=0xe8 or at+5+struct.unpack_from('<i',b,1)[0]!=target:
                raise ValueError('CALL_TARGET_DRIFT_'+h(at))
        for at,target in JUMPS.items():
            if branch_target(at,pins[at])!=target:raise ValueError('BRANCH_DRIFT_'+h(at))
        for label,(vt,slots) in MEMBER_TABLES.items():
            for off,fn in slots.items():
                got=struct.unpack('<Q',p.read(vt+off,8))[0]
                if got!=IMAGEBASE+fn:raise ValueError('MEMBER_VTABLE_DRIFT_'+label+hex(off))
        # Same exact mode helper both in member receiver and Group route selection.
        helper_raw=p.read(0x02DC7E30,0x18)
        if helper_raw.hex()!='8b412883f805770db9290000000fa3c17303b001c332c0c3':
            raise ValueError('MODE_HELPER_LEAF_CHANGED')
        # x64 volatile RDX: on THIS helper's exact leaf path RDX is not modified.
        help_asm=[ins for at,(raw,ins) in owners[LEAF_SPANS[0]].items()]
        if any(re.search(r'^(?:mov|lea|add|sub|xor|and|or|pop|shl|shr)\s+(?:rdx|edx|dx|dl)\b',s) or
               re.match(r'^call\s+',s) for s in help_asm):raise ValueError('HELPER_RDX_NOT_PRESERVED')
        # Constant construction of bit0x20 from B2 routine, not a global packet contract.
        exact={
          0x02F64926:'24 01',0x02F64931:'80 e1 01',
          0x02F6493A:'c0 e1 04',0x02F64948:'80 c9 06',
          0x02F64966:'41 88 4a 50',
        }
        for at,bytestr in exact.items():
            if p.read(at,len(bytes.fromhex(bytestr)))!=bytes.fromhex(bytestr):
                raise ValueError('B2_PACKET_FLAGS_DRIFT_'+h(at))
        if pins[0x03070B74]!=bytes.fromhex('c644242801') or pins[0x0307827C]!=bytes.fromhex('807c246800'):
            raise ValueError('STACK_SIXTH_ARGUMENT_DRIFT')
        if p.read(0x0307AE94,7)!=bytes.fromhex('4881c190040000'):
            raise ValueError('CLEANER_WRONG_OBJECT')
        member_cleanup=direct_e8_inventory(p,0x02DB5AC4)
        wrapper_callers=direct_e8_inventory(p,0x0307AE84)
        # Scope of these findings must never silently broaden to all native paths.
        if 0x03070A94 not in member_cleanup or 0x0307AE9B not in member_cleanup:
            raise ValueError('DEFERRED_CLEAR_SET_MISSING')
        if wrapper_callers != [0x030782B0,0x03078985]:
            raise ValueError('TYPE_CLEANER_CALLER_SET_CHANGED')
        b2_calls=direct_e8_inventory(p,0x0326A994)
        return dict(schema='bsc.r61.same_build_mode_deferred_cleanup.v1',
            exe_sha256=actual, PE_imagebase=h(p.imagebase),
            fixed_machine_code_pins=len(pins), verified_e8=len(E8), verified_branches=len(JUMPS),
            typed_member_vtable_slots=sum(len(x[1]) for x in MEMBER_TABLES.values()),
            mode_helper=h(0x02DC7E30),mode_helper_returns_true_for=[m for m in range(12) if helper(m)],
            mode_helper_preserves_rdx_by_whole_leaf_inspection=True,
            receiver_mode_helper_call=h(0x03070A7B),
            group_route_mode_helper_call=h(0x0327ECC6),
            modes_with_transitive_immediate_e8_cleanup=[6,7,8,9],
            transitive_cleanup_direct_edges=[{'site':h(k),'target':h(v)} for k,v in E8.items()
                if k in (0x030782B0,0x03078985,0x0307AE9B,0x0307AEA7)],
            delayed_cleanup_direct_callers_in_udata=len(member_cleanup),
            delayed_cleanup_direct_callers_contains=['0x03070A94','0x0307AE9B'],
            typed_cleanup_wrapper_all_direct_callers=[h(i) for i in wrapper_callers],
            b2_member_sender_direct_callers=[h(i) for i in b2_calls],
            packet_B2_constructor_bit20_must_be_zero=True,
            B2_two_packets_with_stable_mode_cannot_split_deferred_immediate_in_same_receiver=True,
            immediate_path_may_cancel_deferred_through_virtual_method=True,
            all_immediate_paths_cancel_deferred_proven=False,
            group_mode_is_stable_during_actual_Shift_proven=False,
            player_input_to_group_mode_identity_proven=False,
            queued_Shift_crowding_causality_proven=False,gameplay_patch_authorized=False)
    finally:p.close()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',required=True,type=Path);ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    if args.out and args.out.resolve()==args.exe.resolve():ap.error('CANNOT_OVERWRITE_EXE')
    d=static_audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
    print('PASS',d['fixed_machine_code_pins'],'pins',d['verified_e8'],'E8',d['typed_member_vtable_slots'],'slots NO PATCH')
if __name__=='__main__':main()
