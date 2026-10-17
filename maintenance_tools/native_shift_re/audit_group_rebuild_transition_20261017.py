#!/usr/bin/env python3
"""Fixed-WH3 original Group rebuild: retire -> checkout -> rebind ordering.

Read-only original-EXE audit. Does NOT prove stale dereference, race, real Shift
runtime branch, or patch safety.
"""
import argparse,json,re,struct,subprocess,tempfile
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA,IMAGEBASE
PINS=Path(__file__).with_name('group_rebuild_transition_pins_20261017.txt')
E8={
0x301b902:0x30197a8,0x301b91f:0x301b834,
0x301b946:0x30e0460,0x301b968:0x30d20a4,
0x30197e0:0x302c2d4,0x301b8b7:0x30c2c3c,
0x301b8ca:0x1325434,0x302db8e:0x301b8e4,
0x303dcff:0x301b8e4,0x30200ef:0x301b8e4,
0x301a284:0x301b8e4,0x3039df1:0x301dc0c,
0x3043770:0x304433c,0x304377c:0x3043520,
0x3043784:0x3047628}
CALLERS=[0x301a284,0x30200ef,0x302db8e,0x303dcff]
def pins():
 out={}
 for ln,line in enumerate(PINS.read_text('utf8').splitlines(),1):
  parts=line.split('#',1)[0].split()
  if not parts:continue
  if len(parts)!=2:raise ValueError('PIN_ROW:'+str(ln))
  at=int(parts[0],16)
  if at in out:raise ValueError('DUPLICATE_OPCODE')
  out[at]=bytes.fromhex(parts[1])
 if len(out)!=72:raise ValueError('PIN_COUNT_DRIFT')
 return out
def decoded(pe,span):
 lo,hi=span
 with tempfile.NamedTemporaryFile() as f:
  f.write(pe.read(lo,hi-lo));f.flush()
  r=subprocess.run(['objdump','-D','-w','-b','binary','-m','i386:x86-64',
      '-M','intel',f'--adjust-vma={lo}',f.name],capture_output=True,text=True,check=True)
 d={}
 for line in r.stdout.splitlines():
  m=re.match(r'^\s*([0-9a-fA-F]+):\s+((?:[0-9a-fA-F]{2} )+)\s*(.*)',line)
  if m:d[int(m.group(1),16)]=(bytes.fromhex(m.group(2)),m.group(3).strip())
 return d
def callers(pe,target):
 section=next((s for s in pe.sections if s[0]=='.00cfg'),None)
 if section is None:raise ValueError('CODE_SECTION_MISSING')
 _,va,_,rp,n=section;data=pe.mm[rp:rp+n]
 out=[];cache={};i=0
 while True:
  i=data.find(b'\xe8',i)
  if i<0:break
  if i+5<=len(data):
   at=va+i
   if at+5+struct.unpack_from('<i',data,i+1)[0]==target:
    owner=pe.owner(at)
    if owner:
     span=owner[:2]
     if span not in cache:cache[span]=pe.starts_in(*span)
     if at in cache[span]:out.append(at)
  i+=1
 return sorted(set(out))
def audit(exe):
 pe=OriginalEXE(exe)
 try:
  if pe.sha!=SHA or pe.base!=IMAGEBASE:raise ValueError('BUILD_MISMATCH')
  d=pins();owners={}
  for at,raw in d.items():
   if pe.section(at)!='.00cfg' or pe.read(at,len(raw))!=raw:
    raise ValueError('OPCODE_DRIFT:'+hex(at))
   owner=pe.owner(at)
   if owner is None:raise ValueError('UNWIND_OWNER_MISSING:'+hex(at))
   span=owner[:2]
   if span not in owners:owners[span]=decoded(pe,span)
   if owners[span].get(at,(None,))[0]!=raw:
    raise ValueError('MID_INSTRUCTION:'+hex(at))
  for at,dest in E8.items():
   b=d[at]
   if b[0]!=0xe8 or at+5+struct.unpack_from('<i',b,1)[0]!=dest:
    raise ValueError('DIRECT_CALL_DRIFT:'+hex(at))
  if callers(pe,0x301b8e4)!=CALLERS:raise ValueError('REBUILD_CALLER_SET_DRIFT')
  rebuild=owners[pe.owner(0x301b8e4)[:2]]
  root_writes=[at for at,(_,op) in rebuild.items()
    if re.search(r'^(?:mov|and|or|xor|xchg)\s+(?:QWORD PTR )?\[rsi\+0x32f8\]',op)]
  if root_writes!=[0x301b96d]:raise ValueError('EARLY_DIRECT_ROOT_STORE_FOUND')
  retired=owners[pe.owner(0x302c2d4)[:2]]
  checkout=owners[pe.owner(0x301b834)[:2]]
  if retired[0x302c2f2][1]!='mov    QWORD PTR [rdi],rax' or \
     retired[0x302c2f5][1]!='mov    QWORD PTR [rbx],rdi':
   raise ValueError('POOL_RETURN_LIFO_DRIFT')
  if checkout[0x301b874][1]!='mov    rbx,QWORD PTR [rdi+0x58]' or \
     checkout[0x301b8b0][1]!='mov    QWORD PTR [rdi+0x58],rcx':
   raise ValueError('POOL_CHECKOUT_LIFO_DRIFT')
  return dict(schema='bsc.n1.group_rebuild_nonatomic_transition.v1',
    original_exe_sha256=pe.sha,proof='EXACT_ORIGINAL_EXE_STATIC',
    guarded_decoded_sites=len(d),verified_e8=len(E8),
    real_direct_callers=[hex(s) for s in CALLERS],
    typed_unwind_functions=len(owners),
    ordered_sites=['0x301b902 recycle old group vector',
      '0x301b91f checkout from pool','0x301b968 initialize group',
      '0x301b96d directly assign UnitRoot+0x32F8'],
    no_direct_root_clear_before_retirement_in_this_caller=True,
    intermediate_retired_pointer_possible=True,
    same_address_new_checkout_incarnation_possible=True,
    unexamined_indirect_side_effects_excluded=False,
    queued_shift_reaches_this_branch_proven=False,
    runtime_stale_dereference_proven=False,
    safe_hook_ready=False,native_patch_authorized=False)
 finally:pe.close()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True);p.add_argument('--out',type=Path)
 a=p.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():p.error('EXE_OVERWRITE_FORBIDDEN')
 r=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
 print('STATIC_PASS',r['guarded_decoded_sites'],'instruction starts',
   r['verified_e8'],'E8; NO PATCH')
if __name__=='__main__':main()
