#!/usr/bin/env python3
"""Exact-WH3 read-only lineage: member+0x348 timer -> mode+0x42 -> action.

Original EXE 9.0.3 SHA256 and typed native virtual slots, no game mutation.
Does NOT infer player RMB/Shift identity or crowding cause.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

PINS={
 0x0306b51a:'488d9990040000',0x0306b52c:'488d4b18',0x0306b53b:'e8a83cefff',
 0x02f5f1fd:'488d05847a9a00',0x02f5f207:'488d4f40',
 0x02f5f20b:'488907',0x02f5f20e:'e845ace3ff',
 0x02d99e64:'0fb64202',0x02d99e68:'884102',
 0x032638d7:'c6410200',
 0x032774b0:'e80fc4feff',0x032774c0:'41ff9048030000',
 0x03277b6e:'e851bdfeff',0x03277b80:'41ff9048030000',
 0x0327bd0b:'e8b47bfeff',0x0327bd29:'ff9048030000',
 0x02f73058:'0f2f899c000000',0x02f73061:'e8526b0000',
 0x02f838ad:'0f2f899c000000',0x02f838b6:'e8fd62ffff',
 0x02f79bcd:'385142',0x02f79bd0:'7473',
 0x02f79c3d:'ff9080050000',0x02f79cb6:'ff90b0040000',
 0x02f79d6e:'ff9080050000',0x02f79e5c:'ff90f0050000',
 0x030698b7:'80bbc005000001',0x030698c0:'488d8ba8040000',
 0x030698ca:'ff9080000000',0x03069906:'488dbb28030000',
 0x03069910:'e8fb70d4ff',0x03069924:'e8ab4cfeff',
 0x0304e5e9:'488d0518eca700',0x0304e5f0:'488903',
 0x0307c388:'48895c2408',
 0x0304e6ae:'f30f108a880000',0x0304e6b9:'f30f1082900000',
 0x0304e6c5:'f30f5c88880000',0x0304e6cd:'f30f5c80900000',
 0x0304e6d5:'f30f118be00000',0x0304e6dd:'f30f1183e40000',
 0x0307c3af:'c7807002000001',0x0307c3b9:'e89ec4ffff',
 0x0307c3cb:'80a0110b0000df',0x0307c3e2:'80bbb100000001',
 0x0307c436:'41ff91c8000000',
}
EDGES={
 0x0306b53b:0x02f5f1e8,0x02f5f20e:0x02d99e58,
 0x032774b0:0x032638c4,0x03277b6e:0x032638c4,0x0327bd0b:0x032638c4,
 0x02f73061:0x02f79bb8,0x02f838b6:0x02f79bb8,
 0x03069910:0x02db0a10,0x03069924:0x0304e5d4,
 0x0307c3b9:0x0307885c,
}
VTABLES={
 0x038fd9a0:0x0306b510,0x038fd9c0:0x0306b9f0,
 0x038fdb08:0x03069844,0x038fdbd8:0x0306a990,
 0x038fdc10:0x0306a8c0,0x038fdc48:0x0306b0f8,
 0x03910848:0x0306b510,0x03910868:0x0306b9f0,
 0x039109b0:0x03069844,0x03910a80:0x0306a990,
 0x03910ab8:0x0306a8c0,0x03910af0:0x0306b0f8,
 0x03906c88:0x02f63b38,0x03906c90:0x02f7301c,
 0x03906c98:0x02f83868,
 0x03acd208:0x03052f30,0x03acd210:0x0307c388,
 0x03acd218:0x0308279c,
}
# These two original, bounded x64 leaf functions have no PE unwind entry.
LEAVES={
 0x02d99e64:(0x02d99e58,0x02d99ecb),
 0x02d99e68:(0x02d99e58,0x02d99ecb),
 0x032638d7:(0x032638c4,0x03263927),
}
EXPECTED_SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'

def audit(exe):
    exe=Path(exe)
    with exe.open('rb') as stream:actual_sha=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual_sha!=EXPECTED_SHA:raise ValueError('EXACT_GAME_SHA_MISMATCH')
    pe=StrictPE(exe)
    try:
        boundaries={}
        for at,hexbytes in PINS.items():
            if pe.read(at,len(hexbytes)//2,True).hex()!=hexbytes:
                raise ValueError('OPCODE_GUARD_DRIFT:'+hex(at))
            owner=pe.function(at) or LEAVES.get(at)
            if not owner:raise ValueError('UNVERIFIED_NATIVE_LEAF:'+hex(at))
            if owner not in boundaries:
                asm=pe.disasm(owner[0],owner[1]-owner[0])
                # Whitespace cannot consume the following instruction line.
                boundaries[owner]={int(x,16) for x in re.findall(
                    r'^[ \t]*([0-9a-f]+):[ \t]+[0-9a-f]{2}',asm,re.M)}
            if at not in boundaries[owner]:
                raise ValueError('NOT_NATIVE_INSTRUCTION_START:'+hex(at))
        for at,destination in EDGES.items():
            data=pe.read(at,5,True)
            if data[0]!=0xe8 or at+5+struct.unpack_from('<i',data,1)[0]!=destination:
                raise ValueError('NATIVE_E8_EDGE_CHANGED:'+hex(at))
        for slot,dest in VTABLES.items():
            if struct.unpack('<Q',pe.read(slot,8))[0]!=pe.base+dest:
                raise ValueError('NATIVE_TYPE_SLOT_CHANGED:'+hex(slot))
        lea=pe.read(0x02f5f1fd,7,True)
        if 0x02f5f1fd+7+struct.unpack_from('<i',lea,3)[0]!=0x03906c88:
            raise ValueError('TIMER_VTABLE_INSTALL_CHANGED')
        more=pe.read(0x0304e5e9,7,True)
        if 0x0304e5e9+7+struct.unpack_from('<i',more,3)[0]!=0x03acd208:
            raise ValueError('FALLBACK_ACTION_VTABLE_INSTALL_CHANGED')
        return dict(
            schema='bsc.n1.member_timer_mode_provenance.static.v1',
            exact_original_exe_sha256=actual_sha,
            guarded_x64_instruction_starts=len(PINS),
            verified_E8_edges=len(EDGES),
            typed_vtable_entries=len(VTABLES),
            type_evidence='both member vtables expose +0x348, +0x368, +0x4B0, +0x580, +0x5B8 and +0x5F0',
            native_member_timer_factory='member+0x348 -> 0x0306B510 -> member+0x4A8',
            timer_vtable='0x03906C88',
            timer_callbacks=['0x02F7301C','0x02F83868'],
            mode_origin='descriptor+0x02 copied by 0x02D99E58 to task+0x42',
            three_group_factory_sites_initialize_descriptor_02_zero=True,
            timer_branch='task+0x42 != 0: virtual+0x580; ==0: virtual+0x4B0',
            action_installers_are_at_least_three_typed_subclasses=True,
            action_plus_4b0_constructed_subtype='0x03ACD208 +0x08=0x0307C388',
            fallback_ctor_relative_target_dx_dz='action+0xE0,+0xE4 = target(+0x88,+0x90) minus member(+0x88,+0x90), when target pointer nonnull',
            fallback_action_tick_sets_member_plus270_one=True,
            fallback_action_tick_may_clear_member_plusB11_bit0x20=True,
            fallback_action_tick_conditional_virtual_plus_c8=True,
            action_plus_580_constructed_subtype='0x03913808 +0x08=0x032599C8',
            action_plus_5b8_constructed_subtype='0x03ADAA08 +0x08=0x03259950',

            other_timer_mode='0x02F79CC4 can dispatch +0x580 or +0x5F0',
            timer_condition='scaled group clock compared with task+0x9C',
            actor_4b0_status_gates=['member+0x5C0','member+0x4A8 virtual+0x80','member+0x330 current action'],
            queued_shift_or_RMB_identity_proven=False,
            historic_actor_instance_matched=False,
            native_crowding_fix_authorized=False)
    finally:pe.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    x=p.parse_args()
    if x.exe.resolve()==x.out.resolve():p.error('REFUSE_OVERWRITE_GAME_EXE')
    record=audit(x.exe)
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ORIGINAL_GAME_PASS',record['guarded_x64_instruction_starts'],
          'opcodes',record['verified_E8_edges'],'calls',
          record['typed_vtable_entries'],'typed slots; NO PATCH')
if __name__=='__main__':main()
