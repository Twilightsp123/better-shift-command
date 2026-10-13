"""Pin class-correct actor action subtypes on exact WH3 vtables."""
import os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_dual_member_action_subtypes as m
from audit_wh3_full_native_chain import StrictPE

class NativeDualMemberSubtype(unittest.TestCase):
 def test_actor_same_action_slot_two_typed_subclasses(self):
  self.assertEqual(len(m.PINS),19)
  self.assertEqual(len(m.VTABLES),6)
  self.assertEqual(m.PINS[0x0306A99A],m.PINS[0x0306A8CA])
  self.assertEqual(m.PINS[0x0306A9AC],m.PINS[0x0306A8DC])
  for alt,geom in ((0x038FDBD8,0x038FDC10),
                   (0x03910A80,0x03910AB8)):
   self.assertEqual(geom-alt,0x5B8-0x580)
   self.assertEqual(m.VTABLES[alt],0x0306A990)
   self.assertEqual(m.VTABLES[geom],0x0306A8C0)
 def test_action_embedded_vtable_tick_variants_are_not_equal(self):
  self.assertEqual(m.VTABLES[0x03913810],0x032599C8)
  self.assertEqual(m.VTABLES[0x03ADAA10],0x03259950)
  self.assertEqual(m.VTABLE_LEA[0x0324935C],0x03913808)
  self.assertEqual(m.VTABLE_LEA[0x03248EE4],0x03ADAA08)
 def test_direct_motor_path_is_from_alternate_subtype(self):
  self.assertEqual(m.CONTROL[0x03259C55],('E8',0x0306EF1C))
  self.assertEqual(m.CONTROL[0x0306EF96],('E9',0x0311954C))
  self.assertEqual(m.PINS[0x0311963A],'0f1187e0010000')
  for site in (0x02F79C3D,0x02F79D6E,0x02F7A116):
   self.assertEqual(m.PINS[site],'ff9080050000')
  self.assertEqual(m.PINS[0x03117EF7],'ff90b8050000')
 def test_wrong_exe_fails_before_reads(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'wrong.exe';content=b'MZ'+b'native-drift'*70
   p.write_bytes(content)
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):StrictPE(p)
   self.assertEqual(p.read_bytes(),content)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Exact original game EXE excluded from GitHub')
 def test_exact_original_vtables_and_two_subclasses(self):
  report=m.audit(os.environ['WH3_903_EXE'])
  self.assertEqual(report['original_opcode_guards'],19)
  self.assertEqual(report['exact_direct_call_or_jump_edges'],5)
  self.assertEqual(report['typed_vtable_slots'],6)
  self.assertFalse(report['which_subclass_user_RMB_or_Shift_chooses_proven'])
  self.assertFalse(report['native_patch_authorized'])

if __name__=='__main__':unittest.main()
