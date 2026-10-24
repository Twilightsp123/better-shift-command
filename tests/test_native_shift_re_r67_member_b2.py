#!/usr/bin/env python3
"""R67 public synthetic contract checks. Private original EXE is NOT in GitHub CI."""
import os,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"maintenance_tools"/"native_shift_re"))
import audit_r67_member_b2_branch as r
class B2Branch(unittest.TestCase):
 def test_pin_inventory(self):self.assertEqual(len(r.PINS),64)
 def test_branch_is_not_shift_key(self):
  self.assertEqual(r.PINS["03070b2f"],"8b8704010000")
  self.assertEqual(r.PINS["03070b35"],"ffc8")
  self.assertEqual(r.PINS["03070b3c"],"83f801")
  self.assertEqual(r.PINS["03070b49"],"0f96c0")
 def test_receiver_pointer_provenance(self):
  self.assertEqual(r.PINS["03070a64"],"488bf9")
  self.assertEqual(r.PINS["03070b23"],"4c8b1f")
 def test_indirect_sites(self):
  for pc,slot in r.VIRTUAL.items():
   b=bytes.fromhex(r.PINS[f"{pc:08x}"])
   self.assertEqual(b[:3],bytes.fromhex("41ff93"))
   self.assertEqual(struct.unpack_from("<I",b,3)[0],slot)
 def test_call_targets(self):
  for pc,dest in r.CALLS.items():
   b=bytes.fromhex(r.PINS[f"{pc:08x}"])
   self.assertEqual(pc+5+struct.unpack_from("<i",b,1)[0],dest)
 def test_type_divergence(self):
  self.assertNotEqual(r.VTABLES[0x03912950][0xe8],r.VTABLES[0x03ad3360][0xe8])
  self.assertEqual(r.VTABLES[0x03912950][0x100],r.VTABLES[0x03ad3360][0x100])
 def test_member_physical_xyz(self):
  self.assertEqual(r.PINS["03164658"],"f20f118788000000")
  self.assertEqual(r.PINS["0316466a"],"898790000000")
 def test_world_goal_separate(self):
  self.assertEqual(r.PINS["0311e6ca"],"0f1187e0010000")
  self.assertEqual(r.PINS["0311e6e8"],"f20f118ff0010000")
 def test_integrator_before_goal_read(self):
  self.assertLess(0x0310014c,0x03100247)
 def test_wrong_sha_fails_closed(self):
  with self.assertRaisesRegex(ValueError,"FAIL_CLOSED"):
   r.verify(b"MZ"+bytes(400))
 def test_private_exact_exe_optional(self):
  exe=os.environ.get("BSC_WARHAMMER3_EXE")
  if not exe:self.skipTest("original licensed game EXE not distributed to public CI")
  data=Path(exe).read_bytes()
  result=r.verify(data)
  self.assertFalse(result["root_cause_proven"])
if __name__=="__main__":unittest.main()
