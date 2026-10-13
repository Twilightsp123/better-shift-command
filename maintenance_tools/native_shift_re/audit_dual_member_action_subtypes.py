#!/usr/bin/env python3
"""Exact WH3 typed actor action subtypes: SAME member+0x330 slot, two vmethods.

+0x580 installs a subtype whose +8 tick has a native motor-goal path.
+0x5B8 installs a DIFFERENT subtype from the geometry fanout.
It is NOT proven that RMB/Shift selects these subtypes, nor that either
subtype is a cause of soldier crowding. No code or memory patching.
"""
import argparse, json, struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

PINS={
 0x0306A99A:'488d9928030000',0x0306A9AC:'488d4b08',
 0x0306A9BB:'e890e91d00',
 0x0306A8CA:'488d9928030000',0x0306A8DC:'488d4b08',
 0x0306A8EB:'e8d8e51d00',
 0x0324935C:'488d15a5a46c00',0x03248EE4:'488d051d1b8900',
 0x032599C8:'48895c2410',0x03259950:'4881c1c0000000',
 0x03259957:'e93c335cfe',0x03259C55:'e8c252e1ff',
 0x0306EF96:'e9b1a50a00',0x0311963A:'0f1187e0010000',
 0x02F79C3D:'ff9080050000',0x02F79D6E:'ff9080050000',
 0x02F7A116:'ff9080050000',
 0x03117EF7:'ff90b8050000',0x03118040:'41ff90b8050000',
}
CONTROL={
 0x0306A9BB:('E8',0x03249350),
 0x0306A8EB:('E8',0x03248EC8),
 0x03259C55:('E8',0x0306EF1C),
 0x0306EF96:('E9',0x0311954C),
 0x03259957:('E9',0x0181CC98),
}
VTABLES={
 0x038FDBD8:0x0306A990,0x038FDC10:0x0306A8C0,
 0x03910A80:0x0306A990,0x03910AB8:0x0306A8C0,
  0x03913810:0x032599C8,0x03ADAA10:0x03259950,
}
VTABLE_LEA={0x0324935C:0x03913808,0x03248EE4:0x03ADAA08}

def audit(exe):
    pe=StrictPE(Path(exe))
    try:
        for a,hx in PINS.items():
            if pe.read(a,len(hx)//2,True).hex()!=hx:
                raise ValueError('CODE_GUARD_DRIFT:'+hex(a))
        for a,(opcode,target) in CONTROL.items():
            bits=pe.read(a,5,True)
            actual=a+5+struct.unpack_from('<i',bits,1)[0]
            if bits[0]!=int(opcode,16) or actual!=target:
                raise ValueError('CALL_OR_JUMP_DRIFT:'+hex(a))
        for a,target in VTABLES.items():
            observed=struct.unpack('<Q',pe.read(a,8))[0]
            if observed!=pe.base+target:
                raise ValueError('TYPED_VTABLE_DRIFT:'+hex(a))
        for a,target in VTABLE_LEA.items():
            instruction=pe.read(a,7,True)
            actual=a+7+struct.unpack_from('<i',instruction,3)[0]
            if actual!=target:raise ValueError('VTABLE_LEA_DRIFT:'+hex(a))
        return {
          'schema':'bsc.n1.typed_dual_member_action_branch.v1',
          'exe_sha256':pe.sha,
          'original_opcode_guards':len(PINS),
          'exact_direct_call_or_jump_edges':len(CONTROL),
          'typed_vtable_slots':len(VTABLES),
          'rip_relative_vtable_installs':len(VTABLE_LEA),
          'same_member_action_storage':'member+0x328+8 = member+0x330',
          'typed_member_interfaces':{
             '+0x580':'0x0306A990 -> 0x03249350 -> vtable 0x03913808',
             '+0x5B8':'0x0306A8C0 -> 0x03248EC8 -> vtable 0x03ADAA08'},
          'subclass_tick_plus_8':{
             '0x03913808':'0x032599C8',
             '0x03ADAA08':'0x03259950'},
          'motor_path_proven_from_plus_580_subclass':
             '0x032599C8 -> 0x0306EF1C -> 0x0311954C -> 0x0311963A',
          'plus_5b8_fanout':
             '0x03117E8C -> 0x03117EF7',
          'independent_other_native_plus_580_callsites':[
             '0x02F79C3D','0x02F79D6E','0x02F7A116'],
          'same_subclass_for_both_interfaces':False,
          'which_subclass_user_RMB_or_Shift_chooses_proven':False,
          'single_concrete_stage1_nextSubtask_instance_traced_to_actions':False,
          'crowding_cause_proven':False,
          'native_patch_authorized':False,
        }
    finally:pe.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.resolve()==a.exe.resolve():p.error('REFUSE_OVERWRITE_EXE')
    r=audit(a.exe)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('EXACT',r['original_opcode_guards'],'opcodes',
      r['exact_direct_call_or_jump_edges'],'edges',
      r['typed_vtable_slots'],'vtable slots')
if __name__=='__main__':main()
