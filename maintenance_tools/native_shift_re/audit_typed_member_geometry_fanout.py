#!/usr/bin/env python3
"""Read-only exact-WH3 member geometry fanout: input->packed record->typed member.
Does not identify a particular RMB/Shift order or authorize a patch.
For the comprehensive original-EXE 49-site offline auditor, see the local
evidence delivery audit_endpoint_dispatch.py (no EXE is shipped to GitHub).
"""
import argparse,json,struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE
PINS={
0x0311EBC8:'e87f6ffeff',
0x03117D44:'48895c2408',0x03117D5A:'ff9060020000',
0x03117D73:'f30f104754',0x03117D7B:'f30f104f4c',
0x03117D84:'f30f105f48',0x03117DB4:'f30f104750',
0x03117DEB:'e84c1a1300',0x03117E00:'e887000000',
0x03117E8C:'48895c2410',0x03117EA1:'488bb9680b0000',
0x03117EAB:'8b81640b0000',0x03117EF7:'ff90b8050000',
0x03118040:'41ff90b8050000',0x03118047:'4883c708',
0x0324983C:'418b00',0x032498A4:'f30f11414c',
0x032498AF:'f30f115948',0x032498B4:'f30f114950',
0x032498B9:'f30f114160',
0x0306A8C0:'48895c2408',0x0306A8CA:'488d9928030000',
0x0306A8EB:'e8d8e51d00',
0x03248ED5:'e836060000',0x03249530:'e86f53d1ff',
0x02F5E8F2:'8b4248',0x02F5E8F8:'8b424c',
0x02F5E8FE:'8b4250',0x02F5E918:'8b4260',
}
EDGES={
0x0311EBC8:0x03105B4C,0x03117DEB:0x0324983C,
0x03117E00:0x03117E8C,0x0306A8EB:0x03248EC8,
0x03248ED5:0x03249510,0x03249530:0x02F5E8A4
}
SLOTS={
0x0390FE38:0x03117D44,
0x038FD9C0:0x0306B9F0,0x038FDC10:0x0306A8C0,
0x03910868:0x0306B9F0,0x03910AB8:0x0306A8C0
}
def audit(exe):
 pe=StrictPE(Path(exe))
 try:
  for at,hx in PINS.items():
   if pe.read(at,len(hx)//2,True).hex()!=hx:
    raise ValueError('ORIGINAL_OPCODE_CHANGED:'+hex(at))
  for at,target in EDGES.items():
   raw=pe.read(at,5,True)
   if raw[0]!=0xe8 or at+5+struct.unpack_from('<i',raw,1)[0]!=target:
    raise ValueError('E8_EDGE_CHANGED:'+hex(at))
  for slot,target in SLOTS.items():
   if struct.unpack('<Q',pe.read(slot,8))[0]!=pe.base+target:
    raise ValueError('TYPED_VTABLE_CHANGED:'+hex(slot))
  return dict(schema='bsc.n1.typed_member_geometry_dispatch.v1',
   exe_sha256=pe.sha,static_opcode_guards=len(PINS),
   direct_e8_edges=len(EDGES),typed_vtable_slots=len(SLOTS),
   geometry_reader='0x03117D44',
   packer='0x0324983C',
   per_object_fanout='0x03117E8C',
   array_count_field='+0xB64',array_pointer_field='+0xB68',
   conditional_member_method='+0x5B8',
   same_member_virtual_receiver='+0x368 -> 0x0306B9F0',
   same_member_geometry_dispatch='+0x5B8 -> 0x0306A8C0',
   member_action_destination='member+0x330 action, +0x38 nested packed geometry',
   member_action_ctor='0x03248EC8 -> 0x03249510 -> 0x02F5E8A4',
   input_endpoints_to_record={'+0x48':'+0x48','+0x4C':'+0x4C',
                              '+0x50':'+0x50','+0x54':'+0x60'},
   note='Inputs are repacked, not a naive memcpy of four consecutive fields.',
   source_task_instance_proven=False,
   soldier_model_element_count_proven=False,
   queued_shift_execution_proven=False,crowding_causality_proven=False,
   native_patch_authorized=False)
 finally:pe.close()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.exe.resolve()==a.out.resolve():p.error('REFUSE_OVERWRITE_GAME_EXE')
 result=audit(a.exe);a.out.write_text(json.dumps(result,indent=2)+'\n')
 print('EXACT_STATIC',result['static_opcode_guards'],'sites',
       result['direct_e8_edges'],'E8 calls',result['typed_vtable_slots'],'vtable slots')
if __name__=='__main__':main()
