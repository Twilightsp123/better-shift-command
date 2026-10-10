"""Original WH3 PE instruction-byte guards. Never writes to EXE."""
import hashlib,os,struct,unittest
from pathlib import Path
SHA='518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
BASE=0x140000000
SITE=0x0304459d
END=0x030445ae
ORIGINAL=bytes.fromhex('ff4618498d4e18498b4618488bd6ff5048')
PATCH=bytes.fromhex('e90c000000')
GUARDS={
 'initial_move_state_null':(0x030090e7,'4883a7a000000000'),
 'native_handoff_eligible':(0x03044596,'ff503884c0'),
 'native_pop_after_handoff':(0x030445b1,'e85ab7f0ff'),
 'native_reprocess':(0x030445d3,'e8d8edffff'),
 'move_worker_state_reuse':(0x03025de1,'4d8b1e4d85db'),
}
def get_raw_executable(exe,rva,n):
 with exe.open('rb') as stream:
  b=stream.read()
 nt=struct.unpack_from('<I',b,0x3c)[0]
 assert b[:2]==b'MZ' and b[nt:nt+4]==b'PE\0\0'
 machine,count=struct.unpack_from('<HH',b,nt+4)
 assert machine==0x8664
 opt=nt+24;osz=struct.unpack_from('<H',b,nt+20)[0]
 assert struct.unpack_from('<H',b,opt)[0]==0x20b and struct.unpack_from('<Q',b,opt+24)[0]==BASE
 for i in range(count):
  q=opt+osz+i*40
  _,base,size,raw=struct.unpack_from('<IIII',b,q+8)
  flags=struct.unpack_from('<I',b,q+36)[0]
  if base<=rva and rva+n<=base+size and flags&0x20000000:
   return bytes(b[raw+rva-base:raw+rva-base+n])
 raise ValueError('RVA_NOT_EXECUTABLE')
def verify(exe):
 if hashlib.sha256(exe.read_bytes()).hexdigest()!=SHA:raise ValueError('EXE_SHA_MISMATCH')
 if get_raw_executable(exe,SITE,17)!=ORIGINAL:raise ValueError('ORIGINAL_17_BYTE_GUARD')
 for label,(rva,hexbytes) in GUARDS.items():
  if get_raw_executable(exe,rva,len(hexbytes)//2)!=bytes.fromhex(hexbytes):
   raise ValueError('OPCODE_GUARD_'+label)
 assert SITE+5+struct.unpack('<i',PATCH[1:])[0]==END
 return True
class Contracts(unittest.TestCase):
 def test_relative_jump(self):self.assertEqual(SITE+5+struct.unpack('<i',PATCH[1:])[0],END)
 def test_original_reference_increment(self):self.assertEqual(ORIGINAL[:3],bytes.fromhex('ff4618'))
 def test_original_native_transfer(self):self.assertEqual(ORIGINAL[-3:],bytes.fromhex('ff5048'))
 def test_5_original_machine_guards(self):self.assertEqual(len(GUARDS),5)
 def test_wrong_hash_refused(self):
  import tempfile
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/'fake.exe';p.write_bytes(b'MZ')
   with self.assertRaisesRegex(ValueError,'EXE_SHA_MISMATCH'):verify(p)
 def test_original_exe_when_provided(self):
  value=os.environ.get('WH3_903_EXE')
  if value:self.assertTrue(verify(Path(value)))
if __name__=='__main__':unittest.main()
