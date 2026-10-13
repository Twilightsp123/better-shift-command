"""Typed same-member geometry and false +0x88 writer; original EXE optional."""
import os,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'))
import audit_typed_member_subclass_geometry as a

class MemberSubtypeTests(unittest.TestCase):
 def test_real_instantiated_subclass_pair(self):
  v=a.SLOTS[0x0390FAB0]
  self.assertEqual((v[0x368],v[0x388]),(0x03117CE0,0x03117D44))
  self.assertEqual(v[0x260],0x008D3330)
 def test_same_member_interfaces_different_receiver(self):
  v=a.SLOTS[0x0390FAB0]
  for base in (0x038FD658,0x03910500):
   x=a.SLOTS[base]
   self.assertEqual([x[k] for k in (0x348,0x580,0x5B8)],
                    [v[k] for k in (0x348,0x580,0x5B8)])
   self.assertNotEqual(x[0x368],v[0x368])
   self.assertNotEqual(x[0x388],v[0x388])
 def test_constructor_installs_member_vtable(self):
  self.assertEqual(a.LEAS[0x030EE4D5],0x0390FAB0)
  self.assertEqual(a.CALLS[0x030EE4D0],0x030EE380)
  self.assertEqual(a.PINS[0x030EE4DF],'488903')
 def test_geometry_fanout_is_per_member(self):
  self.assertEqual(a.CALLS[0x03117DEB],0x0324983C)
  self.assertEqual(a.CALLS[0x03117E00],0x03117E8C)
  self.assertEqual(a.JUMPS[0x03117D3F],0x0306B9F0)
  self.assertEqual(a.PINS[0x03117EBA],'f6456840')
  self.assertEqual(a.PINS[0x03118040],'41ff90b8050000')
 def test_simd_overlapping_88_creates_different_object(self):
  self.assertEqual(a.PINS[0x0326F4DD],'b990000000')
  self.assertEqual(a.CALLS[0x0326F4E5],0x030C4BBC)
  self.assertEqual(a.PINS[0x0326F4EA],'488bd8')
  self.assertEqual(a.LEAS[0x0326F53D],0x03915038)
  self.assertEqual(a.PINS[0x0326F548],'488903')
  self.assertEqual(a.PINS[0x0326F54B],'f30f7f8380000000')
 def test_second_false_writer_has_other_vtable(self):
  self.assertEqual(a.LEAS[0x03265179],0x03ADDE08)
  self.assertEqual(a.PINS[0x0326519B],'48898388000000')
 def test_wrong_exe_is_refused(self):
  class Wrong:
   sha='wrong'
   def close(self):pass
  with patch.object(a,'StrictPE',return_value=Wrong()):
   with self.assertRaisesRegex(ValueError,'WRONG_EXE'):a.audit(Path('fake.exe'))
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Original WH3 EXE excluded from public CI')
 def test_exact_original_exe(self):
  r=a.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual((r['opcode_instruction_starts'],r['typed_member_vtable_slots']),(29,18))
  self.assertFalse(r['native_patch_authorized'])
if __name__=='__main__':unittest.main()
