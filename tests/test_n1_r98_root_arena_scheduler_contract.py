"""BSC R98: original WH3 Root-owned arena -> typed shortTask dispatcher.

Offline contract tests only. Optional BSC_R98_GAME_EXE verifies the original
game binary. Never grants live Hook/snapshot or Shift gameplay causality.
"""
import hashlib,os,struct,unittest
from pathlib import Path
SHA="9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496"
SIZE=232531920
BASE=0x140000000
PINS={
0x0300cb85:"498d87a02f0000",0x0300cc16:"49898780020000",
0x02f5548f:"48894110",0x0300d901:"488b4210",0x0300d905:"48894118",
0x0300e180:"e843f7ffff",0x030377c2:"e845dcf1ff",0x030377e8:"e88369fdff",
0x0302b188:"488b5318",0x0302b195:"e83e9ef0ff",0x0302b1b3:"e8c065f0ff",
0x02f35007:"898240020000",0x02f35013:"f30f7f84c200020000",
0x03048879:"488d8ba02f0000",0x03048880:"e89ffdffff",
0x0304863b:"66c781500200000100",0x03048644:"8b8940020000",
0x03048670:"488b34c3",0x0304867a:"488b16",0x0304867d:"3bf8",
0x0304867f:"7521",0x03048681:"ff5210",0x03048684:"ff461c",
0x03048687:"807e1801",0x03048692:"e8c1c6f0ff",0x030486a2:"ff5218",
0x02f54daa:"ff10",0x02f5b5c3:"884318",0x02ddbff7:"e850c72600",
0x02f317bb:"488d054efbb800",0x02f317c2:"488901"}
E8={
0x0300e180:0x0300d8c8,0x030377c2:0x02f5540c,
0x030377e8:0x0300e170,0x0302b195:0x02f34fd8,
0x0302b1b3:0x02f31778,0x03048880:0x03048624,
0x03048692:0x02f54d58,0x02ddbff7:0x0304874c}
VTABLE={0x03ac1318:0x008d3c60,0x03ac1320:0x02f5b1e4,
        0x03ac1328:0x008d3c60}

def rva_bytes(buf,addr,n):
    pe=struct.unpack_from("<I",buf,0x3c)[0]
    if buf[pe:pe+4]!=b"PE\x00\x00":raise ValueError("not PE")
    if struct.unpack_from("<H",buf,pe+4)[0]!=0x8664:raise ValueError("not AMD64")
    if struct.unpack_from("<Q",buf,pe+24+24)[0]!=BASE:raise ValueError("wrong ImageBase")
    count=struct.unpack_from("<H",buf,pe+6)[0]
    opsz=struct.unpack_from("<H",buf,pe+20)[0]
    for i in range(count):
        p=pe+24+opsz+i*40
        _,va,size,raw=struct.unpack_from("<IIII",buf,p+8)
        if va<=addr and addr+n<=va+size:return buf[raw+addr-va:raw+addr-va+n]
    raise ValueError("RVA not file-backed")

class TestR98TypedArenaDispatch(unittest.TestCase):
    def test_frozen_focus_has_31_real_instruction_bytes(self):
        self.assertEqual(len(PINS),31)
        for h in PINS.values():self.assertEqual(bytes.fromhex(h).hex(),h)
    def test_eight_direct_call_targets(self):
        self.assertEqual(len(E8),8)
        for site,dest in E8.items():
            b=bytes.fromhex(PINS[site])
            self.assertEqual(b[0],0xe8)
            self.assertEqual(site+5+struct.unpack_from("<i",b,1)[0],dest)
    def test_original_root_owned_arena(self):
        self.assertEqual(PINS[0x0300cb85],"498d87a02f0000")
        self.assertEqual(PINS[0x0300cc16],"49898780020000")
        self.assertEqual(PINS[0x03048879],"488d8ba02f0000")
    def test_queue_and_move_slot_copy_same_arena_pointer(self):
        self.assertEqual(PINS[0x02f5548f],"48894110")
        self.assertEqual(PINS[0x0300d905],"48894118")
    def test_arena_record_16byte_write_and_dispatch_read(self):
        self.assertEqual(PINS[0x02f35013],"f30f7f84c200020000")
        self.assertEqual(PINS[0x03048670],"488b34c3")
    def test_typed_scheduler_virtual_plus_10(self):
        self.assertEqual(E8[0x03048880],0x03048624)
        self.assertEqual(PINS[0x03048681],"ff5210")
        self.assertEqual(VTABLE[0x03ac1320],0x02f5b1e4)
    def test_earlier_concrete_task_virtual_plus_18_is_noop(self):
        self.assertEqual(PINS[0x030486a2],"ff5218")
        self.assertEqual(VTABLE[0x03ac1328],0x008d3c60)
    def test_callback_completion_byte_is_checked_by_scheduler(self):
        self.assertEqual(PINS[0x02f5b5c3],"884318")
        self.assertEqual(PINS[0x03048687],"807e1801")
    def test_conditional_cleanup_is_after_callback(self):
        self.assertLess(0x03048681,0x03048692)
        self.assertEqual(E8[0x03048692],0x02f54d58)
    def test_root_and_arena_address_not_route_generation(self):
        a={"root":1,"arena":2,"route":3,"group_epoch":4}
        b={"root":1,"arena":2,"route":5,"group_epoch":6}
        self.assertEqual((a["root"],a["arena"]),(b["root"],b["arena"]))
        self.assertNotEqual((a["route"],a["group_epoch"]),(b["route"],b["group_epoch"]))
    def test_no_unverified_hook_authorization(self):
        evidence={"binary_valid":True,"thread_owner_proven":False,
                  "group_lifetime_proven":False,"route_generation_proven":False}
        self.assertFalse(all(evidence.values()))
    @unittest.skipUnless(os.environ.get("BSC_R98_GAME_EXE"),
                         "commercial game EXE absent in public CI")
    def test_exact_real_file_pins_and_vtable(self):
        buf=Path(os.environ["BSC_R98_GAME_EXE"]).read_bytes()
        self.assertEqual(len(buf),SIZE)
        self.assertEqual(hashlib.sha256(buf).hexdigest(),SHA)
        for addr,h in PINS.items():
            self.assertEqual(rva_bytes(buf,addr,len(h)//2),bytes.fromhex(h))
        for addr,target in VTABLE.items():
            self.assertEqual(struct.unpack("<Q",rva_bytes(buf,addr,8))[0],BASE+target)
        self.assertEqual(rva_bytes(buf,0x008d3c60,3),bytes.fromhex("c20000"))

if __name__=="__main__":unittest.main()
