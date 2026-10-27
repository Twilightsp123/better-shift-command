#!/usr/bin/env python3
"""R82 constructor-time Root/member/Group shared-context proof, offline only."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).parent
BASE=0x140000000
class Drift(ValueError):pass
def scenario(initial,member_now=None,group_now=None,root_now=None):
 if not isinstance(initial,str) or not initial:raise Drift('EMPTY_CONTEXT')
 context=lambda v:initial if v is None else v
 return {'construction_source_same':True,
   'current_pointer_same':len({context(member_now),context(group_now),context(root_now)})==1,
   'queued_move_generation_proven':False,'gameplay_patch_authorized':False}
def verify(data,m):
 if len(data)!=m['exe_size'] or hashlib.sha256(data).hexdigest()!=m['exe_sha256']:
  raise Drift('SHA_SIZE_DRIFT')
 if data[:2]!=b'MZ':raise Drift('MZ')
 p=struct.unpack_from('<I',data,0x3c)[0]
 if not 0x40<=p<0x1000 or data[p:p+4]!=b'PE\0\0':raise Drift('PE')
 if struct.unpack_from('<H',data,p+4)[0]!=0x8664 or struct.unpack_from('<H',data,p+24)[0]!=0x20b:
  raise Drift('PE64')
 if struct.unpack_from('<Q',data,p+48)[0]!=BASE:raise Drift('BASE')
 count=struct.unpack_from('<H',data,p+6)[0];opt=struct.unpack_from('<H',data,p+20)[0];s=[]
 for i in range(count):
  q=p+24+opt+i*40
  _,r,size,o=struct.unpack_from('<IIII',data,q+8)
  if o+size>len(data):raise Drift('SECTION')
  s.append((r,size,o))
 def read(r,n):
  for a,size,off in s:
   if a<=r and r+n<=a+size:return data[off+r-a:off+r-a+n]
  raise Drift('RVA')
 e,sz=struct.unpack_from('<II',data,p+24+112+3*8)
 unwind={}
 for k in range(sz//12):
  a,end,u=struct.unpack('<III',read(e+k*12,12));unwind[a]=end
 for name,(a,z) in m['function_ranges'].items():
  if name in m['no_unwind_leaf']:
   if int(a,16) in unwind:raise Drift('LEAF_DRIFT')
  elif unwind.get(int(a,16))!=int(z,16):raise Drift('UNWIND_'+name)
 for site,item in m['pins'].items():
  r=int(site,16);expected=bytes.fromhex(item['hex'])
  lo,hi=m['function_ranges'][item['owner']]
  if r<int(lo,16) or r+len(expected)>int(hi,16) or read(r,len(expected))!=expected:
   raise Drift('PIN_DRIFT_'+site)
 for site,target in m['e8_edges'].items():
  r=int(site,16);b=read(r,5)
  if b[0]!=0xe8 or r+5+struct.unpack_from('<i',b,1)[0]!=int(target,16):
   raise Drift('CALL_DRIFT_'+site)
 # Proof hinges on exact source/base/consumer field offsets, not arbitrary matching bytes.
 for site,raw in {'03013235':'488d5630','03052bd5':'4c8bfa',
    '03141803':'488b4208','03141814':'48894158',
    '03052f62':'488b4358','03052f6d':'48898320070000',
    '03020a17':'4c8bc6','03020952':'4c8940e0',
    '030c7cd2':'488b5208','030c7cd6':'4883c230',
    '030c7dbc':'488b4208','030c7dca':'48894110',
    '030c7cf9':'488983100a0000'}.items():
  if m['pins'][site]['hex']!=raw:raise Drift('CONTEXT_SOURCE_DRIFT_'+site)
 return {'grade':'EXACT_PRIVATE_EXE_STATIC','pins':len(m['pins']),
  'e8':len(m['e8_edges']),'constructor_source_proven':True,
  'same_queued_shift_generation_proven':False,'gameplay_patch_authorized':False}
if __name__=='__main__':
 try:
  m=json.loads((ROOT/'r82_context_manifest.json').read_text())
  print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
 except (IndexError,ValueError,OSError,struct.error) as ex:
  print('FAIL_CLOSED',ex);sys.exit(2)
