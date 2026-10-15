#!/usr/bin/env python3
"""WH3 original EXE: read-only RMB replace vs queued MOVE/state lifecycle.

Two SHA-pinned manifests, real instruction-start & E8/JCC checks; NO gameplay patch.
The CLI needs private original EXE and GNU objdump. Public CI tests contracts only.
"""
import argparse, json, re, struct, subprocess, tempfile
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE, SHA, IMAGEBASE

HERE=Path(__file__).resolve().parent
MANIFESTS={'queue':('rmb_shift_exact_pins.txt',72),'state':('state_lifecycle_exact_pins.txt',69)}
MOVE=0x030323C8
CALLS={0x0311E362:0x03125A1C,0x0311E445:0x0311EC28,
 0x0311E636:0x0311E80C,0x0311EAC7:0x0310F560,
 0x02F5620A:0x02F4EFE0,0x02F56467:0x02F4EFE0,
 0x02F56479:0x02F4F514,0x02F4F62C:0x03279EE8}
BRANCHES={0x0311DEC0:0x0311E578,0x0311DEC9:0x0311E462,
 0x0311DED2:0x0311E14C,0x0311E36C:0x0311E41B,
 0x0311E63F:0x0311E7E0,0x0311EB17:0x0311EBD8}
MOVEVT={0x08:0x03025D70,0x38:0x008D3350,
        0x40:0x03039FB0,0x48:0x03040864}

def manifests():
 result={}
 for label,(name,count) in MANIFESTS.items():
  out={}
  for lineno,line in enumerate((HERE/name).read_text('utf-8').splitlines(),1):
   words=line.split('#',1)[0].split()
   if not words:continue
   if len(words)!=2:raise ValueError(f'BAD_PIN:{name}:{lineno}')
   rva=int(words[0],16)
   if rva in out:raise ValueError('DUPLICATE_PIN:'+hex(rva))
   out[rva]=bytes.fromhex(words[1])
  if len(out)!=count:raise ValueError('PIN_INVENTORY_DRIFT:'+name)
  result[label]=out
 return result

def branch_target(site,code):
 if len(code)==6 and code[:1]==b'\x0f' and 0x80<=code[1]<=0x8f:
  return site+6+struct.unpack_from('<i',code,2)[0]
 if len(code)==2 and 0x70<=code[0]<=0x7f:
  return site+2+struct.unpack_from('<b',code,1)[0]
 raise ValueError('INVALID_JCC:'+hex(site))

def decode(pe,begin,end):
 with tempfile.NamedTemporaryFile() as f:
  f.write(pe.read(begin,end-begin));f.flush()
  proc=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel',
       '--no-show-raw-insn',f'--adjust-vma=0x{begin:x}',f.name],
       capture_output=True,text=True,check=True)
 return [(int(m.group(1),16),m.group(2).strip()) for line in proc.stdout.splitlines()
       if (m:=re.match(r'^\s*([0-9a-fA-F]+):\s+(.+)$',line))]

def branch_history(flag,ready,helper_zero):
 """Synthetic conditional path; not actual frame-by-frame engine execution."""
 if not flag:return [1,4]
 result=[1,2]
 if ready:
  result.append(3)
  if helper_zero:result.append(4)
 return result

def shorttask_b_gate(state,valid_flag,stage):
 return state==4 and valid_flag==0 and stage==3

def audit(path):
 pins=manifests();pe=OriginalEXE(path)
 try:
  if pe.sha!=SHA or pe.base!=IMAGEBASE:raise ValueError('BAD_EXE')
  cache={}
  for batch in pins.values():
   for rva,data in batch.items():
    if pe.section(rva)!='.00cfg' or pe.read(rva,len(data))!=data:
     raise ValueError('OPCODE_DRIFT:'+hex(rva))
    owner=pe.owner(rva)
    if not owner:raise ValueError('FUNCTION_OWNER_MISSING:'+hex(rva))
    bounds=owner[:2]
    if bounds not in cache:cache[bounds]=decode(pe,*bounds)
    if rva not in {x for x,_ in cache[bounds]}:
     raise ValueError('MID_INSTRUCTION:'+hex(rva))
  for site,target in CALLS.items():
   code=pe.read(site,5)
   if code[0]!=0xe8 or site+5+struct.unpack_from('<i',code,1)[0]!=target:
    raise ValueError('E8_DRIFT:'+hex(site))
  for site,target in BRANCHES.items():
   if branch_target(site,pins['state'][site])!=target:
    raise ValueError('JCC_DRIFT:'+hex(site))
  for slot,target in MOVEVT.items():
   if struct.unpack('<Q',pe.read(0x0390B4F0+slot,8))[0]!=IMAGEBASE+target:
    raise ValueError('MOVE_VTABLE_DRIFT:'+hex(slot))
  # Search raw encodings, then require real instruction starts, owner and exact E8.
  s=next((x for x in pe.sections if x[0]=='.00cfg'),None)
  if not s:raise ValueError('EXECUTABLE_SECTION_MISSING')
  _,va,_,rp,rs=s
  sites=[];pos=rp
  while True:
   pos=pe.mm.find(b'\xe8',pos,rp+rs-4)
   if pos<0:break
   site=va+pos-rp;pos+=1
   if site+5+struct.unpack_from('<i',pe.mm,pos)[0]!=MOVE:continue
   owner=pe.owner(site)
   if not owner:raise ValueError('CALL_SITE_HAS_NO_OWNER:'+hex(site))
   bounds=owner[:2]
   if bounds not in cache:cache[bounds]=decode(pe,*bounds)
   if (site,f'call   0x{MOVE:x}') not in cache[bounds]:
    raise ValueError('SPURIOUS_CALL_SITE:'+hex(site))
   sites.append(site)
  if len(sites)!=64:raise ValueError('MOVE_CALLSITE_INVENTORY_DRIFT')
  # Two independent queue-manager self-reissue sites preserve R8B=1.
  for site in (0x030444C1,0x03044531):
   if site not in sites:raise ValueError('INTERNAL_APPEND_CALLSITE_DRIFT')
  leaf=decode(pe,0x02D25674,0x02D256EA)
  if leaf[0][0]!=0x02D25674 or leaf[-1][0]!=0x02D256E9 or not leaf[-1][1].startswith('ret'):
   raise ValueError('COPIER_LEAF_BOUNDS_DRIFT')
  if any(re.match(r'\w+\s+r8(?:b|d|w)?\s*,',op) or re.search(r'\bcall\b',op)
         for _,op in leaf):raise ValueError('COPIER_R8_CLOBBER')
  # No-unwind shortTask bigTask getter: +0x80 indirection or fallback +0x98.
  if pe.owner(0x02F4EFE0) or pe.read(0x02F4EFE0,7)!=bytes.fromhex('488b8180000000') or \
     pe.read(0x02F4EFF0,7)!=bytes.fromhex('488b8198000000'):
   raise ValueError('SHORTTASK_GETTER_DRIFT')
  if pe.read(0x02F4EFEF,1)!=b'\xc3' or pe.read(0x02F4EFF7,1)!=b'\xc3':
   raise ValueError('SHORTTASK_GETTER_TERMINATION_DRIFT')
  return {'schema':'bsc.n1.rmb_shift_lifecycle_comparison.v1',
     'proof':'EXACT_ORIGINAL_EXE_STATIC','sha256':pe.sha,
     'queue_instruction_starts':len(pins['queue']),
     'state_instruction_starts':len(pins['state']),
     'native_move_direct_calls':len(sites),'typed_move_vtable_slots':len(MOVEVT),
     'verified_state_E8':len(CALLS),'verified_state_jcc':len(BRANCHES),
     'internal_queue_append_sites':[hex(x) for x in (0x030444C1,0x03044531)],
     'early_enqueue_delta':'R9B controls reset vs append; all new slots start task+0xA0 NULL',
     'late_handoff_delta':'eligible old bigTask may be moved into next MOVE slot, state1; not automatic for append',
     'conditional_state1_paths':{'projected':[1,2,3,4], 'direct_fallback':[1,4]},
     'shorttask_b_callback_tuple':[4,0,3],
     'hotkey_instance_mapped':False,'same_shorttask_identity_across_all_phases_proven':False,
     'same_member_goal_generation_mismatch_proven':False,'gameplay_patch_authorized':False}
 finally:pe.close()

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--exe',type=Path,required=True);parser.add_argument('--out',type=Path)
 a=parser.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():parser.error('EXE_OVERWRITE_FORBIDDEN')
 answer=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(exist_ok=True,parents=True)
  a.out.write_text(json.dumps(answer,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('PASS',answer['queue_instruction_starts'],'queue pins',answer['state_instruction_starts'],
       'state pins',answer['native_move_direct_calls'],'MOVE E8; NO GAMEPLAY PATCH')
if __name__=='__main__':main()
