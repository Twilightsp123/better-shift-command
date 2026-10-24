#!/usr/bin/env python3
"""R73: exact-EXE code identity and synthetic member roster re-read. NO hook."""
import hashlib,json,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
class EvidenceError(ValueError):pass
def verify(data,m):
 if len(data)!=m['exe_size'] or hashlib.sha256(data).hexdigest()!=m['exe_sha256']:
  raise EvidenceError('EXE_SHA_SIZE_MISMATCH')
 if data[:2]!=b'MZ':raise EvidenceError('MZ')
 p=struct.unpack_from('<I',data,0x3c)[0]
 if p>0x1000 or data[p:p+4]!=b'PE\0\0':raise EvidenceError('PE')
 if struct.unpack_from('<H',data,p+4)[0]!=0x8664 or struct.unpack_from('<H',data,p+24)[0]!=0x20b:raise EvidenceError('AMD64_PE32_PLUS')
 if struct.unpack_from('<Q',data,p+48)[0]!=0x140000000:raise EvidenceError('IMAGEBASE')
 n=struct.unpack_from('<H',data,p+6)[0];opt=struct.unpack_from('<H',data,p+20)[0];sects=[]
 for k in range(n):
  q=p+24+opt+k*40
  _,r,sz,off=struct.unpack_from('<IIII',data,q+8)
  if off+sz>len(data):raise EvidenceError('SECTION_BOUNDS')
  sects.append((r,sz,off))
 def grab(r,n):
  for base,length,off in sects:
   if base<=r and r+n<=base+length:return data[off+r-base:off+r-base+n]
  raise EvidenceError('RVA_BOUNDS')
 for k,hexstr in m['pins'].items():
  expected=bytes.fromhex(hexstr)
  if grab(int(k,16),len(expected))!=expected:raise EvidenceError('PIN_DRIFT_'+k)
 for k,t in m['e8_edges'].items():
  r=int(k,16);b=grab(r,5)
  if b[0]!=0xe8 or r+5+struct.unpack_from('<i',b,1)[0]!=int(t,16):
   raise EvidenceError('EDGE_DRIFT_'+k)
 for k,v in {'0326a9c4':'488bf2','0326aa38':'395e24','0326aa44':'488b4628',
             '0326aa4b':'4c8b34c8','0326abaf':'ff9068030000',
             '0326abbd':'443b6624','0326abc1':'0f827dfeffff'}.items():
  if m['pins'][k]!=v:raise EvidenceError('ROSTER_CONTRACT_DRIFT')
 return {'exact_exe_static_only':True,'pins':len(m['pins']),'e8':len(m['e8_edges']),
         'same_group_roster_immutable_proven':False,'actual_shift_hit_proven':False,
         'game_hook_authorized':False}
def simulate(rosters,epochs=None,fail_closed=False):
 """Synthetic only: re-read array at each indexed iteration. No WH3 event claim."""
 if not rosters or any(not isinstance(a,(list,tuple)) or type(c)!=int or c<0 or len(a)<c for a,c in rosters):
  raise ValueError('BAD_ROSTER')
 if fail_closed and epochs is not None and len(set(epochs))>1:
  raise ValueError('CROSS_GENERATION')
 if not rosters[0][1]:return []
 out=[];i=0
 while i<len(rosters):
  members,count=rosters[i]
  if i>=count:break
  out.append(members[i]);i+=1
  if i<len(rosters) and i>=rosters[i][1]:break
 return out
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('usage: python audit_r73_roster.py matching_Warhammer3.exe')
 try:
  m=json.loads((HERE/'r73_roster_pins.json').read_text())
  print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
 except (ValueError,OSError,struct.error) as e:
  print('FAIL_CLOSED',str(e));raise SystemExit(2)
