#!/usr/bin/env python3
"""R80 focused exact-EXE SHA/pin/branch audit, not a gameplay mod or Hook."""
import hashlib,json,struct,sys
from pathlib import Path
class EvidenceDrift(ValueError):pass
def choose(selector_value,special,reference,fallback):
 if type(selector_value)!=int or selector_value<0:raise ValueError('BAD_SELECTOR_VALUE')
 if selector_value==3 and special is not None:return ('manager_special',special)
 if reference is not None:return ('reference_plus_0x80',reference)
 return ('manager_fallback',fallback)
def scan_exact(nodes,head,match):
 if len(nodes)>64:raise ValueError('BUDGET')
 used=set()
 while head is not None:
  if head in used or head<0 or head>=len(nodes):raise ValueError('CYCLE_OR_BOUNDS')
  used.add(head)
  entry=nodes[head]
  if set(entry)!={'candidate','next'}:raise ValueError('SCHEMA')
  if entry['candidate']==match:return (True,head)
  head=entry['next']
 return (False,None) # Other direction-score choices NOT represented
def verify(data,m):
 if len(data)!=m['size'] or hashlib.sha256(data).hexdigest()!=m['sha256']:
  raise EvidenceDrift('SHA_FAIL_CLOSED')
 if data[:2]!=b'MZ':raise EvidenceDrift('MZ')
 pe=struct.unpack_from('<I',data,0x3c)[0]
 if pe<0x40 or pe>=0x1000 or data[pe:pe+4]!=b'PE\x00\x00':raise EvidenceDrift('PE')
 if struct.unpack_from('<H',data,pe+4)[0]!=0x8664 or struct.unpack_from('<H',data,pe+24)[0]!=0x20b:raise EvidenceDrift('PE64')
 if struct.unpack_from('<Q',data,pe+48)[0]!=0x140000000:raise EvidenceDrift('IMAGEBASE')
 n=struct.unpack_from('<H',data,pe+6)[0];opt=struct.unpack_from('<H',data,pe+20)[0];sects=[]
 for i in range(n):
  p=pe+24+opt+40*i;_,r,z,o=struct.unpack_from('<IIII',data,p+8)
  if o+z>len(data):raise EvidenceDrift('SECTION')
  sects.append((r,z,o))
 def rd(r,z):
  for a,n,o in sects:
   if a<=r and r+z<=a+n:return data[o+r-a:o+r-a+z]
  raise EvidenceDrift('RVA')
 er,sz=struct.unpack_from('<II',data,pe+24+112+3*8)
 unwind={}
 for i in range(sz//12):
  a,z,u=struct.unpack('<III',rd(er+i*12,12));unwind[a]=z
 for name,(a,z) in m['function_ranges'].items():
  if unwind.get(int(a,16))!=int(z,16):raise EvidenceDrift('OWNER_'+name)
 for a,item in m['pins'].items():
  r=int(a,16);raw=bytes.fromhex(item['hex']);fn=m['function_ranges'][item['owner']]
  if r<int(fn[0],16) or r+len(raw)>int(fn[1],16) or rd(r,len(raw))!=raw:
   raise EvidenceDrift('PIN_'+a)
 for a,target in m['e8'].items():
  r=int(a,16);b=rd(r,5)
  if b[0]!=0xe8 or r+5+struct.unpack_from('<i',b,1)[0]!=int(target,16):
   raise EvidenceDrift('E8_'+a)
 for a,target in m['branches'].items():
  r=int(a,16);b=bytes.fromhex(m['pins'][a]['hex'])
  if len(b)==2 and 0x70<=b[0]<=0x7f:z=r+2+struct.unpack_from('<b',b,1)[0]
  elif len(b)==6 and b[0]==0x0f and 0x80<=b[1]<=0x8f:z=r+6+struct.unpack_from('<i',b,2)[0]
  else:raise EvidenceDrift('JCC_ENCODING')
  if z!=int(target,16):raise EvidenceDrift('JCC_'+a)
 for a,hexcode in {'03076f7e':'488db918070000','030771ec':'4c8d8b10090000',
    '0311f410':'448b88a0000000','0311f41c':'488b5728','0311f43e':'4c3bf0',
    '0311f530':'4c894728','0311f54f':'4c896730','0313217c':'4183f903',
    '0313218b':'488b8008010000','0313219c':'498b8080000000'}.items():
  if m['pins'][a]['hex']!=hexcode:raise EvidenceDrift('SEMANTIC_'+a)
 return {'level':'CURRENT_ORIGINAL_EXE_STATIC_ONLY','pins':len(m['pins']),
         'direct_calls':len(m['e8']),'branches':len(m['branches']),
         'queued_shift_identity_proven':False,'native_hook_authorized':False}
if __name__=='__main__':
 try:
  m=json.loads(Path(__file__).with_name('r80_focus_pins.json').read_text())
  print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
 except (IndexError,OSError,ValueError,struct.error) as e:
  print('FAIL_CLOSED',e);sys.exit(2)
