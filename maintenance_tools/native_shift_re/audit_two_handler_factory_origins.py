#!/usr/bin/env python3
"""Exact-build static proof of two native handler factories and member-task forks.

Previously unknown slot 0x03915930 is +0x100 on the installed 0x03915830
vtable. Its sibling factory installs 0x039156F8 whose +0x100 callback uses
member+0x348. Neither can be labelled RMB or Shift from static type alone.

Only reads the original game EXE; refuses other SHA. No native patch.
"""
import argparse, json, re, shutil, struct
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

PINS = {
 0x0326F07C:'4053', 0x0326F09B:'b960000000',
 0x0326F0A0:'4c8b4b60', 0x0326F0A4:'e8135be5ff',
 0x0326F0B9:'e8ca5cffff', 0x0326F0BE:'488d156b676a00',
 0x0326F0C5:'4c894958', 0x0326F0C9:'488911',
 0x0326F0DC:'4053', 0x0326F0FB:'b968000000',
 0x0326F100:'4c8b4b68', 0x0326F104:'4c8b5350',
 0x0326F108:'e8af5ae5ff', 0x0326F11D:'e8665cffff',
 0x0326F122:'488d15cf656a00', 0x0326F129:'488911',
 0x0326F12C:'4c894958', 0x0326F130:'4c895160',
 0x0327BCF8:'4881ec88000000',
 0x0327BCFF:'4c8b4158', 0x0327BD0B:'e8b47bfeff',
 0x0327BD29:'ff9048030000',
 0x0327BD38:'48895c2410', 0x0327BD58:'488b4958',
 0x0327BD5F:'ff5060', 0x0327BD68:'0f84e4000000',
 0x0327BE4B:'e820fbdeff', 0x0327BE59:'ff5070',
 0x0327BE86:'e8c1f6deff',
 0x03264D88:'488d0519036a00',0x030C4BBC:'4883ec18',
 0x0327711C:'488d05e52aaa00',
 0x03277123:'48394138',
 0x03277129:'488d05e02aaa00',
 0x03277130:'48394138',
 0x0327714C:'488b4138',
 0x03277168:'488d0d1929aa00',
 0x03277214:'488b4138',
 0x03277224:'488d0d5d28aa00',
}
EDGES={
 0x0326F092:0x0327C6B0,
 0x0326F0A4:0x030C4BBC,0x0326F0B9:0x03264D88,
 0x0326F0F2:0x0327C6B0,
 0x0326F108:0x030C4BBC,0x0326F11D:0x03264D88,
 0x0327BD0B:0x032638C4,
 0x0327BE4B:0x0306B970,0x0327BE86:0x0306B54C
}
TABLE={
 0x039156F8:0x03268840,   # variant one, vtable start
 0x039157F8:0x0327BCF8,   # variant one's vtable+0x100
 0x03915830:0x032688A0,   # variant two, vtable start
 0x03915930:0x0327BD38,   # variant two's vtable+0x100
 0x03941408:0x0326F07C,   # callback on an upstream factory descriptor
 0x03940EE0:0x0326F0DC,   # parallel upstream factory descriptor
 0x03940ED8:0x0326FFF4,   # first callback class entry
 0x03941400:0x0326FF60,   # second callback class entry
 0x03940F00:0x03270098,   # first callback class +0x28
 0x03941428:0x03270C68,   # second callback class +0x28
 0x03D19A88:0x03940ED8,  # static callback registry points to first class
 0x03D19C10:0x03941400,  # registry points to second class
}
LEA_VTABLE={
 0x0326F0BE:0x03915830,
 0x0326F122:0x039156F8,
}
LEAF_BOUNDS={
 0x03264D88:(0x03264D88,0x03264E1D),
}
PRESERVE_REGS=('r9','r10')

def opcode_boundaries(pe):
 if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
 cache={}
 for at,code in PINS.items():
  if pe.read(at,len(code)//2,True).hex()!=code:
   raise ValueError('OPCODE_CHANGED:'+hex(at))
  owner=pe.function(at) or LEAF_BOUNDS.get(at)
  if owner is None:raise ValueError('UNWIND_OR_LEAF_NOT_PINNED:'+hex(at))
  if owner not in cache:
   asm=pe.disasm(owner[0],owner[1]-owner[0])
   cache[owner]={int(m.group(1),16) for line in asm.splitlines()
     if (m:=re.match(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+',line))}
  if at not in cache[owner]:raise ValueError('MID_INSTRUCTION:'+hex(at))
 return len(PINS)

def no_callee_register_writes(pe):
 """These two exact non-recursive leaf bodies have no R9/R10 tokens.

 Conservatively check no calls and no reads/writes of R9/R10.  Because
 x64 calls *usually* clobber those registers, this check is indispensable
 before propagating parent's +0x60/+0x68 source into constructed +0x58.
 """
 for a,b in ((0x030C4BBC,0x030C4C32),(0x03264D88,0x03264E1D)):
  asm=pe.disasm(a,b-a).lower()
  if re.search(r'\bcall\b',asm):raise ValueError('LEAF_GAINED_CALL:'+hex(a))
  if re.search(r'\br(?:9|10)(?:d|w|b)?\b',asm):
   raise ValueError('SOURCE_REGISTER_CLOBBER_OR_ACCESS:'+hex(a))
 return 2

def audit(exe):
 pe=StrictPE(Path(exe))
 try:
  pins=opcode_boundaries(pe)
  for at,dest in EDGES.items():
   insn=pe.read(at,5,True)
   if insn[0]!=0xe8 or at+5+struct.unpack_from('<i',insn,1)[0]!=dest:
    raise ValueError('E8_EDGE_CHANGED:'+hex(at))
  for at,dest in TABLE.items():
   va=struct.unpack('<Q',pe.read(at,8))[0]
   if va!=pe.base+dest:raise ValueError('NATIVE_TABLE_CHANGED:'+hex(at))
  for at,dest in LEA_VTABLE.items():
   insn=pe.read(at,7,True)
   if at+7+struct.unpack_from('<i',insn,3)[0]!=dest:
    raise ValueError('RIP_REL_VTABLE_CHANGED:'+hex(at))
  leaves=no_callee_register_writes(pe)
  return {
   'schema':'bsc.n1.two_native_handler_factories_member_timer_selection.v1',
   'exe_sha256':pe.sha,'grade':'EXACT_ORIGINAL_EXE_STATIC',
   'exact_code_guard_and_disasm_sites':pins,
   'exact_E8_calls':len(EDGES),'typed_pointer_table_entries':len(TABLE),
   'RIP_relative_vtable_installs':len(LEA_VTABLE),
   'source_register_preserving_called_leaf_bodies':leaves,
   'upstream_static_callback_registry':{
      '0x03D19A88':'0x03940ED8 (callback +0x08 is 0x0326F0DC)',
      '0x03D19C10':'0x03941400 (callback +0x08 is 0x0326F07C)'},
   'keyboard_or_queued_order_selector_for_registry_entries':None,
   'native_runtime_type_predicates':{
     'B_family':'0x0327711C checks [object+0x38] == 0x03D19C08 or 0x03D19C10',
     'A_family':'0x0327714C and 0x03277214 check [object+0x38] against a small set including 0x03D19A88'},
   'type_predicate_to_MOVE_queue_order_link_proven':False,
   'variant_one':{
     'factory_callback':'0x0326F0DC','callback_descriptor_slot':'0x03940EE0',
     'alloc_bytes':0x68,'installed_vtable':'0x039156F8',
     'parent_plus_68_to_object_plus_58':True,
     'parent_plus_50_to_object_plus_60':True,
     'vtable_plus_100_method':'0x0327BCF8',
     'downstream':'build descriptor 0x032638C4, dispatch member virtual+0x348'},
   'variant_two':{
     'factory_callback':'0x0326F07C','callback_descriptor_slot':'0x03941408',
     'alloc_bytes':0x60,'installed_vtable':'0x03915830',
     'parent_plus_60_to_object_plus_58':True,
     'vtable_plus_100_method':'0x0327BD38',
     'downstream':'group source virtual+0x60/+0x70 -> typed +0x4C0/+0x4B8 task selection'},
   'prior_unknown_method_slot_resolved':
     '0x03915930 == installed 0x03915830 + 0x100',
   'both_paths_from_same_upstream_factory_descriptor_class_proven':False,
   'MOVE_queue_slot_to_variant_task_instance_proven':False,
   'RMB_v_Shift_player_input_identity_proven':False,
   'crowding_causal_repair_proven':False,'native_patch_authorized':False,
  }
 finally:pe.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--exe',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True)
 a=ap.parse_args()
 if a.out.resolve()==a.exe.resolve():ap.error('NEVER_OVERWRITE_EXE')
 report=audit(a.exe)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('PASS',report['exact_code_guard_and_disasm_sites'],'opcodes',
       report['exact_E8_calls'],'edges',report['typed_pointer_table_entries'],
       'table entries; NOT A PATCH')
if __name__=='__main__':main()
