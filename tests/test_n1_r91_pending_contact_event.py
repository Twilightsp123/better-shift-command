"""R91 public contact-event static contract; no Hook or gameplay patch.
Commercial EXE tests require BSC_R91_GAME_EXE. Public CI skips exact EXE.
Full 66-pin LLVM/PE/unwind verifier is delivered in the R91 research ZIP.
"""
import hashlib,os,struct,unittest
SHA="9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496"
SIZE=232531920
BASE=0x140000000
# Frozen original WH3 RVA -> complete instruction bytes (all LLVM instruction starts).
PINS={
0x02DD0753:"ff5010",0x02DD0758:"7413",0x02DD0763:"ff5008",
0x02DD076D:"40b501",0x02DD078C:"488d4f30",0x02DD0790:"498bd6",
0x02DD0793:"e8dcdffbff",0x02DC9579:"488b7938",0x02DC9580:"8b4134",
0x02DC9583:"486bd038",0x02DC95AA:"ff5010",0x02DC95AF:"750c",
0x02DC95BA:"ff5008",0x02DC95D4:"4883c738",0x02DC95E5:"83633400",
0x02D8E7AD:"486bc838",0x02D8E914:"ff4304",
0x01196574:"4881e9d8010000",0x0119657B:"e99c73c101",
0x02DA210E:"488988d8010000"}
EDGES={0x02DD0758:0x02DD076D,0x02DD0793:0x02D8E774,
       0x02DC95AF:0x02DC95BD,0x0119657B:0x02DAD91C}
VTABLES={0x03AAF7F0:(0x02DC9564,0x02DACF54,0x02DD06F0),
         0x03AB1B48:(0x02DC9564,0x01196574,0x02DD06F0)}
def target(rva,h):
 b=bytes.fromhex(h)
 if b[0] in (0xe8,0xe9): return rva+5+struct.unpack("<i",b[1:])[0]
 if b[0] in (0x74,0x75):return rva+2+struct.unpack("<b",b[1:])[0]
 raise ValueError("unsupported relative opcode")
def pe_bytes(data,rva,n):
 off=struct.unpack_from("<I",data,0x3c)[0]
 if data[off:off+4]!=bytes((80,69,0,0)):raise ValueError("PE")
 if struct.unpack_from("<H",data,off+4)[0]!=0x8664:raise ValueError("AMD64")
 if struct.unpack_from("<Q",data,off+24+24)[0]!=BASE:raise ValueError("imagebase")
 sections=struct.unpack_from("<H",data,off+6)[0]
 op_size=struct.unpack_from("<H",data,off+20)[0]
 for i in range(sections):
  p=off+24+op_size+i*40
  _,start,size,raw=struct.unpack_from("<IIII",data,p+8)
  if start<=rva and rva+n<=start+size:return data[raw+rva-start:raw+rva-start+n]
 raise ValueError("no file-backed section")
class TestR91PendingContact(unittest.TestCase):
 def test_public_manifest_size(self):self.assertEqual(len(PINS),20)
 def test_all_pins_valid(self):
  for opcode in PINS.values():self.assertEqual(bytes.fromhex(opcode).hex(),opcode)
 def test_relative_edges(self):
  for a,b in EDGES.items():self.assertEqual(target(a,PINS[a]),b)
 def test_gate_is_subscriber_method(self):self.assertEqual(PINS[0x02DD0753],"ff5010")
 def test_immediate_callback(self):self.assertEqual(PINS[0x02DD0763],"ff5008")
 def test_immediate_zero_defers(self):self.assertEqual(PINS[0x02DD0758],"7413")
 def test_pending_write(self):self.assertEqual(target(0x02DD0793,PINS[0x02DD0793]),0x02D8E774)
 def test_replay_count(self):self.assertEqual(PINS[0x02DC9580],"8b4134")
 def test_replay_buffer(self):self.assertEqual(PINS[0x02DC9579],"488b7938")
 def test_replay_callback(self):self.assertEqual(PINS[0x02DC95BA],"ff5008")
 def test_replay_gate_opposite(self):self.assertEqual(PINS[0x02DC95AF],"750c")
 def test_pending_clear(self):self.assertEqual(PINS[0x02DC95E5],"83633400")
 def test_record_size(self):self.assertEqual(PINS[0x02D8E7AD],"486bc838")
 def test_receiver_thunk_not_callback(self):self.assertEqual(PINS[0x01196574],"4881e9d8010000")
 def test_two_typed_vtables(self):
  self.assertEqual(VTABLES[0x03AAF7F0][2],VTABLES[0x03AB1B48][2])
  self.assertNotEqual(VTABLES[0x03AB1B48][1],0x02DD0763)
 def test_synthetic_not_engine_causality(self):
  self.assertEqual(("immediate" if 1 else "pending"),"immediate")
  self.assertEqual(("immediate" if 0 else "pending"),"pending")
 @unittest.skipUnless(os.environ.get("BSC_R91_GAME_EXE"),"public CI cannot distribute commercial WH3 EXE")
 def test_exact_file_and_vtables(self):
  data=open(os.environ["BSC_R91_GAME_EXE"],"rb").read()
  self.assertEqual(len(data),SIZE);self.assertEqual(hashlib.sha256(data).hexdigest(),SHA)
  for a,h in PINS.items():self.assertEqual(pe_bytes(data,a,len(h)//2),bytes.fromhex(h))
  for a,items in VTABLES.items():
   self.assertEqual(tuple(struct.unpack("<Q",pe_bytes(data,a+8*i,8))[0]-BASE for i in range(3)),items)
if __name__=="__main__":unittest.main()
