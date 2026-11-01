"""BSC R89: public typed-receiver static contract; optional exact WH3 EXE checks.
Run: python -m unittest discover -s tests -p 'test_n1_r89_typed_receiver_contract.py'
For exact-file checks set BSC_R89_GAME_EXE to the original game EXE. No Hook.
"""
import hashlib
import mmap
import os
import struct
import unittest

EXPECTED_SHA = "9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496"
EXPECTED_SIZE = 232531920
BASE = 0x140000000
PINS = {
  0x02D9904E: "4c8db740040000",
  0x02D99070: "e88f0f0000",
  0x02D990A6: "498906",
  0x02D9A02F: "488bf9",
  0x02D9A357: "b9e8370000",
  0x02D9A370: "488bc8",
  0x02D9A373: "e888640000",
  0x02D9A381: "488987f0000000",
  0x02D9AD5C: "488bc7",
  0x02DA09DC: "488d87d8010000",
  0x02DA0FDF: "488d8798080000",
  0x02DA1AD7: "488d8f981f0000",
  0x02DA2065: "488db718370000",
  0x02DA209D: "488b4540",
  0x02DA2107: "488d0d3afad000",
  0x02DA210E: "488988d8010000",
  0x02DD06F0: "48895c2410",
  0x02DD070B: "4c8bf2",
  0x02DD0753: "ff5010",
  0x02DD0763: "ff5008",
  0x0300BC91: "488b8840040000",
  0x0300BC98: "488b89f0000000",
  0x0300BC9F: "4881c198080000",
  0x0300BCA6: "e845f1c2fe",
  0x0308529D: "498d8dd8010000",
  0x030852A7: "ff5010",
}
E8 = {0x02D99070: 0x02D9A004, 0x02D9A373: 0x02DA0800, 0x0300BCA6: 0x01C3ADF0}
OWNERS = {
  0x02D99070: (0x02D98420,0x02D99A8B),
  0x02D9A381: (0x02D9A004,0x02D9AD82),
  0x02DA210E: (0x02DA0800,0x02DA2CD6),
  0x02DD06F0: (0x02DD06F0,0x02DD07DF),
  0x0300BC91: (0x0300B178,0x0300BDD6),
  0x030852A7: (0x03085114,0x030852C8),
}
class PE:
  def __init__(self,b):
    self.b=b
    pe=struct.unpack_from("<I",b,0x3c)[0]
    assert b[pe:pe+4]==bytes((80,69,0,0))
    machine,n,_,_,_,optlen,_=struct.unpack_from("<HHIIIHH",b,pe+4)
    assert machine==0x8664
    self.base=struct.unpack_from("<Q",b,pe+24+24)[0]
    self.sect=[]
    s0=pe+24+optlen
    for i in range(n):
      s=s0+i*40
      sz,rva,rawsz,raw=struct.unpack_from("<IIII",b,s+8)
      self.sect.append((rva,rawsz,raw))
    opt=pe+24
    exc_rva,exc_sz=struct.unpack_from("<II",b,opt+112+24)
    self.exc_rva,self.exc_sz=exc_rva,exc_sz
  def at(self,rva,n):
    for va,size,raw in self.sect:
      if va<=rva<va+size: return self.b[raw+rva-va:raw+rva-va+n]
    raise ValueError(hex(rva))
  def owner(self,rva):
    exc=self.at(self.exc_rva,self.exc_sz)
    lo,hi=0,len(exc)//12
    while lo<hi:
      mid=(lo+hi)//2
      beg,end,_=struct.unpack_from("<III",exc,mid*12)
      if rva<beg:hi=mid
      elif rva>=end:lo=mid+1
      else:return beg,end
    return None

class TestR89TypedReceiver(unittest.TestCase):
  def test_pins_are_bytes(self):
    self.assertEqual(len(PINS),26)
    for h in PINS.values(): self.assertEqual(bytes.fromhex(h).hex(),h)
  def test_e8_destinations(self):
    for rva,target in E8.items():
      b=bytes.fromhex(PINS[rva])
      self.assertEqual(rva+5+struct.unpack_from("<i",b,1)[0],target)
  def test_public_constructor_contract(self):
    self.assertEqual(PINS[0x02D990A6],"498906")
    self.assertEqual(PINS[0x02D9A381],"488987f0000000")
  def test_vtable_lea_arithmetic(self):
    a=0x02DA2107; b=bytes.fromhex(PINS[a])
    self.assertEqual(a+len(b)+struct.unpack_from("<i",b,3)[0],0x03AB1B48)
  def test_event_dispatch_boundary(self):
    self.assertEqual(PINS[0x02DD0753],"ff5010")
    self.assertEqual(PINS[0x02DD0763],"ff5008")
  def test_owner_bounds_manifest(self):
    for rva,(a,b) in OWNERS.items():self.assertLessEqual(a,rva);self.assertLess(rva,b)
  @unittest.skipUnless(os.environ.get("BSC_R89_GAME_EXE"),"commercial EXE absent in public CI")
  def test_original_exe_identity_and_instructions(self):
    with open(os.environ["BSC_R89_GAME_EXE"],"rb") as f:
      b=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
      try:
        self.assertEqual(len(b),EXPECTED_SIZE)
        self.assertEqual(hashlib.sha256(b).hexdigest(),EXPECTED_SHA)
        pe=PE(b);self.assertEqual(pe.base,BASE)
        for rva,h in PINS.items():self.assertEqual(pe.at(rva,len(h)//2),bytes.fromhex(h))
        for rva,bounds in OWNERS.items():self.assertEqual(pe.owner(rva),bounds)
        self.assertEqual(struct.unpack("<Q",pe.at(0x03AB1B48+16,8))[0],BASE+0x02DD06F0)
      finally:b.close()
if __name__=="__main__":unittest.main()
