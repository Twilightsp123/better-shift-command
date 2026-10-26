#!/usr/bin/env python3
"""R76 focused SHA-gated WH3 static verifier. NO process access or live Hook."""
import hashlib,json,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
class StaticDrift(ValueError):pass
def verify(data,m):
 if len(data)!=m['size'] or hashlib.sha256(data).hexdigest()!=m['sha256']:
  raise StaticDrift('SHA_OR_SIZE_FAIL_CLOSED')
 if data[:2]!=b'MZ':raise StaticDrift('NOT_MZ')
 pe=struct.unpack_from('<I',data,0x3c)[0]
 if not 0x40<=pe<0x1000 or data[pe:pe+4]!=b'PE\x00\x00':raise StaticDrift('NOT_PE')
 if struct.unpack_from('<H',data,pe+4)[0]!=0x8664 or struct.unpack_from('<H',data,pe+24)[0]!=0x20b:raise StaticDrift('NOT_AMD64')
 if struct.unpack_from('<Q',data,pe+48)[0]!=0x140000000:raise StaticDrift('IMAGEBASE')
 n=struct.unpack_from('<H',data,pe+6)[0];opt=struct.unpack_from('<H',data,pe+20)[0];sections=[]
 for k in range(n):
  p=pe+24+opt+40*k
  _,r,z,o=struct.unpack_from('<IIII',data,p+8)
  if o+z>len(data):raise StaticDrift('SECTION_RANGE')
  sections.append((r,z,o))
 def rd(r,z):
  for start,length,o in sections:
   if start<=r and r+z<=start+length:return data[o+r-start:o+r-start+z]
  raise StaticDrift('RVA_RANGE')
 for site,opcode in m['focused_pins'].items():
  expected=bytes.fromhex(opcode)
  if rd(int(site,16),len(expected))!=expected:raise StaticDrift('OPCODE_'+site)
 for site,dest in m['e8_edges'].items():
  r=int(site,16);b=rd(r,5)
  if b[0]!=0xe8 or r+5+struct.unpack_from('<i',b,1)[0]!=int(dest,16):
   raise StaticDrift('E8_'+site)
 for site,dest in m['branches'].items():
  r=int(site,16);b=bytes.fromhex(m['focused_pins'][site])
  if len(b)==2 and b[0] in (0x74,0x75,0x76):
   target=r+2+struct.unpack('<b',b[1:])[0]
  elif len(b)==6 and b[0]==0x0f and 0x80<=b[1]<=0x8f:
   target=r+6+struct.unpack_from('<i',b,2)[0]
  else:raise StaticDrift('JCC_ENCODING_'+site)
  if target!=int(dest,16):raise StaticDrift('JCC_TARGET_'+site)
 for off,dest in m['member_vmethods'].items():
  a=int(m['member_vtable'],16)+int(off,16)
  if struct.unpack('<Q',rd(a,8))[0]!=0x140000000+int(dest,16):
   raise StaticDrift('VTABLE_'+off)
 return {'grade':'FOCUSED_CURRENT_EXE_STATIC','pins':len(m['focused_pins']),
         'e8':len(m['e8_edges']),'branches':len(m['branches']),
         'member_vtable_slots':len(m['member_vmethods']),
         'goal_motion_same_shift_proven':False,'gameplay_patch_authorized':False}
def synthetic_partition(velocity_sq,neighbor_threshold_sq,bit2,bit4):
 if type(bit2)!=bool or type(bit4)!=bool or any(type(v) not in (int,float) or not 0<=v<1e9 for v in (velocity_sq,neighbor_threshold_sq)):
  raise ValueError('INVALID_SYNTHETIC')
 return {'world_goal_branch':velocity_sq>neighbor_threshold_sq,
         'integrator_branch':('complex' if bit2 else 'direct' if bit4 else 'skip'),
         'same_shift_instance_proven':False}
if __name__=='__main__':
 try:
  m=json.loads((HERE/'r76_focused_pins.json').read_text())
  print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
 except (IndexError,OSError,ValueError,struct.error) as e:
  print('FAIL_CLOSED',e);sys.exit(2)
