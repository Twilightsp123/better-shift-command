#!/usr/bin/env python3
"""WH3 original EXE: bigTask release -> two typed ordinary-B packet paths.

Strict SHA, PE section/unwind, decoded starts, E8/JCC/vtable guards.
Read-only evidence, no gameplay patch or actual keyboard-instance claim.
"""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA,IMAGEBASE
PINS=Path(__file__).with_name('b_ordinary_identity_pins_20261015.txt')
LEAVES=((0x02F50FE4,0x02F5101F),(0x03263F64,0x03263FCA))
E8={
 0x02F4F52B:0x02F50FE4,0x02F4F554:0x02D4BE38,
 0x02F4F5DE:0x031219B0,0x02F4F617:0x03263F64,
 0x02F4F62C:0x03279EE8,0x03279F71:0x03263EC4,
 0x03263ED0:0x030C35A0,0x03271B8E:0x03265B24,
 0x03271BE9:0x030ECA50,0x03271C04:0x031219B0,
 0x032815C5:0x03265B24,
}
JCC={0x02F4F538:0x02F4F590,0x03279F16:0x03279F4F,
     0x03271B2B:0x03271BA8,0x03281537:0x032815DE}
VTABLE={(0x03AE00E8,0x08):0x03271B0C,(0x03AE00E8,0x10):0x03281520}

def inventory():
    out={}
    for line in PINS.read_text('utf8').splitlines():
        parts=line.strip().split()
        if not parts:continue
        if len(parts)!=2:raise ValueError('INVALID_PIN_FORMAT')
        addr=int(parts[0],16)
        if addr in out:raise ValueError('DUPLICATE_PIN:'+hex(addr))
        out[addr]=bytes.fromhex(parts[1])
    if len(out)!=72:raise ValueError('PIN_COUNT_DRIFT')
    return out

def ordinary_b_schedule(route_present,node_ready,already_handled=False):
    """Only the guarded +0x08/+0x10 methods; not a full engine tick model."""
    if already_handled:return ('skip','skip')
    if route_present:return ('direct_packet_set_done','skip')
    if node_ready:return ('build_node','node_packet_set_done')
    return ('build_node','defer_no_valid_node')

def audit(path):
    original=OriginalEXE(path)
    try:
        pin=inventory()
        starts={}
        for addr,b in pin.items():
            if original.section(addr)!='.00cfg' or original.read(addr,len(b))!=b:
                raise ValueError('INSTRUCTION_DRIFT:'+hex(addr))
            owner=original.owner(addr)
            bounds=owner[:2] if owner else next(
                (s for s in LEAVES if s[0]<=addr<s[1]),None)
            if bounds is None:raise ValueError('UNWIND_OR_LEAF_OWNER_MISSING:'+hex(addr))
            if bounds not in starts:starts[bounds]=original.starts_in(*bounds)
            if addr not in starts[bounds]:raise ValueError('MID_INSTRUCTION:'+hex(addr))
        for addr,target in E8.items():
            data=original.read(addr,5)
            if data[0]!=0xe8 or addr+5+struct.unpack_from('<i',data,1)[0]!=target:
                raise ValueError('E8_DRIFT:'+hex(addr))
        for addr,target in JCC.items():
            data=original.read(addr,6)
            if data[0]==0x0f and 0x80<=data[1]<=0x8f:
                actual=addr+6+struct.unpack_from('<i',data,2)[0]
            elif 0x70<=data[0]<=0x7f:
                actual=addr+2+struct.unpack_from('<b',data,1)[0]
            else:raise ValueError('BAD_JCC:'+hex(addr))
            if actual!=target:raise ValueError('JCC_DRIFT:'+hex(addr))
        for (table,slot),target in VTABLE.items():
            actual=struct.unpack('<Q',original.read(table+slot,8))[0]
            if actual!=IMAGEBASE+target:raise ValueError('B_VTABLE_TYPE_DRIFT')
        lea=original.read(0x03263ED5,7)
        if lea[:3]!=bytes.fromhex('488d15') or \
            0x03263ED5+7+struct.unpack_from('<i',lea,3)[0]!=0x03AE00E8:
            raise ValueError('CONSTRUCTOR_VTABLE_DRIFT')
        if original.owner(0x03263F64) or original.owner(0x02F50FE4):
            raise ValueError('LEAF_BOUNDARY_DRIFT')
        for ret in (0x03263FC9,0x02F51006,0x02F5101E):
            if original.read(ret,1)!=b'\xc3':
                raise ValueError('LEAF_RET_DRIFT:'+hex(ret))
        return {'schema':'bsc.n1.ordinary_b_release_to_packet_two_path.v1',
          'sha256':original.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
          'opcode_starts':len(pin),'E8_edges':len(E8),
          'JCC_targets':len(JCC),'typed_B_vtable_slots':len(VTABLE),
          'release_before_B_build':True,
          'route_identity':'node+0x70 -> descriptor+0x28 -> aux+0x60',
          'constructor_aux_plus78_null':True,'constructor_aux_plus80_zero':True,
          'virtual_plus08_direct_route_sends_packet_and_sets_plus80_one':True,
          'virtual_plus10_skips_if_plus80_nonzero':True,
          'virtual_plus08_null_route_builds_aux_plus78_node':True,
          'virtual_plus10_may_send_node_plus70_if_valid':True,
          'no_double_send_through_both_methods_on_direct_route':True,
          'same_Shift_instance_observed':False,
          'member_motor_goal_error_proven':False,
          'native_patch_authorized':False}
    finally:original.close()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    if args.out and args.out.resolve()==args.exe.resolve():
        ap.error('CANNOT_OVERWRITE_EXE')
    r=audit(args.exe)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('EXACT_STATIC_PASS',r['opcode_starts'],'opcode',r['E8_edges'],'E8',
          r['JCC_targets'],'JCC',r['typed_B_vtable_slots'],'vtables; NO PATCH')
if __name__=='__main__':main()
