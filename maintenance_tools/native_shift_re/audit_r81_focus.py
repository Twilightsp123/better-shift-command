#!/usr/bin/env python3
"""R81 constructor-owner SHA/PE verifier. Offline only; never reads game process."""
import hashlib,json,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
class Drift(ValueError):pass
def context_model(member_context,root_context,member_epoch=None,task_epoch=None):
 if type(member_context)!=str or not member_context:raise Drift('MEMBER_CONTEXT_REQUIRED')
 return {'context_same':member_context==root_context,
         'epochs_match':member_epoch is not None and task_epoch is not None and member_epoch==task_epoch,
         'queued_shift_same_instance_proven':False,'no_unsafe_game_hook':True}
def verify(data,m):
 if len(data)!=m['size'] or hashlib.sha256(data).hexdigest()!=m['sha256']:
  raise Drift('EXE_SHA_SIZE_FAIL_CLOSED')
 if data[:2]!=b'MZ':raise Drift('MZ')
 pe=struct.unpack_from('<I',data,0x3c)[0]
 if pe<0x40 or pe>=0x1000 or data[pe:pe+4]!=b'PE\0\0':raise Drift('PE')
 if struct.unpack_from('<H',data,pe+4)[0]!=0x8664 or struct.unpack_from('<H',data,pe+24)[0]!=0x20b:raise Drift('AMD64')
 if struct.unpack_from('<Q',data,pe+48)[0]!=0x140000000:raise Drift('BASE')
 n=struct.unpack_from('<H',data,pe+6)[0];opt=struct.unpack_from('<H',data,pe+20)[0];sections=[]
 for i in range(n):
  j=pe+24+opt+40*i;_,rv,z,off=struct.unpack_from('<IIII',data,j+8)
  if off+z>len(data):raise Drift('SECTION')
  sections.append((rv,z,off))
 def read(r,n):
  for v,z,o in sections:
   if v<=r and r+n<=v+z:return data[o+r-v:o+r-v+n]
  raise Drift('RVA_BOUNDS')
 ex,esize=struct.unpack_from('<II',data,pe+24+112+3*8)
 funcs={}
 for k in range(esize//12):
  a,z,u=struct.unpack('<III',read(ex+k*12,12));funcs[a]=z
 for name,(start,end) in m['functions'].items():
  if funcs.get(int(start,16))!=int(end,16):raise Drift('UNWIND_'+name)
 for addr,obj in m['pins'].items():
  r=int(addr,16);v=bytes.fromhex(obj['hex'])
  a,z=m['functions'][obj['owner']]
  if r<int(a,16) or r+len(v)>int(z,16) or read(r,len(v))!=v:raise Drift('PIN_'+addr)
 for addr,target in m['e8'].items():
  r=int(addr,16);b=read(r,5)
  if b[0]!=0xe8 or r+5+struct.unpack_from('<i',b,1)[0]!=int(target,16):raise Drift('E8_'+addr)
 for addr,h in {'03052f62':'488b4358','03052f66':'48898318070000','03052f6d':'48898320070000',
  '03052f82':'4c89a338070000','03052f89':'4c89a340070000',
  '0305313c':'f30f118310090000','0305315c':'4c89a320090000',
  '03076f7e':'488db918070000','030770cd':'488b8338070000',
  '030771ec':'4c8d8b10090000','0308a321':'0f108920090000',
  '03054b2a':'488b8950010000','03054b3b':'48899110090000',
  '030861f5':'488b9150010000','0308620d':'48898a10090000'}.items():
  if m['pins'][addr]['hex']!=h:raise Drift('SEMANTIC_'+addr)
 return {'grade':'CURRENT_EXE_STATIC_ONLY','pin_count':len(m['pins']),'e8_count':len(m['e8']),
   'constructor_member_context_source_proven':True,'runtime_member_reference_writer_proven':False,
   'queued_shift_instance_proven':False,'gameplay_patch_authorized':False}
if __name__=='__main__':
 try:
  m=json.loads(Path(__file__).with_name('r81_focus_pins.json').read_text())
  print(json.dumps(verify(Path(sys.argv[1]).read_bytes(),m),indent=2))
 except (IndexError,OSError,ValueError,struct.error) as e:
  print('FAIL_CLOSED',e);sys.exit(2)
