"""R95 focused original WH3 machine-code contract. Commercial EXE optional.

Private R95 archive has complete 120/120 LLVM and PE unwind validation.
This public suite is a condensed byte/branch and 2-record-type regression.
"""
import hashlib,os,struct,unittest
from pathlib import Path
SHA="9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496"
SIZE=232531920
BASE=0x140000000
PINS={
0x03121F5B:"488b4910",0x03122153:"488b4918",
0x03121F64:"4883c118",0x0312215C:"4883c118",
0x03121F62:"740b",0x0312215A:"740b",
0x03121F68:"e8fbb6e1ff",0x03122160:"e803b5e1ff",
0x0305A061:"488d8fe0010000",0x0305A06D:"e8e27e0c00",
0x0305A05B:"0f8644010000",
0x03070B52:"741b",0x03070B54:"e8f3150b00",
0x03070B66:"41ff9300010000",0x03070B6F:"e8d8150b00",
0x03070B9C:"41ff93e8000000",
0x0311E6CA:"0f1187e0010000",0x0311E6E8:"f20f118ff0010000",
0x02F3D67D:"f30f594120",0x02F3D6A3:"f30f595124",
0x02F3D685:"f30f594928",
0x02F3D6B9:"f30f59412c",0x02F3D6A8:"f30f595930",0x02F3D6CE:"f30f594934",
0x02F3D6B4:"f30f596138",0x02F3D69E:"f30f59713c",0x02F3D6C5:"f30f596940"}
CALLS={0x03121F68:0x02F3D668,0x03122160:0x02F3D668,
       0x03070B54:0x0312214C,0x03070B6F:0x0312214C,
       0x0305A06D:0x03121F54}
JCC={0x03121F62:0x03121F6F,0x0312215A:0x03122167,
     0x03070B52:0x03070B6F,0x0305A05B:0x0305A1A5}

def target(addr,raw):
    b=bytes.fromhex(raw)
    if b[0]==0xe8:return addr+5+struct.unpack_from("<i",b,1)[0]
    if b[0] in (0x74,0x75):return addr+2+struct.unpack_from("<b",b,1)[0]
    if b[:2] in (b"\x0f\x86",b"\x0f\x85",b"\x0f\x84"):
        return addr+6+struct.unpack_from("<i",b,2)[0]
    raise ValueError("unexpected opcode")

def read_rva(buf,addr,size):
    pe=struct.unpack_from("<I",buf,0x3c)[0]
    if buf[pe:pe+4]!=bytes((80,69,0,0)):raise ValueError("invalid PE")
    if struct.unpack_from("<H",buf,pe+4)[0]!=0x8664:raise ValueError("non AMD64")
    if struct.unpack_from("<Q",buf,pe+24+24)[0]!=BASE:raise ValueError("wrong base")
    n=struct.unpack_from("<H",buf,pe+6)[0]
    op_size=struct.unpack_from("<H",buf,pe+20)[0]
    for i in range(n):
        s=pe+24+op_size+40*i
        _,rva,raw_size,raw=struct.unpack_from("<IIII",buf,s+8)
        if rva<=addr and addr+size<=rva+raw_size:
            return buf[raw+addr-rva:raw+addr-rva+size]
    raise ValueError("RVA not file backed")

class TestR95SourceBoundaries(unittest.TestCase):
    def test_frozen_pins(self):
        for h in PINS.values():self.assertEqual(bytes.fromhex(h).hex(),h)
    def test_different_reference_offsets(self):
        self.assertNotEqual(PINS[0x03121F5B],PINS[0x03122153])
        self.assertEqual(PINS[0x03121F5B],"488b4910")
        self.assertEqual(PINS[0x03122153],"488b4918")
    def test_two_resolvers_one_affine_function(self):
        self.assertEqual(target(0x03121F68,PINS[0x03121F68]),0x02F3D668)
        self.assertEqual(target(0x03122160,PINS[0x03122160]),0x02F3D668)
    def test_five_e8_and_four_branches(self):
        for r,dst in CALLS.items():self.assertEqual(target(r,PINS[r]),dst)
        for r,dst in JCC.items():self.assertEqual(target(r,PINS[r]),dst)
    def test_steering_reads_actual_member_goal(self):
        self.assertEqual(PINS[0x0305A061],"488d8fe0010000")
    def test_packet_receiver_both_branches_resolve(self):
        self.assertEqual(CALLS[0x03070B54],CALLS[0x03070B6F])
    def test_setter_copies_goal_and_reference(self):
        self.assertEqual(PINS[0x0311E6CA],"0f1187e0010000")
        self.assertEqual(PINS[0x0311E6E8],"f20f118ff0010000")
    def test_basis_has_all_nine_scalar_multiplications(self):
        self.assertEqual(len([r for r in PINS if 0x02F3D668<=r<0x02F3D700]),9)
    @unittest.skipUnless(os.environ.get("BSC_R95_GAME_EXE"),
                         "commercial WH3 EXE not in public CI")
    def test_original_exe_exact_hash_and_pins(self):
        buf=Path(os.environ["BSC_R95_GAME_EXE"]).read_bytes()
        self.assertEqual(len(buf),SIZE)
        self.assertEqual(hashlib.sha256(buf).hexdigest(),SHA)
        for r,h in PINS.items():self.assertEqual(read_rva(buf,r,len(h)//2),bytes.fromhex(h))
if __name__=="__main__":unittest.main()
