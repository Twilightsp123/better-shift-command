"""Typed native actor dispatch is grounded by matching two vtable slots."""
import os,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(HERE))
import audit_typed_member_geometry_fanout as m
from audit_wh3_full_native_chain import StrictPE

class TypedMemberGeometryDispatch(unittest.TestCase):
 def test_typed_receiver_and_geometry_action_same_object(self):
  for recv,action in ((0x38FD9C0,0x38FDC10),(0x3910868,0x3910AB8)):
   self.assertEqual(action-recv,0x5B8-0x368)
   self.assertEqual(m.SLOTS[recv],0x306B9F0)
   self.assertEqual(m.SLOTS[action],0x306A8C0)
 def test_actual_source_to_packet_to_actor_calls(self):
  self.assertEqual(len(m.EDGES),6)
  self.assertEqual(m.EDGES[0x3117DEB],0x324983C)
  self.assertEqual(m.EDGES[0x3117E00],0x3117E8C)
  self.assertEqual(m.EDGES[0x306A8EB],0x3248EC8)
  self.assertEqual(m.EDGES[0x3249530],0x2F5E8A4)
  self.assertEqual(m.PINS[0x3117EF7],'ff90b8050000')
 def test_fourth_float_packed_at_plus60_not_plus54(self):
  self.assertEqual(m.PINS[0x32498B9],'f30f114160')
  self.assertEqual(m.PINS[0x2F5E918],'8b4260')
  self.assertEqual(m.PINS[0x2F5E8F2],'8b4248')
 def test_wrong_build_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'not-game.exe';raw=b'MZ'+b'nope'*100;p.write_bytes(raw)
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):StrictPE(p)
   self.assertEqual(raw,p.read_bytes())
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'GitHub CI excludes original WH3 executable')
 def test_full_actual_build(self):
  report=m.audit(os.getenv('WH3_903_EXE'))
  self.assertEqual(report['static_opcode_guards'],len(m.PINS))
  self.assertEqual(report['direct_e8_edges'],6)
  self.assertEqual(report['typed_vtable_slots'],5)
  self.assertEqual(report['input_endpoints_to_record']['+0x54'],'+0x60')
  self.assertFalse(report['source_task_instance_proven'])
  self.assertFalse(report['native_patch_authorized'])

if __name__=='__main__':unittest.main()
