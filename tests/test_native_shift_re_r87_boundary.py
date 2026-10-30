"""R87 public CI negative controls. No licensed game EXE committed."""
import json,os,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(P))
import r87_boundary as a
M=json.loads((P/'r87_boundary_pins.json').read_text())
def p(r):return M['pins'][r]['hex']
class R87(unittest.TestCase):
 def test_focus_76(self):self.assertEqual(len(M['pins']),76)
 def test_E8_6(self):self.assertEqual(len(M['e8']),6)
 def test_JCC_11(self):self.assertEqual(len(M['jcc']),11)
 def test_owners_5(self):self.assertEqual(len(M['functions']),5)
 def test_contact_target(self):self.assertEqual(M['e8']['0305a800'],'03085114')
 def test_pair_identity(self):self.assertEqual(p('03085140'),'4d8bf0')
 def test_selected_neighbour(self):self.assertEqual(p('03059f6a'),'488bf3')
 def test_owner_compare(self):self.assertEqual(p('03059f4e'),'48398380000000')
 def test_contact_packet_record(self):self.assertEqual(p('0308529d'),'498d8dd8010000')
 def test_contact_virtual_not_physical(self):self.assertEqual(p('030852a7'),'ff5010')
 def test_steering_path_gated(self):self.assertEqual(p('0305a05b'),'0f8644010000')
 def test_post_steering_call(self):self.assertEqual(M['e8']['03087351'],'0308d830')
 def test_post_requires_both_ptrs(self):
  self.assertEqual(p('0308d839'),'4883793000')
  self.assertEqual(p('0308d857'),'4883b9e802000000')
 def test_post_state_limit(self):self.assertEqual(p('0308d865'),'8b816c020000')
 def test_post_optional_target_helper(self):
  self.assertEqual(p('0308da23'),'488d93e0010000')
  self.assertEqual(M['e8']['0308da71'],'03065db8')
 def test_integrator_heading_writes(self):
  self.assertEqual(p('03147199'),'f30f118b3c010000')
  self.assertEqual(p('031471a1'),'f30f11a344010000')
 def test_integrator_own_velocity_xyz(self):
  self.assertEqual(p('0314745d'),'f30f118340010000')
  self.assertEqual(p('03147465'),'f30f11933c010000')
  self.assertEqual(p('0314746d'),'f30f119b44010000')
 def test_integrator_physical_xyz(self):
  self.assertEqual(p('0314720b'),'f30f118388000000')
  self.assertEqual(p('03147223'),'f30f118b8c000000')
  self.assertEqual(p('0314723b'),'f30f118390000000')
 def test_post_absent_owner_no_action(self):self.assertFalse(a.post_gate(False,True,0x78,True))
 def test_post_absent_attached_state_no_action(self):self.assertFalse(a.post_gate(True,False,0x78,True))
 def test_post_non_special_no_action(self):self.assertFalse(a.post_gate(True,True,0x15,True))
 def test_post_condition_false_no_action(self):self.assertFalse(a.post_gate(True,True,0x78,False))
 def test_post_synthetic_positive_not_game_causality(self):
  self.assertTrue(a.post_gate(True,True,0x79,True))
  self.assertFalse(M['actual_same_shift_member_causality'])
 def test_neighbour_is_not_proven_same_unit(self):self.assertFalse(M['actual_same_shift_member_causality'])
 def test_unknown_patch(self):self.assertFalse(M['gameplay_patch_authorized'])
 def test_wrong_binary_fails(self):
  with self.assertRaises(ValueError):a.audit_bytes(b'MZ'+bytes(160),M)
 def test_private_original_exe_optional(self):
  path=os.getenv('BSC_EXE')
  if not path:self.skipTest('Commercial matching WH3 EXE absent from public CI')
  r=a.audit_bytes(Path(path).read_bytes(),M)
  self.assertEqual(r['focus_pins'],76)
