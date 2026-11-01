"""BSC R88 static contract: contact receiver provenance, not a gameplay patch.
Run with python -m unittest tests.test_n1_r88_contact_receiver_contract.
Optional exact-file check: BSC_R88_GAME_EXE=/path/to/Warhammer3.exe.
"""
import hashlib
import mmap
import os
import struct
import unittest

EXPECTED_SHA = "9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496"
EXPECTED_SIZE = 232531920
PINS = {
  0x03059CCA:"4c8d6f58",  # R13=&entry_member+58
  0x0305A7B5:"498b4500",  # C=[R13]
  0x0305A7C1:"4c8bc6",    # participant2=RSI
  0x0305A7C9:"488bcf",    # participant1=current RDI
  0x0305A7CC:"488b9040040000", # G=[C+440]
  0x0305A7F4:"488b92f0000000", # P=[G+F0]
  0x0305A800:"e80fa90200", # E8 contact entry
  0x03085147:"4c8bea",    # R13=P
  0x0308514A:"488bd9",    # RBX=contact participant1
  0x0308529D:"498d8dd8010000", # this=P+1D8
  0x030852A4:"488b01",    # vptr=[this]
  0x030852A7:"ff5010",    # vcall [vptr+10]
}

def raw_offset(b,rva):
    pe=struct.unpack_from("<I",b,0x3c)[0]
    if b[pe:pe+4]!=b"PE\\x00\\x00": raise ValueError("invalid PE")
    n=struct.unpack_from("<H",b,pe+6)[0]
    opt=struct.unpack_from("<H",b,pe+20)[0]
    for i in range(n):
        pos=pe+24+opt+i*40
        _,start,size,off=struct.unpack_from("<IIII",b,pos+8)
        if start<=rva<start+size: return off+rva-start
    raise ValueError("RVA not mapped: "+hex(rva))

class TestR88ContactReceiverContract(unittest.TestCase):
    def test_causal_edge_not_claimed(self):
        self.assertNotIn("MOTOR_CAUSAL_EDGE_PROVEN",__doc__)
    def test_pins_well_formed(self):
        for h in PINS.values(): self.assertEqual(bytes.fromhex(h).hex(),h)
    def test_branch_call_target_arithmetic(self):
        insn=bytes.fromhex(PINS[0x0305A800])
        self.assertEqual(insn[0],0xe8)
        self.assertEqual(0x0305A800+5+struct.unpack("<i",insn[1:])[0],0x03085114)
    @unittest.skipUnless(os.environ.get("BSC_R88_GAME_EXE"), "commercial EXE not in public CI")
    def test_exact_original_exe(self):
        with open(os.environ["BSC_R88_GAME_EXE"],"rb") as f:
            mm=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
            try:
                self.assertEqual(len(mm),EXPECTED_SIZE)
                self.assertEqual(hashlib.sha256(mm).hexdigest(),EXPECTED_SHA)
                for rva,h in PINS.items():
                    pos=raw_offset(mm,rva)
                    self.assertEqual(mm[pos:pos+len(h)//2].hex(),h)
            finally: mm.close()

if __name__=="__main__": unittest.main()