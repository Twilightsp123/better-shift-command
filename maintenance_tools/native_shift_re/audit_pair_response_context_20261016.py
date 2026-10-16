#!/usr/bin/env python3
"""Exact WH3 original: five pair-response callers and the still-untyped virtual.

Read-only binary proof; the indirect method's steering effect is UNKNOWN.
"""
import argparse,json,re,struct,subprocess,tempfile
from pathlib import Path
from audit_b_member_packet_task_lifecycle import OriginalEXE,SHA

PINS=Path(__file__).with_name('pair_response_context_pins_20261016.txt')
TARGET=0x030800c4
TRIPLES=((0x03055788,0x030557b0,0x030557bc),
 (0x0307b1dc,0x0307b1fe,0x0307b219),
 (0x0307b3aa,0x0307b3d1,0x0307b3dd),
 (0x0324f4d0,0x0324f4f7,0x0324f503),
 (0x03260cde,0x03260d05,0x03260d11))

def pins():
 out={}
 for n,line in enumerate(PINS.read_text('utf8').splitlines(),1):
  parts=line.split('#',1)[0].split()
  if not parts:continue
  if len(parts)!=2:raise ValueError('BAD_PIN_ROW:'+str(n))
  site=int(parts[0],16)
  if site in out:raise ValueError('DUPLICATE_PIN')
  out[site]=bytes.fromhex(parts[1])
 if len(out)!=31:raise ValueError('PIN_INVENTORY_DRIFT')
 return out

def decode(pe,begin,end):
 with tempfile.NamedTemporaryFile() as f:
  f.write(pe.read(begin,end-begin));f.flush()
  r=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel',
   '--no-show-raw-insn',f'--adjust-vma=0x{begin:x}',f.name],
   capture_output=True,text=True,check=True)
 out={}
 for line in r.stdout.splitlines():
  m=re.match(r'^\s*([0-9a-fA-F]+):\s+(.+)$',line)
  if m:out[int(m.group(1),16)]=m.group(2).strip()
 return out

def direct_callers(pe,target,cache):
 section=next((s for s in pe.sections if s[0]=='.00cfg'),None)
 if section is None:raise ValueError('EXEC_SECTION_MISSING')
 _,va,_,offset,size=section
 data=pe.mm[offset:offset+size]
 found=[];pos=0
 while True:
  idx=data.find(b'\xe8',pos)
  if idx<0:break
  pos=idx+1
  if idx+5>len(data):continue
  at=va+idx
  if at+5+struct.unpack_from('<i',data,idx+1)[0]!=target:continue
  owner=pe.owner(at)
  if owner is None:continue
  span=owner[:2]
  if span not in cache:cache[span]=decode(pe,*span)
  if at in cache[span] and cache[span][at].startswith('call'):found.append(at)
 return sorted(set(found))

def audit(exe):
 pe=OriginalEXE(exe)
 try:
  if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
  d=pins();cache={}
  for at,raw in d.items():
   if pe.section(at)!='.00cfg' or pe.read(at,len(raw))!=raw:raise ValueError('BYTE_DRIFT:'+hex(at))
   owner=pe.owner(at)
   if owner is None:raise ValueError('FUNCTION_OWNER_MISSING:'+hex(at))
   span=owner[:2]
   if span not in cache:cache[span]=decode(pe,*span)
   if at not in cache[span]:raise ValueError('MID_INSTRUCTION:'+hex(at))
  sites=direct_callers(pe,TARGET,cache)
  if sites!=sorted(x[2] for x in TRIPLES):raise ValueError('CALLER_INVENTORY_DRIFT')
  if d[0x03054c86]!=bytes.fromhex('4c8d6f58') or d[0x03055771]!=bytes.fromhex('498b4500'):
   raise ValueError('MEMBER_CASE_ROOT_CHANGED')
  for source,through,call in TRIPLES:
   if d[source]!=bytes.fromhex('488b9040040000') or d[through]!=bytes.fromhex('488b92f0000000'):
    raise ValueError('CONTEXT_CHAIN_CHANGED')
   raw=d[call]
   if raw[0]!=0xe8 or call+5+struct.unpack_from('<i',raw,1)[0]!=TARGET:
    raise ValueError('E8_CHANGED:'+hex(call))
   local=cache[pe.owner(call)[:2]]
   intervening=[op for at,op in local.items() if through<at<call]
   if any('call' in op or re.search(
     r'^(?:mov|xor|lea|add|sub|and|or|pop)\s+(?:\w+ PTR\s+)?(?:rdx|edx|dx|dl)\b',op)
     for op in intervening):raise ValueError('RDX_IDENTITY_BROKEN:'+hex(call))
  handler=cache[pe.owner(TARGET)[:2]]
  expected={0x030800f7:'mov    r13,rdx',
   0x0308024d:'lea    rcx,[r13+0x1d8]',
   0x03080254:'mov    rax,QWORD PTR [rcx]',
   0x03080257:'call   QWORD PTR [rax+0x10]'}
  if any(handler.get(at)!=op for at,op in expected.items()):
   raise ValueError('VIRTUAL_DISPATCH_CHANGED')
  # This excludes only explicit writes to these known member motion fields.
  direct=[(at,op) for at,op in handler.items() if re.match(
   r'^(?:mov|movss|movsd|add|sub|and|or)\s+(?:\w+ PTR )?\[(?:rbx|r14)\+(?:0xe0|0xe8|0x1e0|0x1f0)\]',op)]
  if direct:raise ValueError('DIRECT_MEMBER_MOTION_STORE_PRESENT')
  return dict(schema='bsc.n1.pair_response_context_provenance.v1',
    sha256=pe.sha,proof='EXACT_ORIGINAL_EXE_STATIC',
    guarded_instruction_starts=len(d),verified_direct_calls=len(sites),
    call_sites=[hex(s) for s in sites],
    common_path='caller source+0x440 -> +0xf0 -> embedded object +0x1d8 -> virtual+0x10',
    member_source_case='0x03054C86/0x03055771: member+0x58 supplies source object',
    explicit_speed_or_goal_stores_in_dispatcher=0,
    virtual_concrete_implementation_known=False,
    virtual_indirect_speed_effect_proven=False,
    shift_instance_connected=False,gameplay_patch_authorized=False)
 finally:pe.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--out',type=Path)
 a=ap.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():ap.error('EXE_OVERWRITE_FORBIDDEN')
 r=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('PASS',r['guarded_instruction_starts'],'pins',r['verified_direct_calls'],'callers; NO PATCH')
if __name__=='__main__':main()
