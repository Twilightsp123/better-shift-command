#!/usr/bin/env python3
"""R74 public SHA-gated read-only group roster evidence. Never a live WH3 Hook."""
import hashlib,json,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
class Drift(ValueError):pass
def interleave(roster=('A','B','C'),transferred='B'):
 if not roster or transferred not in roster or len(set(roster))!=len(roster):
  raise ValueError('INVALID_SYNTHETIC_ROSTER')
 old=list(roster)
 sent=[old[0]]
 index=old.index(transferred)
 old[index]=old[-1]
 old.pop()
 sent.extend(old[1:])
 return {'grade':'SYNTHETIC_ONLY','old_roster':old,'possible_sent':sent,
         'actual_concurrent_executions_proven':False}
def verify(data,m):
 if len(data)!=m['exe_size'] or hashlib.sha256(data).hexdigest()!=m['exe_sha256']:
  raise Drift('EXACT_SHA_AND_SIZE_REQUIRED')
 if data[:2]!=b'MZ':raise Drift('NOT_MZ')
 p=struct.unpack_from('<I',data,0x3c)[0]
 if not 0x40<=p<0x1000 or data[p:p+4]!=b'PE\0\0':raise Drift('NOT_PE')
 if struct.unpack_from('<H',data,p+4)[0]!=0x8664 or struct.unpack_from('<H',data,p+24)[0]!=0x20b:raise Drift('NOT_AMD64')
 if struct.unpack_from('<Q',data,p+48)[0]!=0x140000000:raise Drift('BASE_DRIFT')
 n=struct.unpack_from('<H',data,p+6)[0];optional=struct.unpack_from('<H',data,p+20)[0];ss=[]
 for k in range(n):
  j=p+24+optional+40*k
  _,r,s,o=struct.unpack_from('<IIII',data,j+8)
  if o+s>len(data):raise Drift('SECTION_OOB')
  ss.append((r,s,o))
 def rd(r,s):
  for a,n,o in ss:
   if a<=r and r+s<=a+n:return data[o+r-a:o+r-a+s]
  raise Drift('RVA_OOB')
 for key,value in m['pins'].items():
  expected=bytes.fromhex(value)
  if rd(int(key,16),len(expected))!=expected:raise Drift('PIN_'+key)
 for key,dest in m['edges'].items():
  x=int(key,16);code=rd(x,5)
  if code[0]!=0xe8 or x+5+struct.unpack_from('<i',code,1)[0]!=int(dest,16):
   raise Drift('E8_'+key)
 for off,dest in m['group_vmethods'].items():
  addr=int(m['group_vtable'],16)+int(off,16)
  if struct.unpack('<Q',rd(addr,8))[0]!=0x140000000+int(dest,16):
   raise Drift('GROUP_TYPE')
 for vt,slots in m['member_vtables'].items():
  for off,dest in slots.items():
   addr=int(vt,16)+int(off,16)
   if struct.unpack('<Q',rd(addr,8))[0]!=0x140000000+int(dest,16):
    raise Drift('MEMBER_TYPE')
 return {'level':'EXACT_EXE_STATIC_ONLY','pins':len(m['pins']),
         'edges':len(m['edges']),'actor_overlap_proven':False,
         'gameplay_patch_authorized':False}
if __name__=='__main__':
 try:
  m=json.loads((HERE/'r74_roster_writer_pins.json').read_text())
  print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
 except (IndexError,OSError,ValueError,struct.error) as e:
  print('FAIL_CLOSED',str(e));sys.exit(2)
