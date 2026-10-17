#!/usr/bin/env python3
"""Exact fixed-WH3 Group pool checkout/return and root group binding (read-only)."""
import argparse,json,re,struct,subprocess,tempfile
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA,IMAGEBASE
MANIFEST=Path(__file__).with_name('group_pool_lifecycle_pins_20261017.txt')
RECOMPUTE=(0x301dc59,0x301dc8e,0x301dcc6,0x301dcf0,0x301dd1a,
 0x301dd49,0x301de7d,0x301e0e7,0x301e197,0x301e1ea,0x301e205)
OTHER={0x3007ce8:'initial_zero',0x301b96d:'new_group',
 0x3039e92:'first_group_fallback',0x303bbc6:'clear_before_rebuild'}
CALLS={0x30197e0:0x302c2d4,0x301b886:0x4d9400,
 0x301b898:0x3006d24,0x301b8b7:0x30c2c3c,0x301b8ca:0x1325434,
 0x301b91f:0x301b834,0x301b968:0x30d20a4,
 0x301dce8:0x30337d8,0x301dd12:0x30337d8,
 0x301de78:0x3011c98,0x301e0e2:0x3011d04,
 0x301e1fd:0x30337d8,0x3039df1:0x301dc0c,
 0x3039e3f:0x30cfac4,0x3039e83:0x301b834,
 0x303bb78:0x30197a8,0x303bbd3:0x3039d9c,
 0x3043770:0x304433c,0x304377c:0x3043520,
 0x3043784:0x3047628,0x304379a:0x303a98c}
OWNER_SETS={
 'pool_checkout':(0x301b834,0x301b874,0x301b8b0),
 'pool_return':(0x302c2d4,0x302c2f2,0x302c2f5),
 'pool_vector_clear':(0x30197a8,0x30197e0,0x30197ee),
 'group_update':(0x301dc0c,0x301dc23,*RECOMPUTE),
 'group_rebind':(0x3039d9c,0x3039de7,0x3039df1,0x3039e92),
 'group_teardown':(0x303bb60,0x303bbc6,0x303bbd3),
 'unit_tick':(0x3043648,0x3043770,0x304377c)}
def pins():
 d={}
 for line in MANIFEST.read_text('utf8').splitlines():
  w=line.split('#',1)[0].split()
  if not w:continue
  if len(w)!=2:raise ValueError('PIN_FORMAT_DRIFT')
  a=int(w[0],16)
  if a in d:raise ValueError('DUPLICATE_PIN')
  d[a]=bytes.fromhex(w[1])
 if len(d)!=120:raise ValueError('PIN_COUNT_DRIFT')
 return d
def decode(pe,lo,hi):
 with tempfile.NamedTemporaryFile() as f:
  f.write(pe.read(lo,hi-lo));f.flush()
  o=subprocess.run(['objdump','-D','-w','-b','binary','-m','i386:x86-64',
     '-M','intel',f'--adjust-vma={lo}',f.name],capture_output=True,text=True,check=True).stdout
 d={}
 for line in o.splitlines():
  m=re.match(r'^\s*([0-9a-fA-F]+):\s+((?:[0-9a-fA-F]{2} )+)\s*(.*)$',line)
  if m:d[int(m.group(1),16)]=(bytes.fromhex(m.group(2)),m.group(3).strip())
 return d
def audit(exe):
 pe=OriginalEXE(Path(exe))
 try:
  if pe.sha!=SHA or pe.base!=IMAGEBASE:raise ValueError('EXE_DRIFT')
  d=pins();decoded={}
  for at,b in d.items():
   if pe.section(at)!='.00cfg' or pe.read(at,len(b))!=b:
    raise ValueError('OPCODE_CHANGED:'+hex(at))
   owner=pe.owner(at)
   if owner is None:raise ValueError('NO_OWNER:'+hex(at))
   span=owner[:2]
   if span not in decoded:decoded[span]=decode(pe,*span)
   if decoded[span].get(at,(None,None))[0]!=b:
    raise ValueError('MID_INSTRUCTION:'+hex(at))
  for label,addresses in OWNER_SETS.items():
   if len({pe.owner(a)[:2] for a in addresses})!=1:
    raise ValueError('OWNER_TYPE_DRIFT:'+label)
  for at,target in CALLS.items():
   b=d[at]
   if len(b)!=5 or b[0]!=0xe8 or at+5+struct.unpack_from('<i',b,1)[0]!=target:
    raise ValueError('E8_DRIFT:'+hex(at))
  a=decoded[pe.owner(0x301dc0c)[:2]]
  writes={at for at,(b,s) in a.items() if re.search(
    r'^(?:mov|and)\s+QWORD PTR \[rsi\+0x32f8\]',s)}
  if writes!=set(RECOMPUTE):raise ValueError('GROUP_BINDING_WRITER_DRIFT')
  for at in OTHER:
   s=decoded[pe.owner(at)[:2]][at][1]
   if not re.search(r'^(?:mov|and)\s+QWORD PTR \[(?:r15|rsi|rbx)\+0x32f8\]',s):
    raise ValueError('OTHER_ROOT_GROUP_STORE_DRIFT')
  checkout=decoded[pe.owner(0x301b834)[:2]]
  retire=decoded[pe.owner(0x302c2d4)[:2]]
  if checkout[0x301b874][1]!='mov    rbx,QWORD PTR [rdi+0x58]' or checkout[0x301b8b0][1]!='mov    QWORD PTR [rdi+0x58],rcx':
   raise ValueError('FREE_LIST_POP_CHANGED')
  if retire[0x302c2f2][1]!='mov    QWORD PTR [rdi],rax' or retire[0x302c2f5][1]!='mov    QWORD PTR [rbx],rdi':
   raise ValueError('FREE_LIST_PUSH_CHANGED')
  return dict(schema='bsc.n1.typed_group_pool_binding.v1',proof='EXACT_ORIGINAL_EXE_STATIC',
   original_exe_sha256=pe.sha,original_opcode_starts=len(d),
   direct_calls=len(CALLS),unwind_functions=len(decoded),
   group_recompute_root_stores=[hex(x) for x in RECOMPUTE],
   typed_root_initial_and_rebinding_sites={hex(k):v for k,v in OTHER.items()},
   free_list_checkout='0x301B874 -> 0x301B8B0, pool+0x58',
   free_list_return='0x30197E0 -> 0x302C2D4 -> 0x302C2F2/F5',
   active_group_binding='UnitRoot+0x32F8',
   group_vector='UnitRoot+0x3298 / count+0x3294',
   raw_pointer_is_unique_object_lifetime=False,
   root_binding_revision_is_group_lifetime_generation=False,
   entire_game_group_writer_coverage_proven=False,
   runtime_collection_ready=False,
   shift_crowding_root_cause_proven=False,gameplay_patch_authorized=False)
 finally:pe.close()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True);p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.exe.resolve()==a.out.resolve():p.error('NEVER_OVERWRITE_EXE')
 r=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print('PASS',r['original_opcode_starts'],'instructions',r['direct_calls'],'E8; NO PATCH')
if __name__=='__main__':main()
