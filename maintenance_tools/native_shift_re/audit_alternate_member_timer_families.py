#!/usr/bin/env python3
"""Read-only exact-build audit of native member TIMER families and action subtype forks.

Not an RMB-vs-Shift discriminator: this group-task vtable selects on a virtual
result (+0x60), then fallback virtual result (+0x70), not on keyboard state.
"""
import argparse,json,re,struct,shutil
from pathlib import Path
from audit_wh3_full_native_chain import StrictPE

PINS={
 0x0327bd5f:'ff5060',0x0327bd68:'0f84e4000000',
 0x0327bd6e:'8a8fc0050000',0x0327bd88:'ff92e0000000',
 0x0327be3f:'e8e038ceff',0x0327be4b:'e820fbdeff',
 0x0327be59:'ff5070',0x0327be5f:'742a',0x0327be86:'e8c1f6deff',
 0x0306b54c:'48895c2408',0x0306b568:'e84755d4ff',
 0x0306b581:'488d0568caa500',
 0x0306b970:'48895c2408',0x0306b98c:'e82351d4ff',
 0x0306b9a5:'488d0554c8a500',0x0306b9b6:'e8053defff',
 0x02f73074:'4883ec38',0x02f730a7:'ff90b8040000',
 0x02f73260:'4053',0x02f73292:'ff90c0040000',
 0x02f838e8:'488b4118',0x02f838fb:'c6412001',
 0x03069948:'48895c2408',0x0306998b:'e8ec4dfeff',
 0x0306a7e8:'48895c2408',0x0306a813:'e80445feff',
 0x0304e788:'488d1511eea700',0x0304ed31:'488d0d98e9a700',
 0x03117c5f:'ff9050030000',0x0327bf45:'ff9058030000',
}
CALLS={
 0x0327be3f:0x02f5f724,0x0327be4b:0x0306b970,
 0x0327be86:0x0306b54c,0x0306b568:0x02db0ab4,
 0x0306b98c:0x02db0ab4,0x0306b9b6:0x02f5f6c0,
 0x0306998b:0x0304e77c,0x0306a813:0x0304ed1c,
}
VTABLES={
 0x03915930:0x0327bd38,
 0x03ac7ff8:0x02f73074,0x03ac8000:0x02f838e8,
 0x03ac8208:0x02f73260,0x03ac8210:0x02f838e8,
  0x038fdb10:0x03069948,0x039109b8:0x03069948,
  0x038fdb18:0x02dc39cc,0x039109c0:0x0306a7e8,
  0x038fd9a8:0x03117c1c,0x03910850:0x03117c1c,
  0x038fd9b0:0x0306b6d4,0x03910858:0x0306b6d4,
  0x038fd9a0:0x0306b510,0x03910848:0x0306b510,
  0x03acd5a8:0x0307c464,0x03acd6d8:0x0307cad0,
}
RIP_LEAS={
 0x0306b581:0x03ac7ff0,0x0306b9a5:0x03ac8200,
 0x0304e788:0x03acd5a0,0x0304ed31:0x03acd6d0,
}
LEAF=(0x02f838e8,0x02f83900)

def audit(exe):
 pe=StrictPE(Path(exe))
 try:
  if not shutil.which('objdump'):raise ValueError('OBJDUMP_REQUIRED')
  owners={}
  for site,expected in PINS.items():
   if pe.read(site,len(expected)//2,True).hex()!=expected:
    raise ValueError('ORIGINAL_OPCODE_DRIFT:'+hex(site))
   owner=pe.function(site) or (LEAF if LEAF[0]<=site<LEAF[1] else None)
   if not owner:raise ValueError('UNKNOWN_INSTRUCTION_OWNER:'+hex(site))
   if owner not in owners:
    asm=pe.disasm(owner[0],owner[1]-owner[0])
    owners[owner]={int(x,16) for x in re.findall(
        r'^\s*([0-9a-f]+):\s+[0-9a-f]{2}',asm,re.M)}
   if site not in owners[owner]:raise ValueError('MID_INSTRUCTION:'+hex(site))
  for site,dest in CALLS.items():
   code=pe.read(site,5,True)
   if code[0]!=0xe8 or site+5+struct.unpack_from('<i',code,1)[0]!=dest:
    raise ValueError('E8_TARGET_DRIFT:'+hex(site))
  for slot,dest in VTABLES.items():
   val=struct.unpack('<Q',pe.read(slot,8))[0]
   if val!=pe.base+dest:raise ValueError('VTABLE_TYPE_DRIFT:'+hex(slot))
  for site,dest in RIP_LEAS.items():
   code=pe.read(site,7,True)
   if site+7+struct.unpack_from('<i',code,3)[0]!=dest:
    raise ValueError('LEA_VTABLE_DRIFT:'+hex(site))
  for site,target,length in ((0x0327bd68,0x0327be52,6),
                             (0x0327be5f,0x0327be8b,2)):
   code=pe.read(site,length,True)
   displacement=struct.unpack_from('<i' if length==6 else '<b',code,2 if length==6 else 1)[0]
   if site+length+displacement!=target:
    raise ValueError('GROUP_FORK_BRANCH_DRIFT:'+hex(site))
  return dict(schema='bsc.n1.group_selected_alternate_member_timers.v1',
    exact_exe_sha=pe.sha,
    verified_opcode_boundaries=len(PINS),direct_edges=len(CALLS),
    typed_vtable_slots=len(VTABLES),rip_relative_installs=len(RIP_LEAS),
    group_virtual_source='0x03915900+0x30 -> 0x0327BD38',
    first_path='group +0x60 nonnull -> 0x0306B970 -> 0x03AC8200 (+8 calls actor +0x4C0)',
    fallback_path='group +0x60 null and +0x70 nonnull -> 0x0306B54C -> 0x03AC7FF0 (+8 calls actor +0x4B8)',
    both_timer_plus10='0x02F838E8 (marks completion when owner state mismatches)',
    compared_prior_clock_timer='0x03906C88 (+8=0x02F7301C) is a DIFFERENT family',
    action_plus_4b8_subtype='0x03ACD5A0 (+8=0x0307C464)',
    action_plus_4c0_subtype='0x03ACD6D0 (+8=0x0307CAD0)',
    matched_member_vtable_offset_plus_4c0_can_differ_by_subclass=True,
    direct_callsite_for_fallback_factory='0x0327BE86',
    rmb_or_shift_player_key_proven=False,
    source_order_instance_proven=False,crowding_root_cause_proven=False,
    native_patch_authorized=False)
 finally:pe.close()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.out.resolve()==a.exe.resolve():p.error('NEVER_OVERWRITE_EXE')
 r=audit(a.exe)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print('PASS',r['verified_opcode_boundaries'],'code sites,',
       r['typed_vtable_slots'],'typed slots; no patch')
if __name__=='__main__':main()
