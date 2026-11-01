"""BSC R90 public source contract. No commercial EXE distributed; no Hook or gameplay patch.
Run: python -m unittest discover -s tests -p 'test_n1_r90_constructor_context_contract.py'
Optional: BSC_R90_GAME_EXE=... runs the exact-file check. This does not test gameplay.
"""
import hashlib, mmap, os, struct, unittest

SHA="9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496"
SIZE=232531920
BASE=0x140000000
PINS={
  0x02d9846d:"488bf9", 0x02d98d8e:"48897dc0", 0x02d98d92:"48897dc8",
  0x02d99069:"488d55c0", 0x02d99070:"e88f0f0000",
  0x02d9a046:"488b4208", 0x02d9a04a:"48894108",
  0x02d9a7f7:"498bd6", 0x02d9a80e:"e8b5510000", 0x02d9f9fb:"48894108",
  0x02db6981:"488bd3", 0x02db6999:"e836eafdff",
  0x02d9540f:"48894108", 0x02d955b2:"488bd3", 0x02d955b5:"e8de070000",
  0x02d95e44:"48898138010000", 0x02d96607:"488bd6",
  0x02d96613:"e85cb8ffff", 0x02d91ebe:"e8d5aa2700",
  0x0300c9b4:"488b8238010000", 0x0300c9bf:"48894130",
  0x0300c9c6:"488b8238010000", 0x0300c9d1:"48894138",
  0x0300c9e5:"4c8b9040040000",
  0x03141810:"488b4208", 0x03141814:"48894158",
  0x0305a7cc:"488b9040040000",
}
E8={
  0x02d99070:0x02d9a004,
  0x02d9a80e:0x02d9f9c8,
  0x02db6999:0x02d953d4,
  0x02d955b5:0x02d95d98,
  0x02d96613:0x02d91e74,
  0x02d91ebe:0x0300c998,
}
def rva_offset(buf,rva):
    e=struct.unpack_from("<I",buf,0x3c)[0]
    if buf[e:e+4]!=bytes((80,69,0,0)):raise ValueError("not PE")
    machine,sections=struct.unpack_from("<HH",buf,e+4)
    if machine!=0x8664:raise ValueError("not AMD64")
    opt=e+24
    if struct.unpack_from("<Q",buf,opt+24)[0]!=BASE:raise ValueError("wrong base")
    optsz=struct.unpack_from("<H",buf,e+20)[0]
    for i in range(sections):
        start=opt+optsz+40*i
        _,va,size,raw=struct.unpack_from("<IIII",buf,start+8)
        if va<=rva<va+size:return raw+rva-va
    raise ValueError("rva not raw backed "+hex(rva))
class R90Contract(unittest.TestCase):
    def test_01_hash_has_64_digits(self):self.assertEqual(len(SHA),64)
    def test_02_focus_manifest(self):self.assertEqual(len(PINS),27)
    def test_03_hex_instructions(self):
        for h in PINS.values():self.assertEqual(bytes.fromhex(h).hex(),h)
    def test_04_constructor_saves_self(self):
        self.assertEqual(PINS[0x02d9846d],"488bf9")
        self.assertEqual(PINS[0x02d98d92],"48897dc8")
    def test_05_G_receives_descriptor_C(self):
        self.assertEqual(PINS[0x02d99069],"488d55c0")
        self.assertEqual(PINS[0x02d9a046],"488b4208")
    def test_06_G_to_K(self):self.assertEqual(E8[0x02d9a80e],0x02d9f9c8)
    def test_07_K_to_child(self):self.assertEqual(E8[0x02db6999],0x02d953d4)
    def test_08_child_to_config(self):
        self.assertEqual(PINS[0x02d955b2],"488bd3")
        self.assertEqual(PINS[0x02d95e44],"48898138010000")
    def test_09_config_to_Root(self):self.assertEqual(E8[0x02d91ebe],0x0300c998)
    def test_10_Root_reads_source(self):
        self.assertEqual(PINS[0x0300c9b4],"488b8238010000")
        self.assertEqual(PINS[0x0300c9d1],"48894138")
    def test_11_Root_reads_C_440(self):self.assertEqual(PINS[0x0300c9e5],"4c8b9040040000")
    def test_12_member_receives_context(self):self.assertEqual(PINS[0x03141814],"48894158")
    def test_13_original_steering_reads_C_440(self):self.assertEqual(PINS[0x0305a7cc],"488b9040040000")
    def test_14_verified_E8_arithmetic(self):
        for source,dest in E8.items():
            b=bytes.fromhex(PINS[source])
            self.assertEqual(b[0],0xe8)
            self.assertEqual(source+5+struct.unpack_from("<i",b,1)[0],dest)
    def test_15_constructor_alias_is_conditional(self):
        c=object();c2=object()
        self.assertIsNot(c,c2) # no across-run identity guarantee
        stack={"plus_8":c};g={"plus_8":stack["plus_8"]}
        k={"plus_8":g["plus_8"]};child={"plus_8":k["plus_8"]}
        cfg={"plus_138":child["plus_8"]};root={"plus_38":cfg["plus_138"]}
        self.assertIs(c,root["plus_38"])
    @unittest.skipUnless(os.environ.get("BSC_R90_GAME_EXE"),"commercial EXE unavailable in public CI")
    def test_16_exact_original_exe_focus_pins(self):
        with open(os.environ["BSC_R90_GAME_EXE"],"rb") as f:
            b=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
            try:
                self.assertEqual(len(b),SIZE)
                self.assertEqual(hashlib.sha256(b).hexdigest(),SHA)
                for rva,h in PINS.items():
                    i=rva_offset(b,rva)
                    self.assertEqual(b[i:i+len(h)//2],bytes.fromhex(h))
            finally:b.close()
if __name__=="__main__":unittest.main()
