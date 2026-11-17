"""BSC R96 public native chain contract: exact WH3 build, conditional only.
This is not a gameplay patch, a Shift runtime trace, or a live Hook.
Full LLVM/unwind 131-instruction audit is in offline R96 archive.
"""
import hashlib,os,struct,unittest
from pathlib import Path
SHA="9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496"
SIZE=232531920
BASE=0x140000000
PINS={
0x03037500:"458af1",0x030377A6:"4584f6",
0x030377BF:"418ad6",0x030377C2:"e845dcf1ff",
0x030377E8:"e88369fdff",0x030377ED:"e97c020000",
0x03037A69:"e8dab1ffff",
0x0300E185:"488d1574fb8f00",0x0300E18C:"488917",
0x0302AEDB:"4c8db3a0000000",0x0302B191:"4c897590",
0x0302B1AC:"488b5108",0x0302B1B3:"e8c065f0ff",
0x02F31791:"48895108",0x02F317BB:"488d054efbb800",
0x02F317C2:"488901",0x02F5B3F0:"488b4b08",
0x02F5B3F9:"488b89f8320000",0x02F5B400:"e89f383200",
0x03032C92:"e855ddfeff",0x03032C9A:"488bf8",
0x03032CC8:"e8e34cfeff",0x03032CCD:"488b8570020000",
0x03032CD4:"488bcf",0x03032CDF:"e838780a00"}
E8={0x030377C2:0x02F5540C,0x030377E8:0x0300E170,
0x03037A69:0x03032C48,0x0302B1B3:0x02F31778,
0x02F5B400:0x0327ECA4,0x03032C92:0x030209EC,
0x03032CC8:0x030179B0,0x03032CDF:0x030DA51C}
VTABLE={0x0390DD08:0x0302AE74,0x03AC1320:0x02F5B1E4}
def branch(src,h):
    b=bytes.fromhex(h)
    if b[0] not in (0xe8,0xe9): raise ValueError("not rel32")
    return src+5+struct.unpack_from("<i",b,1)[0]
def pe_get(buf,rva,count):
    pe=struct.unpack_from("<I",buf,0x3c)[0]
    assert buf[pe:pe+4]==bytes((80,69,0,0))
    assert struct.unpack_from("<H",buf,pe+4)[0]==0x8664
    assert struct.unpack_from("<Q",buf,pe+24+24)[0]==BASE
    n=struct.unpack_from("<H",buf,pe+6)[0]
    opts=struct.unpack_from("<H",buf,pe+20)[0]
    for i in range(n):
        s=pe+24+opts+40*i
        _,start,sz,raw=struct.unpack_from("<IIII",buf,s+8)
        if start<=rva and rva+count<=start+sz:
            return buf[raw+rva-start:raw+rva-start+count]
    raise ValueError("RVA not file backed")
class TestR96NativeOwner(unittest.TestCase):
    def test_all_hex_frozen(self):
        self.assertEqual(len(PINS),25)
        for h in PINS.values(): self.assertEqual(bytes.fromhex(h).hex(),h)
    def test_calls(self):
        for src,dst in E8.items():self.assertEqual(branch(src,PINS[src]),dst)
    def test_queued_issue_bypasses_immediate_builder(self):
        self.assertEqual(branch(0x030377ED,PINS[0x030377ED]),0x03037A6E)
        self.assertGreater(0x03037A6E,0x03037A69)
    def test_move_slot_to_short_task(self):
        self.assertEqual(E8[0x030377E8],0x0300E170)
        self.assertEqual(VTABLE[0x0390DD08],0x0302AE74)
        self.assertEqual(E8[0x0302B1B3],0x02F31778)
    def test_short_task_late_binds_group(self):
        self.assertEqual(PINS[0x02F31791],"48895108")
        self.assertEqual(PINS[0x02F5B3F0],"488b4b08")
        self.assertEqual(PINS[0x02F5B3F9],"488b89f8320000")
        self.assertEqual(E8[0x02F5B400],0x0327ECA4)
    def test_immediate_pipeline_does_not_equal_queue_event(self):
        self.assertEqual(E8[0x03032C92],0x030209EC)
        self.assertEqual(E8[0x03032CC8],0x030179B0)
        self.assertEqual(E8[0x03032CDF],0x030DA51C)
        self.assertNotEqual(0x03032C48,0x02F5B1E4)
    def test_no_runtime_claim(self):
        evidence={"same_shift_generation":False,"safe_live_sampler":False,"gameplay_fix":False}
        self.assertFalse(any(evidence.values()))
    @unittest.skipUnless(os.environ.get("BSC_R96_GAME_EXE"),
                         "commercial WH3 EXE absent from public CI")
    def test_exact_game(self):
        data=Path(os.environ["BSC_R96_GAME_EXE"]).read_bytes()
        self.assertEqual(len(data),SIZE)
        self.assertEqual(hashlib.sha256(data).hexdigest(),SHA)
        for rva,h in PINS.items():
            self.assertEqual(pe_get(data,rva,len(h)//2),bytes.fromhex(h))
        for rva,target in VTABLE.items():
            self.assertEqual(struct.unpack("<Q",pe_get(data,rva,8))[0],BASE+target)
if __name__=="__main__":unittest.main()
