#!/usr/bin/env python3
"""Read-only, fixed-EXE BSC packet-path regression. Standard library only."""
import hashlib, pathlib, struct, sys
EXPECTED='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'Warhammer3.exe')
b=p.read_bytes()
if hashlib.sha256(b).hexdigest()!=EXPECTED:
 raise ValueError('EXE SHA mismatch; fail-closed')
pe=struct.unpack_from('<I',b,0x3c)[0]
if b[pe:pe+4]!=b'PE\0\0':
 raise ValueError('Invalid PE signature')
n=struct.unpack_from('<H',b,pe+6)[0]; opt=pe+24
if struct.unpack_from('<H',b,opt)[0]!=0x20b:
 raise ValueError('Expected PE32+ image')
if struct.unpack_from('<Q',b,opt+24)[0]!=0x140000000:
 raise ValueError('Unexpected PE ImageBase')
size_opt=struct.unpack_from('<H',b,pe+20)[0]
sects=[]
for i in range(n):
 off=opt+size_opt+40*i
 name=b[off:off+8].rstrip(b'\0').decode('ascii','replace')
 vs,va,rs,rp=struct.unpack_from('<IIII',b,off+8)
 sects.append((name,va,max(vs,rs),rp,rs))
def read(rva,n):
 for name,va,size,rp,rs in sects:
  if va<=rva and rva+n<=va+rs:
   if name!='.00cfg':
    raise ValueError(f'RVA {rva:x} outside verified executable code')
   return b[rp+rva-va:rp+rva-va+n]
 raise AssertionError(f'RVA not in raw section: {rva:x}')
def check(rva,hexx,description):
 exp=bytes.fromhex(hexx)
 got=read(rva,len(exp))
 if got!=exp:
  raise ValueError(f'{description}: byte mismatch RVA 0x{rva:x}: {got.hex()} != {exp.hex()}')
 print(f'PASS 0x{rva:08X}: {description}')
# Instruction signatures (not a whole-control-flow proof). Each keyed to fixed SHA.
check(0x0328153d,'48 8b 41 78','aux+0x78 read')
check(0x03281554,'48 8b 40 70','node+0x70 read')
check(0x032815c5,'e8 5a 45 fe ff','call typed member-packet builder 0x03265B24')
check(0x03265bbe,'41 ff 52 48','formation strategy virtual+0x48')
check(0x03265d3f,'ff 90 68 03 00 00','member virtual+0x368 delivery')
check(0x02f5f8bd,'c6 43 50 26','0x26 packet ctor stores flags')
check(0x02f5f940,'80 c9 06','variable packet ctor OR 0x06')
check(0x02f5f95e,'41 88 4a 50','variable packet ctor saves combined flags')
check(0x0306ba2f,'f6 42 50 20','member receiver tests bit 0x20')
check(0x0306ba5b,'e8 68 3d ef ff','conditional call 0x02F5F7C8')
print('PASS 10/10 guarded machine-code assertions. No gameplay claim.')
