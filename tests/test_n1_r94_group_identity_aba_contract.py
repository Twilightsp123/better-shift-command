"""BSC R94 public Root/Group/member ownership contract.
Never reads a running process and never authorizes external live pointer polling.
Optional original-file check needs BSC_R94_GAME_EXE; CI has no commercial EXE.
"""
import hashlib,os,struct,unittest
SHA="9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496"
SIZE=232531920;BASE=0x140000000
PINS={
0x03020a0a:"e8a1deffff",0x03020a27:"e810ffffff",
0x03020a4e:"e8994a0c00",0x03020a70:"e8bb660b00",
0x03020a75:"48899ef8320000",0x030209b8:"48894f58",
0x030209bf:"e8f4720a00",0x030c7cf9:"488983100a0000",
0x030c7dca:"48894110",0x030c7de0:"48895120",
0x030c7de4:"48895128",0x030cc4d1:"e8ce9825fe",
0x030cc508:"48ff20",0x030cc512:"48898a00030000",
0x0301e8e8:"e8eb2a0100",0x030313f6:"488907",
0x030313f9:"48893b",0x030c9849:"752c",
0x030c985b:"4883a00003000000",0x030c98b5:"e8b65a4dfd",
0x030da548:"448b4f24",0x030da57c:"488b1cf0",
0x01325e2c:"ff4304",0x030e554e:"e9596ffeff"}
CALLS={0x03020a0a:0x0301e8b0,0x03020a27:0x0302093c,
0x03020a4e:0x030e54ec,0x03020a70:0x030d7130,
0x030209bf:0x030c7cb8,0x030cc4d1:0x01325da4,
0x0301e8e8:0x030313d8}
JUMP={0x030e554e:0x030cc4ac}
VTABLE={0x03914450:0x030cc50c,0x03914460:0x030cb250}
def read_rva(data,rva,n):
    pe=struct.unpack_from("<I",data,0x3c)[0]
    assert data[pe:pe+4]==bytes((80,69,0,0))
    assert struct.unpack_from("<H",data,pe+4)[0]==0x8664
    assert struct.unpack_from("<Q",data,pe+24+24)[0]==BASE
    count=struct.unpack_from("<H",data,pe+6)[0]
    sz=struct.unpack_from("<H",data,pe+20)[0]
    for i in range(count):
        s=pe+24+sz+40*i
        _,va,raw_sz,raw=struct.unpack_from("<IIII",data,s+8)
        if va<=rva and rva+n<=va+raw_sz:
            return data[raw+rva-va:raw+rva-va+n]
    raise ValueError("unmapped rva "+hex(rva))
def addr(src):
    b=bytes.fromhex(PINS[src])
    assert b[0] in (0xe8,0xe9)
    return src+5+struct.unpack_from("<i",b,1)[0]
def coherent(root,group,members):
    # Pure pre-captured record check; not safe live memory acquisition.
    return (root["group"]==group["id"] and group["root"]==root["id"]
      and group["members"]==root["members"]
      and group["count"]==len(group["members"])
      and all(members[p]["group"]==group["id"] for p in group["members"]))
class TestR94Structure(unittest.TestCase):
    def test_frozen_bytes(self):
        self.assertEqual(len(PINS),24)
        for h in PINS.values():self.assertEqual(bytes.fromhex(h).hex(),h)
    def test_e8_and_tail_jump(self):
        for a,b in CALLS.items():self.assertEqual(addr(a),b)
        for a,b in JUMP.items():self.assertEqual(addr(a),b)
    def test_member_group_writer(self):
        self.assertEqual(PINS[0x030cc512],"48898a00030000")
    def test_recycle_conditional(self):
        self.assertEqual(PINS[0x030c9849],"752c")
        self.assertEqual(PINS[0x030c985b],"4883a00003000000")
    def test_double_read_is_not_generation_proof(self):
        root={"id":1,"group":2,"members":[3]}
        group={"id":2,"root":1,"members":[3],"count":1}
        a={3:{"group":2}}
        self.assertTrue(coherent(root,group,a))
        later_root={"id":1,"group":2,"members":[4]}
        later_group={"id":2,"root":1,"members":[4],"count":1}
        self.assertTrue(coherent(later_root,later_group,{4:{"group":2}}))
        self.assertEqual(root["group"],later_root["group"])
        # No route/Group generation follows from pointer equality.
        self.assertNotEqual(root["members"],later_root["members"])
    def test_missing_backpointer_rejected(self):
        self.assertFalse(coherent({"id":1,"group":2,"members":[3]},
                 {"id":2,"root":1,"members":[3],"count":1},
                 {3:{"group":9}}))
    @unittest.skipUnless(os.environ.get("BSC_R94_GAME_EXE"),"commercial EXE unavailable in CI")
    def test_original_exact_file(self):
        data=open(os.environ["BSC_R94_GAME_EXE"],"rb").read()
        self.assertEqual(len(data),SIZE)
        self.assertEqual(hashlib.sha256(data).hexdigest(),SHA)
        for rva,h in PINS.items():
            self.assertEqual(read_rva(data,rva,len(h)//2),bytes.fromhex(h))
        for rva,target in VTABLE.items():
            self.assertEqual(struct.unpack("<Q",read_rva(data,rva,8))[0],BASE+target)
if __name__=="__main__":unittest.main()
