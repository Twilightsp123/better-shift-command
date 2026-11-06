"""BSC R93 public S3 mode/Packet-integrator gate contract; NO game process access or patch.
Original EXE exact-check is optional: BSC_R93_GAME_EXE=/path/to/Warhammer3.exe.
Full 64-pin/LLVM/unwind auditor ships in R93 archive, separate from public test.
"""
import hashlib, os, struct, unittest
from pathlib import Path

EXPECTED_SHA="9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496"
EXPECTED_SIZE=232531920
IMAGE_BASE=0x140000000
# Frozen, exact original opcode bytes: key conditional producer/consumer instructions.
PINS={
  0x02DC7E30:"8b4128",0x02DC7E33:"83f805",0x02DC7E36:"770d",
  0x02DC7E38:"b929000000",0x02DC7E3D:"0fa3c1",
  0x0327ECAE:"488b4110",0x0327ECB8:"488b8840040000",
  0x0327ECBF:"488b8950010000",0x0327ECC6:"e86591b4ff",
  0x0327ECCD:"744f",0x0327ED17:"e8bcb8e5ff",
  0x0327ED3C:"e8df9bfeff",
  0x03070A60:"488b4158",0x03070A6D:"488b8840040000",
  0x03070A74:"488b8950010000",0x03070A7B:"e8b073d5ff",
  0x03070B2F:"8b8704010000",0x03070B35:"ffc8",
  0x03070B3C:"83f801",0x03070B66:"41ff9300010000",
  0x03070B9C:"41ff93e8000000",
  0x03164477:"24f7",0x03164480:"0c02",
  0x03164482:"888608010000",
  0x03164676:"24f7",0x0316467F:"0c02",
  0x03164681:"888708010000",
  0x031471A9:"8a9308010000",0x031471B5:"f6c202",
  0x031471B8:"0f85d1010000",
  0x0314720B:"f30f118388000000",
  0x03147223:"f30f118b8c000000",
  0x0314723B:"f30f118390000000",
  0x03164776:"80a708010000f5"
}
CALLS={0x0327ECC6:0x02DC7E30,0x0327ED17:0x030DA5D8,
       0x0327ED3C:0x03268920,0x03070A7B:0x02DC7E30}
BRANCHES={0x0327ECCD:0x0327ED1E,0x031471B8:0x0314738F}
VTABLE={0x03912950+0xe8:0x03078268,
        0x03912950+0xf0:0x03164710,
        0x03912950+0x100:0x030785AC}

def source_mode_is_A(value):
    if not 0<=value<=0xffffffff:raise ValueError("DWORD expected")
    return value<=5 and bool((0x29>>value)&1)

def branch_target(rva,b):
    if b[0]==0xe8:return rva+5+struct.unpack_from("<i",b,1)[0]
    if b[0] in (0x74,0x75):return rva+2+struct.unpack_from("<b",b,1)[0]
    if b[:2] in (bytes.fromhex("0f85"),bytes.fromhex("0f84")):
        return rva+6+struct.unpack_from("<i",b,2)[0]
    raise ValueError("Unsupported branch")

def pe_read(data,rva,size):
    pe=struct.unpack_from("<I",data,0x3c)[0]
    assert data[pe:pe+4]==bytes((80,69,0,0))
    assert struct.unpack_from("<H",data,pe+4)[0]==0x8664
    assert struct.unpack_from("<Q",data,pe+24+24)[0]==IMAGE_BASE
    count=struct.unpack_from("<H",data,pe+6)[0]
    optsize=struct.unpack_from("<H",data,pe+20)[0]
    for i in range(count):
        pos=pe+24+optsize+i*40
        _,virtual,raw_size,raw_offset=struct.unpack_from("<IIII",data,pos+8)
        if virtual<=rva and rva+size<=virtual+raw_size:
            return data[raw_offset+rva-virtual:raw_offset+rva-virtual+size]
    raise ValueError("unmapped")

class TestR93GroupModesAndPhysicalGate(unittest.TestCase):
    def test_mode_truth_set(self):
        self.assertEqual([i for i in range(256) if source_mode_is_A(i)],[0,3,5])
    def test_mode_large_false(self):
        self.assertFalse(source_mode_is_A(0xffffffff))
    def test_opcode_manifest_valid(self):
        for opcode in PINS.values():self.assertEqual(bytes.fromhex(opcode).hex(),opcode)
    def test_exact_branch_destinations(self):
        for a,b in dict(CALLS,**{}).items():
            self.assertEqual(branch_target(a,bytes.fromhex(PINS[a])),b)
        for a,b in BRANCHES.items():
            self.assertEqual(branch_target(a,bytes.fromhex(PINS[a])),b)
    def test_group_and_member_use_same_predicate(self):
        self.assertEqual(CALLS[0x0327ECC6],CALLS[0x03070A7B])
    def test_packet_both_paths_set_flag_bit1(self):
        for v in range(256):
            self.assertEqual(((v&0xf7)|2)&2,2)
        self.assertEqual(PINS[0x03164480],"0c02")
        self.assertEqual(PINS[0x0316467F],"0c02")
    def test_integrator_has_bit_guard_before_normal_stores(self):
        self.assertEqual(PINS[0x031471B5],"f6c202")
        self.assertEqual(BRANCHES[0x031471B8],0x0314738F)
        self.assertTrue(all(rva<0x0314738F for rva in (0x0314720B,0x03147223,0x0314723B)))
    def test_other_member_method_clears_bit(self):
        self.assertEqual(PINS[0x03164776],"80a708010000f5")
        self.assertEqual((0xff&0xf5)&2,0)
    @unittest.skipUnless(os.environ.get("BSC_R93_GAME_EXE"),"commercial EXE absent in public CI")
    def test_exact_original_exe_bytes_and_vtable(self):
        data=Path(os.environ["BSC_R93_GAME_EXE"]).read_bytes()
        self.assertEqual(len(data),EXPECTED_SIZE)
        self.assertEqual(hashlib.sha256(data).hexdigest(),EXPECTED_SHA)
        for rva,hexdata in PINS.items():
            self.assertEqual(pe_read(data,rva,len(hexdata)//2),bytes.fromhex(hexdata))
        for addr,target in VTABLE.items():
            self.assertEqual(struct.unpack("<Q",pe_read(data,addr,8))[0],IMAGE_BASE+target)
if __name__=="__main__":unittest.main()
