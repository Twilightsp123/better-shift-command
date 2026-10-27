#!/usr/bin/env python3
"""R78 current-build, exact SHA read-only typed route audit; no live Hook."""
import hashlib,json,struct,sys
from pathlib import Path
class EvidenceDrift(ValueError):pass
def model(mode,fifth=1):
 if type(mode)!=int or mode<0 or type(fifth)!=int or fifth not in (0,1):raise ValueError('BAD_INPUT')
 return {'packet50':0x26,'packet51':1|(2 if fifth else 0),'member_adjust':bool(fifth),
         'vslot':'100' if mode in (1,2) else 'e8','final_nav_goal_proven':False}
def verify(b,m):
 if len(b)!=m['size'] or hashlib.sha256(b).hexdigest()!=m['sha256']:raise EvidenceDrift('SHA_FAIL')
 if b[:2]!=b'MZ':raise EvidenceDrift('NOT_MZ')
 p=struct.unpack_from('<I',b,0x3c)[0]
 if p<0x40 or p>=0x1000 or b[p:p+4]!=b'PE\0\0':raise EvidenceDrift('NOT_PE')
 if struct.unpack_from('<H',b,p+4)[0]!=0x8664 or struct.unpack_from('<H',b,p+24)[0]!=0x20b:raise EvidenceDrift('NOT_PE64')
 if struct.unpack_from('<Q',b,p+48)[0]!=0x140000000:raise EvidenceDrift('BASE')
 n=struct.unpack_from('<H',b,p+6)[0];opt=struct.unpack_from('<H',b,p+20)[0];ss=[]
 for k in range(n):
  t=p+24+opt+40*k;_,r,z,o=struct.unpack_from('<IIII',b,t+8)
  if o+z>len(b):raise EvidenceDrift('SECTION')
  ss.append((r,z,o))
 def rd(r,z):
  for a,n,o in ss:
   if a<=r and r+z<=a+n:return b[o+r-a:o+r-a+z]
  raise EvidenceDrift('RVA')
 base,num=struct.unpack_from('<II',b,p+24+112+3*8)
 fn={}
 for k in range(num//12):
  a,z,u=struct.unpack('<III',rd(base+12*k,12));fn[a]=z
 for name,(a,z) in m['functions'].items():
  if fn.get(int(a,16))!=int(z,16):raise EvidenceDrift('UNWIND_'+name)
 for addr,site in m['pins'].items():
  r=int(addr,16);v=bytes.fromhex(site['hex']);a,z=m['functions'][site['owner']]
  if r<int(a,16) or r+len(v)>int(z,16) or rd(r,len(v))!=v:raise EvidenceDrift('PIN_'+addr)
 for addr,target in m['e8'].items():
  r=int(addr,16);v=rd(r,5)
  if v[0]!=0xe8 or r+5+struct.unpack_from('<i',v,1)[0]!=int(target,16):
   raise EvidenceDrift('CALL_'+addr)
 for slot,target in m['methods'].items():
  if struct.unpack('<Q',rd(int(m['vtable'],16)+int(slot,16),8))[0]!=0x140000000+int(target,16):
   raise EvidenceDrift('VTABLE')
 return {'pins':len(m['pins']),'calls':len(m['e8']),'functions':len(m['functions']),
         'A_record_is_final_nav_goal_proven':False,'gameplay_patch_authorized':False}
if __name__=='__main__':
 try:
  m=json.loads((Path(__file__).with_name('r78_focus_pins.json')).read_text())
  print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
 except (IndexError,OSError,ValueError,struct.error) as ex:
  print('FAIL_CLOSED',ex);sys.exit(2)
