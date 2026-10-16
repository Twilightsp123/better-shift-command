#!/usr/bin/env python3
"""Read-only WH3 original EXE: queued-B packet -> member-state direct E8 gap.

Proves absence of *direct* edges only. Indirect virtual calls are unresolved.
"""
import argparse,json,struct
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA,IMAGEBASE
PINS={
0x02F4F900:'e8ebc01100',0x0306B9F0:'48895c2410',
0x0306BA23:'e8dc73d5ff',0x0306BA35:'488d8f90040000',
0x0306BA5B:'e8683defff',0x0306BB0E:'41ff9300010000',
0x0306BB44:'41ff93e8000000',0x0306BB73:'488d8f28030000',
0x0306BB7A:'e8914ed4ff',0x0306BBA0:'e89bd81d00',
0x0306BBD5:'e832cf1d00',0x0306A111:'c7812403000004000000',
0x0306A6BA:'c7832403000010000000',0x0307FB40:'808b0801000006',
0x0307FB5A:'80a108010000fb',0x0307FC7B:'888108010000',
0x03117226:'e8d52ef5ff'}
TABLE=0x0390D4F8
MEMBER_SLOT_METHODS={0x128:0x0307FB0C,0x130:0x0307FC3C,
0x138:0x0307FB50,0x368:0x0306B9F0,0x538:0x0306A100,0x550:0x0306A53C}
STATE_MUTATORS={0x0307FB0C,0x0307FC3C,0x0307FB50,0x0306A100,0x0306A53C}

def direct_callers(pe,target):
 text=next((s for s in pe.sections if s[0]=='.00cfg'),None)
 if not text:raise ValueError('EXEC_SECTION_MISSING')
 _,va,_,rp,rs=text;blob=pe.mm[rp:rp+rs]
 found=[];cache={};i=0
 while True:
  i=blob.find(b'\xe8',i)
  if i<0:break
  if i+5<=len(blob):
   at=va+i
   if at+5+struct.unpack_from('<i',blob,i+1)[0]==target:
    owner=pe.owner(at)
    if owner:
     span=owner[:2]
     if span not in cache:cache[span]=pe.starts_in(*span)
     if at in cache[span]:found.append(at)
  i+=1
 return sorted(set(found))

def audit(exe):
 pe=OriginalEXE(exe)
 try:
  if pe.sha!=SHA or pe.base!=IMAGEBASE:raise ValueError('EXE_BUILD_DRIFT')
  decoded={}
  for at,hexcode in PINS.items():
   raw=bytes.fromhex(hexcode)
   if pe.section(at)!='.00cfg' or pe.read(at,len(raw))!=raw:
    raise ValueError('OPCODE_DRIFT:'+hex(at))
   owner=pe.owner(at)
   if not owner:raise ValueError('OWNER_DRIFT:'+hex(at))
   span=owner[:2]
   if span not in decoded:decoded[span]=pe.starts_in(*span)
   if at not in decoded[span]:raise ValueError('MID_INSTRUCTION:'+hex(at))
  for slot,dest in MEMBER_SLOT_METHODS.items():
   if struct.unpack('<Q',pe.read(TABLE+slot,8))[0]!=IMAGEBASE+dest:
    raise ValueError('VTABLE_DRIFT:'+hex(slot))
  for at,dest in ((0x02F4F900,0x0306B9F0),(0x03117226,0x0306A100)):
   raw=pe.read(at,5)
   if raw[0]!=0xe8 or at+5+struct.unpack_from('<i',raw,1)[0]!=dest:
    raise ValueError('E8_DRIFT')
  import tempfile,subprocess,re
  owner=pe.owner(0x0306B9F0)[:2]
  with tempfile.NamedTemporaryFile() as f:
   f.write(pe.read(owner[0],owner[1]-owner[0]));f.flush()
   r=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64',
     '-M','intel','--no-show-raw-insn',f'--adjust-vma=0x{owner[0]:x}',f.name],
     capture_output=True,text=True,check=True)
  calls=[]
  for line in r.stdout.splitlines():
   m=re.match(r'^\s*([0-9a-f]+):\s+call\s+(.+)',line)
   if m:calls.append((int(m.group(1),16),m.group(2).strip()))
  if len(calls)!=13:raise ValueError('PACKET_RECEIVER_CALLS_DRIFT')
  if not any('r11+0x100' in b for _,b in calls) or not any('r11+0xe8' in b for _,b in calls):
   raise ValueError('INDIRECT_SLOTS_DRIFT')
  if any(b.startswith('0x') and int(b,16) in STATE_MUTATORS for _,b in calls):
   raise ValueError('DIRECT_STATE_EDGE_NOW_PRESENT')
  targets=[0x0306B9F0,0x03117214,*sorted(STATE_MUTATORS)]
  found={k:direct_callers(pe,k) for k in targets}
  expected={0x0306B9F0:[0x02F4F900],0x03117214:[],
   0x0306A100:[0x03117226],0x0306A53C:[],0x0307FB0C:[],
   0x0307FB50:[],0x0307FC3C:[]}
  if found!=expected:raise ValueError('E8_INVENTORY_DRIFT')
  return {'schema':'bsc.n1.packet_state_direct_edge_negative.v1',
    'sha256':pe.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
    'original_instruction_starts':len(PINS),
    'typed_member_slots':len(MEMBER_SLOT_METHODS),
    'packet_receiver_calls':len(calls),
    'direct_call_inventory':{hex(k):[hex(a) for a in v] for k,v in found.items()},
    'receiver_direct_state_change_edge':False,
    'indirect_state_change_excluded':False,
    'actual_shift_pair_observed':False,'patch_authorized':False}
 finally:pe.close()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--exe',type=Path,required=True);p.add_argument('--out',type=Path)
 args=p.parse_args()
 if args.out and args.exe.resolve()==args.out.resolve():p.error('NEVER_OVERWRITE_EXE')
 v=audit(args.exe)
 if args.out:
  args.out.parent.mkdir(parents=True,exist_ok=True)
  args.out.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print('PASS',v['original_instruction_starts'],'pins',v['typed_member_slots'],'vtables; NO PATCH')
if __name__=='__main__':main()
