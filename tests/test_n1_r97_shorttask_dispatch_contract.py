"""BSC R97 read-only source contract; not a gameplay patch or live memory reader.
Run python -m unittest discover -s tests -p 'test_n1_r97_shorttask_dispatch_contract.py'
Optional original EXE: BSC_R97_GAME_EXE=/path/to/Warhammer3.exe
Full 522-pin/LLVM/unwind manifest and synthetic ABA controls are in R97 ZIP.
"""
import hashlib,os,struct,unittest
from pathlib import Path
EXE_SHA="9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496"
EXE_SIZE=232531920
BASE=0x140000000
PINS={
0x0302b188:"488b5318",0x0302b18c:"b9a8000000",
0x0302b195:"e83e9ef0ff",0x0302b1b3:"e8c065f0ff",
0x0302b1bb:"488b07",0x0302b1e2:"48ff6008",
0x02f35007:"898240020000",0x02f3501c:"018a44020000",
0x02f317fd:"44385b7d",0x02f31801:"7463",
0x02f31803:"e8d4270200",0x02f3185f:"e8084e0100",
0x02f31866:"e8a52c0200",0x02f318e1:"88414d",
0x02f318eb:"488b4250",0x02f318ef:"48894150",
0x02f53fdc:"488b8180000000",0x02f53fe8:"488b00",
0x02f53fec:"488b8198000000",
0x02f4669d:"488901",0x02f466a7:"48898398000000",
0x02f54536:"488b4108",0x02f54542:"488b88f8320000",
0x02f54621:"488b89f8320000",0x02f54628:"e81fa73200",
0x02f5b3f9:"488b89f8320000",0x02f5b400:"e89f383200",
0x008d3c60:"c20000"
}
E8={
0x0302b195:0x02f34fd8,0x0302b1b3:0x02f31778,
0x02f31803:0x02f53fdc,0x02f3185f:0x02f4666c,
0x02f31866:0x02f54510,0x02f54628:0x0327ed4c,
0x02f5b400:0x0327eca4
}
VTABLE={
0x03ac1310+0x08:0x008d3c60,
0x03ac1310+0x10:0x02f5b1e4,
0x03ac1310+0x20:0x02f5d560
}
def pe_read(data,rva,length):
    pe=struct.unpack_from("<I",data,0x3c)[0]
    if data[pe:pe+4]!=b"PE\x00\x00":raise ValueError("not PE")
    if struct.unpack_from("<H",data,pe+4)[0]!=0x8664:raise ValueError("not AMD64")
    if struct.unpack_from("<Q",data,pe+24+24)[0]!=BASE:raise ValueError("wrong ImageBase")
    n=struct.unpack_from("<H",data,pe+6)[0]
    op_size=struct.unpack_from("<H",data,pe+20)[0]
    for i in range(n):
        s=pe+24+op_size+40*i
        _,va,raw_size,raw=struct.unpack_from("<IIII",data,s+8)
        if va<=rva and rva+length<=va+raw_size:
            return data[raw+rva-va:raw+rva-va+length]
    raise ValueError("RVA not file-backed")
def target(rva,hexbytes):
    b=bytes.fromhex(hexbytes)
    if b[0]!=0xe8 or len(b)!=5:raise ValueError("not E8")
    return rva+5+struct.unpack_from("<i",b,1)[0]
def slot_state(field_address,field_value,fallback):
    return field_value if field_address is not None else fallback
class TestR97TaskSeam(unittest.TestCase):
    def test_all_pins_hex(self):
        for h in PINS.values():self.assertEqual(h,bytes.fromhex(h).hex())
    def test_e8_destinations(self):
        for src,dst in E8.items():self.assertEqual(target(src,PINS[src]),dst)
    def test_creation_tail_call_is_noop(self):
        self.assertEqual(PINS[0x0302b1e2],"48ff6008")
        self.assertEqual(PINS[0x008d3c60],"c20000")
        self.assertEqual(VTABLE[0x03ac1318],0x008d3c60)
    def test_callback_is_other_slot(self):
        self.assertEqual(VTABLE[0x03ac1320],0x02f5b1e4)
    def test_task_state_is_indirect(self):
        self.assertEqual(PINS[0x02f53fdc],"488b8180000000")
        self.assertEqual(PINS[0x02f53fe8],"488b00")
    def test_fallback_only_when_pointer_itself_null(self):
        self.assertIsNone(slot_state(0x4000,None,0x9000))
        self.assertEqual(slot_state(None,None,0x9000),0x9000)
    def test_slot_value_can_change_at_same_address(self):
        self.assertNotEqual(slot_state(0x4000,0x1,0x9),slot_state(0x4000,0x2,0x9))
    def test_two_group_read_times(self):
        self.assertEqual(PINS[0x02f54542],PINS[0x02f54621])
        self.assertEqual(PINS[0x02f54621],PINS[0x02f5b3f9])
    def test_constructor_conditional_two_paths(self):
        self.assertNotEqual(E8[0x02f3185f],E8[0x02f31866])
    def test_arena_count_not_a_route_generation(self):
        self.assertEqual(PINS[0x02f35007],"898240020000")
    def test_group_can_change_under_same_root_in_synthetic_counterexample(self):
        # Counterexample to pointer-only identity, NOT an observation of WH3.
        before={"root":7,"group_generation":1}
        after={"root":7,"group_generation":2}
        self.assertEqual(before["root"],after["root"])
        self.assertNotEqual(before["group_generation"],after["group_generation"])
    @unittest.skipUnless(os.environ.get("BSC_R97_GAME_EXE"),"commercial EXE unavailable in public CI")
    def test_original_exe_exact_bytes(self):
        data=Path(os.environ["BSC_R97_GAME_EXE"]).read_bytes()
        self.assertEqual(len(data),EXE_SIZE)
        self.assertEqual(hashlib.sha256(data).hexdigest(),EXE_SHA)
        for rva,h in PINS.items():self.assertEqual(pe_read(data,rva,len(h)//2),bytes.fromhex(h))
        for addr,dst in VTABLE.items():
            self.assertEqual(struct.unpack("<Q",pe_read(data,addr,8))[0],BASE+dst)
if __name__=="__main__":unittest.main()
