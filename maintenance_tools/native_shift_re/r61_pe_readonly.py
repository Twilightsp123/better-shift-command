#!/usr/bin/env python3
from __future__ import annotations
import mmap,struct,subprocess,tempfile,re,bisect
from pathlib import Path
class PE:
 def __init__(self,path):
  self.fd=open(path,'rb');self.mm=mmap.mmap(self.fd.fileno(),0,access=mmap.ACCESS_READ)
  m=self.mm; pe=struct.unpack_from('<I',m,0x3c)[0];assert m[pe:pe+4]==b'PE\x00\x00'
  opt=pe+24; assert struct.unpack_from('<H',m,opt)[0]==0x20b
  self.imagebase=struct.unpack_from('<Q',m,opt+24)[0]
  self.sections=[];n=struct.unpack_from('<H',m,pe+6)[0];ns=struct.unpack_from('<H',m,pe+20)[0]
  for i in range(n):
   p=opt+ns+i*40
   name=m[p:p+8].rstrip(b'\0').decode(errors='replace')
   vs,va,rs,ro=struct.unpack_from('<IIII',m,p+8)
   self.sections.append((name,va,vs,rs,ro))
  er,el=struct.unpack_from('<II',m,opt+112+3*8)
  dat=self.read(er,el); self.runtime=[]
  for i in range(0,len(dat)-11,12):
   st,en,uw=struct.unpack_from('<III',dat,i)
   if 0<st<en:self.runtime.append((st,en,uw))
  self.runtime.sort();self.beg=[x[0] for x in self.runtime]
 def read(self,rva,n):
  for name,va,vs,rs,ro in self.sections:
   if va<=rva and rva+n<=va+max(vs,rs):
    pos=ro+rva-va;return self.mm[pos:pos+n]
  raise ValueError(f'unmapped rva {rva:x}+{n}')
 def owner(self,rva):
  i=bisect.bisect_right(self.beg,rva)-1
  if i>=0 and self.runtime[i][0]<=rva<self.runtime[i][1]:return self.runtime[i]
 def asm(self,rva,span=None):
  bounds=self.owner(rva)
  if span is None:
   if bounds is None:raise ValueError('no unwind function')
   lo,hi=bounds[:2]
  else:lo,hi=span
  if hi-lo>200000:raise ValueError('suspiciously large')
  with tempfile.NamedTemporaryFile() as f:
   f.write(self.read(lo,hi-lo)); f.flush()
   p=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64','-M','intel','--adjust-vma='+str(lo),f.name],capture_output=True,text=True,check=True)
  parsed=[]
  for line in p.stdout.splitlines():
   mat=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*([^\n]+)',line)
   if mat:
    at=int(mat.group(1),16); b=bytes.fromhex(mat.group(2));ins=mat.group(3).strip();parsed.append((at,b,ins))
  return parsed
 def calls(self,rva):
  return [(at,int(ins.split('0x')[1],16)) for at,b,ins in self.asm(rva) if ins.startswith('call') and b.startswith(b'\xe8')]
 def close(self):self.mm.close();self.fd.close()

if __name__=='__main__':
 import sys
 pe=PE(sys.argv[1]);print('base',hex(pe.imagebase));print('sections',pe.sections);print('runtimes',len(pe.runtime))
 for arg in sys.argv[2:]:
  r=int(arg,0);print('====',hex(r),'owner',pe.owner(r),'calls',len(pe.calls(r)) if pe.owner(r) else 'n/a')
  if pe.owner(r):
   for at,d in pe.calls(r):print(hex(at),'->',hex(d))
