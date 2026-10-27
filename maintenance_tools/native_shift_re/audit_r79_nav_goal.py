#!/usr/bin/env python3
"""R79 exact WH3 EXE read-only navigation goal static verifier. Never hooks the game."""
import hashlib,json,math,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=0x140000000
class EvidenceError(ValueError):pass
def synthetic(old,new,ref_same=True,heading_same=True,bit9=False,bit15=False,context=False,mode=0):
 if len(old)!=3 or len(new)!=3 or any(type(v) not in (float,int) or not math.isfinite(v) for v in (*old,*new)):
  raise ValueError('BAD_COORDINATES')
 if mode==1:return {'copies':False,'path':'state_skip','clears_aux':False,'root_cause_proven':False}
 if bit15 and context:return {'copies':False,'path':'alternate_helper','clears_aux':False,'root_cause_proven':False}
 clear=bit9 or not ref_same or not heading_same or any(abs(a-b)>.01 for a,b in zip(old,new))
 return {'copies':True,'path':'normal','clears_aux':clear,'root_cause_proven':False}
def verify(data,m):
 if len(data)!=m['size'] or hashlib.sha256(data).hexdigest()!=m['sha256']:
  raise EvidenceError('SHA_OR_SIZE_DRIFT')
 if data[:2]!=b'MZ':raise EvidenceError('NOT_MZ')
 pe=struct.unpack_from('<I',data,0x3c)[0]
 if pe<0x40 or pe>=0x1000 or data[pe:pe+4]!=b'PE\0\0':raise EvidenceError('NOT_PE')
 if struct.unpack_from('<H',data,pe+4)[0]!=0x8664 or struct.unpack_from('<H',data,pe+24)[0]!=0x20b:raise EvidenceError('NOT_PE64')
 if struct.unpack_from('<Q',data,pe+48)[0]!=BASE:raise EvidenceError('IMAGEBASE')
 n=struct.unpack_from('<H',data,pe+6)[0];opt=struct.unpack_from('<H',data,pe+20)[0];secs=[]
 for i in range(n):
  j=pe+24+opt+40*i
  _,r,size,off=struct.unpack_from('<IIII',data,j+8)
  if off+size>len(data):raise EvidenceError('SECTION_OOB')
  secs.append((r,size,off))
 def read(r,n):
  for start,length,o in secs:
   if start<=r and r+n<=start+length:return data[o+r-start:o+r-start+n]
  raise EvidenceError('RVA_OOB')
 ex,sz=struct.unpack_from('<II',data,pe+24+112+3*8)
 unwind={}
 for i in range(sz//12):
  a,b,u=struct.unpack('<III',read(ex+i*12,12));unwind[a]=b
 for start,end in m['verified_unwind'].items():
  if unwind.get(int(start,16))!=int(end,16):raise EvidenceError('UNWIND_'+start)
 for site,rawhex in m['pins'].items():
  raw=bytes.fromhex(rawhex)
  if read(int(site,16),len(raw))!=raw:raise EvidenceError('PIN_'+site)
 for rec in m['caller_sites']:
  site=int(rec['site'],16);by=read(site,5)
  if by[0]!=0xe8 or site+5+struct.unpack_from('<i',by,1)[0]!=int(m['goal_setter'],16):
   raise EvidenceError('CALL_'+rec['site'])
  if not int(rec['owner'],16)<=site<int(m['verified_unwind'][rec['owner']],16):
   raise EvidenceError('CALL_OWNER')
 epsilon=struct.unpack('<f',read(int(m['epsilon_rva'],16),4))[0]
 if abs(epsilon-.01)>1e-7:raise EvidenceError('EPSILON_DRIFT')
 return {'grade':'EXACT_EXE_STATIC_FOCUSED','pins':len(m['pins']),'goal_callers':len(m['caller_sites']),
         'goal_epsilon':epsilon,'shift_instance_proven':False,'gameplay_patch_authorized':False}
if __name__=='__main__':
 try:
  m=json.loads((HERE/'r79_nav_goal_pins.json').read_text())
  print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
 except (IndexError,OSError,ValueError,struct.error) as e:
  print('FAIL_CLOSED',e);sys.exit(2)
