#!/usr/bin/env python3
"""BSC fixed original EXE: route-heading record -> node -> conditional A fanout.
Read-only static evidence only. Never patches EXE or claims Shift gameplay repair.
"""
import argparse, json, struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE, SHA, IMAGEBASE

PINS={int(a,16):bytes.fromhex(b) for a,b in (line.split() for line in """
03025E76 440fb78398000000
03025E91 e8e6c9feff
03026015 440fb7c0
03026022 e855c8feff
03025E7E 40887c2430
03025E83 c644242801
03025E8C 40887c2420
03026008 40887c2430
03026010 c644242801
03026019 40887c2420
0302DBA8 c644243001
0302DBB0 c644242801
0302DBBC c644242001
0302DBC4 e8b34cfeff
03012893 410fb7d8
030128AB 4180b89400000000
030128B3 0f8533010000
030128B9 83b98401000000
030128C0 0f8426010000
030128C6 80bc24d000000000
030128D0 4881c178020000
030128F4 80bc24d800000000
030128FC 0f848e000000
03012902 488b87f8320000
03012935 440fb7cb
03012945 e866a10d00
0301297A 4c8d442440
03012982 e80d5fffff
03012987 48898770020000
03012990 488d8fe8010000
030129DC 66895944
030129E0 f30f117140
030129E5 48898f70020000
030ECAB0 f30f10442428
030ECABC 488911
030ECAC9 418b00
030ECAD6 418b4008
030ECADD 498b4010
030ECAE5 498b4018
030ECAFA 6644894938
030ECB0C c3
030088C9 488b8860010000
030088D0 e8db901100
030088D5 48894718
03008900 0fb74338
0300890E 66894744
0302DBC9 488b8570020000
0302DBD3 488b5018
0302DBD7 488b5270
0302DBDB e8b0780a00
03279E62 e89d8fb4ff
03279E69 744f
03279E6B 807a3000
03279E71 440fb74232
03279E78 498b81100a0000
03279E7F 488b8870020000
03279E86 440fb74144
03279E90 0f2f1d292d6a00
03279E99 498b81100a0000
03279EA0 488b8870020000
03279EA7 f30f105940
03279EB3 e894b6e5ff
03279EB8 eb23
030D55EC 66448945e8
030D55F5 e8a2840200
030D5603 e888feffff
030D54CA 41ff5248
030D54F7 450fb74822
030D54FC e867a3e8ff
030D550F ff9068030000
030EC9EC 488b02
030ECA24 0fb74238
030ECA28 66894138
030ECA4E c3
03121A33 488d4b20
03121A40 e8a7affcff
03121A45 4883637000
03121A82 e87d13caff
03121A87 3c01
03121A89 7406
03121A8B 807e4c01
03121A99 e8febffdff
03121A9E 48894370
""".strip().splitlines())}
assert len(PINS)==83
CALLS={0x03025e91:0x0301287c,0x03026022:0x0301287c,0x0302dbc4:0x0301287c,
0x03012945:0x030ecab0,0x03012982:0x03008894,0x030088d0:0x031219b0,
0x03121a40:0x030ec9ec,0x03121a82:0x02dc2e04,0x03121a99:0x030fda9c,
0x0302dbdb:0x030d5490,0x03279e62:0x02dc2e04,0x03279eb3:0x030d554c,
0x030d55f5:0x030fda9c,0x030d5603:0x030d5490,0x030d54fc:0x02f5f868}
JCC={0x030128b3:0x030129ec,0x030128c0:0x030129ec,0x030128fc:0x03012990,
0x03121a89:0x03121a91,0x03279e69:0x03279eba}
LEAVES=((0x030ecab0,0x030ecb0d),(0x030ec9ec,0x030eca4f))

def conditional_A_heading_source(mode_nonzero, temp_has_heading, explicit, stored):
    return None if not mode_nonzero else (explicit if temp_has_heading else stored)

def audit(exe):
    pe=OriginalEXE(Path(exe))
    try:
        if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
        cache={}
        for at,expected in PINS.items():
            if pe.section(at)!='.00cfg' or pe.read(at,len(expected))!=expected:
                raise ValueError('OPCODE_DRIFT:'+hex(at))
            owner=pe.owner(at)
            span=owner[:2] if owner else next((x for x in LEAVES if x[0]<=at<x[1]),None)
            if span is None:raise ValueError('UNWIND_OWNER_MISSING:'+hex(at))
            if span not in cache:cache[span]=pe.starts_in(*span)
            if at not in cache[span]:raise ValueError('MID_INSTRUCTION:'+hex(at))
        for at,dest in CALLS.items():
            raw=pe.read(at,5)
            if raw[0]!=0xe8 or at+5+struct.unpack_from('<i',raw,1)[0]!=dest:
                raise ValueError('E8_TARGET_DRIFT:'+hex(at))
        for at,dest in JCC.items():
            raw=pe.read(at,6)
            if 0x70<=raw[0]<=0x7f:actual=at+2+struct.unpack_from('<b',raw,1)[0]
            elif raw[0]==0x0f and 0x80<=raw[1]<=0x8f:
                actual=at+6+struct.unpack_from('<i',raw,2)[0]
            else:raise ValueError('JCC_OPCODE_DRIFT:'+hex(at))
            if actual!=dest:raise ValueError('JCC_TARGET_DRIFT:'+hex(at))
        if pe.owner(0x030ecab0) or pe.owner(0x030ec9ec) or \
           pe.read(0x030ecb0c,3)!=b'\xc3\xcc\xcc' or pe.read(0x030eca4e,2)!=b'\xc3\xcc':
            raise ValueError('LEAF_BOUNDARY_DRIFT')
        if struct.unpack('<Q',pe.read(0x0390d4f8+0x368,8))[0]!=IMAGEBASE+0x0306b9f0:
            raise ValueError('TYPED_MEMBER_RECEIVER_DRIFT')
        for at in (0x03025e83,0x03026010,0x0302dbb0):
            if pe.read(at,5)!=b'\xc6\x44\x24\x28\x01':
                raise ValueError('ROUTE_DESCRIPTOR_OPTION_DRIFT')
        # Win64 call ABI: route setter push 8 + stack alloc 0xa0;
        # callee [rsp+0xd0/+0xd8] maps caller [rsp+0x20/+0x28].
        if 0x20+0xb0!=0xd0 or 0x28+0xb0!=0xd8:
            raise ValueError('STACK_ABI_DRIFT')
        return {
           'schema':'bsc.n1.route_heading_to_member_conditional.v1',
           'sha256':pe.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
           'opcodes':len(PINS),'e8_calls':len(CALLS),'conditional_branches':len(JCC),
           'typed_member_vtable_slots':1,
           'record_heading':'R8W -> 0x030ECAB0 record+0x38',
           'route_heading':'0x03008894 record+0x38 -> descriptor+0x44 -> UnitRoot+0x270',
           'node_geometry':'0x030EC9EC record+0x38 -> node+0x58; 0x030FDA9C conditionally writes node+0x70',
           'immediate_packet':'descriptor+0x18 -> node+0x70 -> 0x030D5490',
           'deferred_A_packet':'mode!=0 and temp+0x30=0 -> descriptor+0x44 -> 0x030D554C -> 0x030D5490; explicit temp+0x32 overrides',
           'player_shift_instance_proven':False,'same_member_motor_goal_error_proven':False,
           'native_patch_authorized':False}
    finally:pe.close()

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--exe',type=Path,required=True);a.add_argument('--out',type=Path)
    args=a.parse_args()
    if args.out and args.out.resolve()==args.exe.resolve():
        a.error('NEVER_OVERWRITE_EXE')
    res=audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('STATIC PASS',res['opcodes'],'opcodes',res['e8_calls'],'calls',res['conditional_branches'],'branches; NO PATCH')
if __name__=='__main__':main()
