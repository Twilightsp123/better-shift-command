#!/usr/bin/env python3
"""Read-only original WH3: converter conditional zero-return -> B node handler.

Exact SHA, PE/unwind, decoded instruction starts, direct E8/JCC guards.
A static branch is not an observation of a real Shift MOVE or its crowding cause.
"""
import argparse, json, pathlib, re, struct, subprocess, tempfile
from audit_b_member_packet_task_lifecycle import OriginalEXE, SHA

MANIFEST=pathlib.Path(__file__).with_name('converter_return_guard_manifest_20261016.txt')
CALLS={
 0x030fdb31:0x0311be18, 0x030fdc5f:0x030df598,
 0x030fdc96:0x030fc980, 0x030fddac:0x03125a1c,
 0x030fddea:0x004d9400, 0x030fde7c:0x030c1fdc,
 0x030fdee6:0x004d9400, 0x030fdf65:0x030c1fdc,
 0x03129092:0x030fda9c, 0x032815c5:0x03265b24}
BRANCHES={
 0x030fdc6e:0x030fdee1, 0x030fdc9d:0x030fdee1,
 0x030fddb6:0x030fdece, 0x030fddc2:0x030fdea3,
 0x030fddf5:0x030fde86, 0x030fdec9:0x030fe0a7,
 0x030fdef1:0x030fdf6f, 0x03129076:0x031290a2,
 0x0312908c:0x031290a2}

def pins():
 result={}
 for row in MANIFEST.read_text(encoding='utf8').splitlines():
  parts=row.split('#',1)[0].split()
  if not parts: continue
  if len(parts)!=2:raise ValueError('BAD_GUARD_ROW')
  rva=int(parts[0],16)
  if rva in result:raise ValueError('DUPLICATE_RVA')
  result[rva]=bytes.fromhex(parts[1])
 if len(result)!=76:raise ValueError('MANIFEST_DRIFT')
 return result

def branch(site,raw):
 if raw[0]==0xe9:return site+5+struct.unpack_from('<i',raw,1)[0]
 if raw[0]==0x0f and 0x80<=raw[1]<=0x8f:return site+6+struct.unpack_from('<i',raw,2)[0]
 if 0x70<=raw[0]<=0x7f:return site+2+struct.unpack_from('<b',raw,1)[0]
 raise ValueError('NOT_DIRECT_JUMP:'+hex(site))

def decoded(pe,bounds):
 a,b=bounds
 with tempfile.NamedTemporaryFile() as f:
  f.write(pe.read(a,b-a));f.flush()
  proc=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64',
      '-M','intel',f'--adjust-vma={a}',f.name],capture_output=True,text=True,check=True)
 result={}
 for line in proc.stdout.splitlines():
  match=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*([^\n]+)',line)
  if match:result[int(match.group(1),16)]=(bytes.fromhex(match.group(2)),match.group(3).strip())
 return result

def synthetic_conditional(*,solver_nonzero,candidates,allocator_ok):
 """Not a WH3 simulation; just the inspected symbolic native branch."""
 if not solver_nonzero:return 'alternate_constructor_branch'
 if candidates==0:return 'skips_route_allocation_returns_zero'
 if not allocator_ok:return 'allocator_failure_returns_zero'
 return 'route_build_attempt_result_unknown'

def audit(exe):
 pe=OriginalEXE(exe)
 try:
  if pe.sha!=SHA:raise ValueError('SHA_MISMATCH')
  d=pins();functions={}
  for site,raw in d.items():
   if pe.section(site)!='.00cfg' or pe.read(site,len(raw))!=raw:
    raise ValueError('OPCODE_CHANGED:'+hex(site))
   owner=pe.owner(site)
   if owner is None:raise ValueError('NO_FUNCTION_OWNER:'+hex(site))
   span=owner[:2]
   if span not in functions:functions[span]=decoded(pe,span)
   if site not in functions[span] or functions[span][site][0]!=raw:
    raise ValueError('NOT_ACTUAL_INSTRUCTION_START:'+hex(site))
  for site,target in CALLS.items():
   raw=pe.read(site,5)
   if raw[0]!=0xe8 or site+5+struct.unpack_from('<i',raw,1)[0]!=target:
    raise ValueError('E8_TARGET_CHANGED:'+hex(site))
  for site,target in BRANCHES.items():
   if branch(site,d[site])!=target:raise ValueError('JMP_TARGET_CHANGED:'+hex(site))
  conv=functions[pe.owner(0x030fda9c)[:2]]
  if conv[0x030fdab9][1]!='xor    r15d,r15d' or conv[0x030fdad2][1]!='mov    ebx,r15d':
   raise ValueError('RBX_INITIALIZATION_CHANGED')
  # Prove RBX remains 0 on the count-zero branch; all intervening calls
  # must obey Windows x64 callee-preservation of RBX.
  writer=re.compile(r'^(?:mov|lea|xor|add|sub|and|or|inc|dec|pop|xchg|imul|cmov\w*)\s+(?:\w+\s+PTR\s+)?(?:rbx|ebx|bx|bl|bh)\b',re.I)
  for address,(raw,asm) in conv.items():
   if (0x030fdad2<address<0x030fddc2) or (0x030fdea3<=address<0x030fdec9):
    if writer.search(asm):raise ValueError('ZERO_ROUTE_WITNESS_INVALID:'+hex(address))
  if conv[0x030fddc2][1]!='jbe    0x30fdea3' or conv[0x030fe0b8][1]!='mov    rax,rbx':
   raise ValueError('NULL_RETURN_PATH_CHANGED')
  manager=functions[pe.owner(0x03129092)[:2]]
  if [manager[site][1] for site in (0x03129092,0x03129097,0x0312909e)]!=[
   'call   0x30fda9c','mov    QWORD PTR [rdi+0x70],rax','mov    BYTE PTR [rdi+0x8],r13b']:
   raise ValueError('MANAGER_HANDLE_AFTER_RETURN_CHANGED')
  return {'schema':'bsc.n1.converter_return_contract.v1',
   'sha256':pe.sha,'proof':'EXACT_ORIGINAL_EXE_STATIC',
   'instruction_starts':len(d),'E8_edges':len(CALLS),'JCC_JMP_edges':len(BRANCHES),
   'converter_return':'0x030FE0B8 RAX=RBX',
   'zero_count_condition':'0x030FDDB6 solver nonzero then 0x030FDDC2 count<=0 skips allocation and returns RBX=0',
   'allocation_failure_condition':'0x030FDEF1 branches to 0x030FDF6F where RBX=R15=0 in that branch',
   'manager':'0x03129092 converter, 0x03129097 stores node+0x70, 0x0312909E sets processed node+0x08 without nonnull result gate',
   'solver_success_and_zero_candidates_jointly_reachable_in_game_proven':False,
   'same_SHIFT_instance_observed':False,
   'native_patch_authorized':False}
 finally:pe.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--exe',type=pathlib.Path,required=True)
 ap.add_argument('--out',type=pathlib.Path)
 a=ap.parse_args()
 if a.out and a.out.resolve()==a.exe.resolve():ap.error('EXE_OVERWRITE_FORBIDDEN')
 result=audit(a.exe)
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print('STATIC_PASS',result['instruction_starts'],'code+starts',result['E8_edges'],'E8',result['JCC_JMP_edges'],'branches; NO PATCH')
if __name__=='__main__':main()
